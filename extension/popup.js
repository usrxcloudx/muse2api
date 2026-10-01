/* Muse2API Cookie Importer —— Đọc cookie của muse.ai và POST lên dịch vụ muse2api.
 *
 * Điểm mấu chốt: Dùng chrome.cookies thay vì document.cookie.
 * 4 cookie cốt lõi của muse.ai (hatch_sess / hatch_gw / hatch_vml /
 * hatch_native_auth_device) đều có cờ httpOnly, Javascript trên trang không đọc được,
 * chỉ có quyền cookies của Chrome extension mới lấy được.
 */

const $ = (id) => document.getElementById(id);
const STORE = 'muse2api_ext_cfg';

const ESSENTIAL = ['hatch_sess', 'hatch_gw', 'hatch_vml', 'hatch_native_auth_device'];

function log(html, cls) {
  const el = $('log');
  el.className = 'show';
  el.innerHTML = cls ? `<span class="${cls}">${html}</span>` : html;
}

/* Chuẩn hóa địa chỉ dịch vụ: bỏ dấu gạch chéo cuối và hậu tố /v1 */
function normBase(v) {
  let s = (v || '').trim();
  if (!s) return '';
  if (!/^https?:\/\//i.test(s)) s = 'https://' + s;
  s = s.replace(/\/+$/, '');
  s = s.replace(/\/v1$/i, '');
  return s;
}

async function loadCfg() {
  const o = await chrome.storage.local.get(STORE);
  const c = o[STORE] || {};
  if (c.base) $('base').value = c.base;
  if (c.key) $('key').value = c.key;
  if (c.label) $('label').value = c.label;
  // Nếu chưa cấu hình thì đoán từ tab hiện tại (khi người dùng đang mở trang admin)
  if (!c.base) {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      const u = tab && tab.url ? new URL(tab.url) : null;
      if (u && /\/admin/.test(u.pathname)) {
        $('base').value = u.origin;
        const k = new URLSearchParams(u.search).get('key');
        if (k) $('key').value = k;
      }
    } catch (e) { /* Bỏ qua */ }
  }
}

async function saveCfg() {
  await chrome.storage.local.set({
    [STORE]: {
      base: normBase($('base').value),
      key: $('key').value.trim(),
      label: $('label').value.trim(),
    },
  });
}

async function grabCookies() {
  const all = await chrome.cookies.getAll({ domain: 'muse.ai' });
  const out = {}, exp = {};
  for (const c of all) {
    const dom = (c.domain || '').replace(/^\./, '');
    if (!dom.endsWith('muse.ai')) continue;
    out[c.name] = c.value;
    if (c.expirationDate) exp[c.name] = Math.floor(c.expirationDate);
  }
  return { cookies: out, expires: exp };
}

async function run() {
  const base = normBase($('base').value);
  const key = $('key').value.trim();
  const label = $('label').value.trim();

  if (!base) return log('Vui lòng nhập địa chỉ dịch vụ (BASE URL)', 'bad');
  if (!key) return log('Vui lòng nhập API Key', 'bad');

  $('go').disabled = true;
  log('Đang đọc Cookie của muse.ai…');

  try {
    // Kích hoạt session để muse.ai cấp hatch_vml nếu đang ở tab rảnh
    try {
      await fetch('https://muse.ai/api/session', { credentials: 'include' });
    } catch (_) {}

    const { cookies, expires } = await grabCookies();
    const names = Object.keys(cookies);
    if (!names.length) {
      return log('Không tìm thấy Cookie nào của muse.ai.\nVui lòng mở và đăng nhập vào https://muse.ai/ trên trình duyệt này trước, sau đó bấm lại nút này.', 'bad');
    }
    const missing = ESSENTIAL.filter((n) => !(n in cookies));
    if (missing.length) {
      log(`Đã đọc ${names.length} Cookie, nhưng thiếu mục cốt lõi: ${missing.join(', ')}\n`
          + 'Cho thấy bạn chưa mở vào giao diện trò chuyện. Hãy truy cập https://muse.ai/thread/new và gửi thử 1 tin nhắn rồi thử lại.', 'warn');
      return;
    }

    log(`Đã đọc ${names.length} Cookie, đang gửi lên ${base} …`);

    const r = await fetch(base + '/admin/accounts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + key,
      },
      body: JSON.stringify({ label, cookies, expires }),
    });

    const text = await r.text();
    let data;
    try { data = JSON.parse(text); } catch (e) { data = { raw: text }; }

    if (r.status === 401) {
      return log('API Key không chính xác (Mã lỗi 401).\nVui lòng sao chép đúng API Key từ trang quản trị muse2api.', 'bad');
    }
    if (!r.ok) {
      return log(`Nhập thất bại: HTTP ${r.status}\n${text.slice(0, 300)}`, 'bad');
    }

    const a = (data.added && data.added[0]) || {};
    await saveCfg();
    log(`✓ Nhập tài khoản thành công\nNhãn tài khoản: ${a.label || label || '(Tự động)'}\n`
        + `ID tài khoản: ${a.id || '?'}\nSố lượng Cookie: ${a.cookie_count || names.length}\n`
        + `Hết hạn vào: ${a.expires_at ? new Date(a.expires_at * 1000).toLocaleString('vi-VN') : 'Không xác định'}\n`
        + (data.warning ? `\nLưu ý: ${data.warning}` : ''), 'ok');
  } catch (e) {
    log('Đã xảy ra lỗi: ' + (e && e.message ? e.message : String(e))
        + '\n\nNguyên nhân thường gặp:\n'
        + '· Địa chỉ dịch vụ điền sai hoặc dịch vụ chưa khởi động\n'
        + '· Địa chỉ không hỗ trợ hoặc chứng chỉ SSL không hợp lệ\n'
        + '· Trình duyệt chặn yêu cầu liên kết chéo (CORS)', 'bad');
  } finally {
    $('go').disabled = false;
  }
}

$('go').addEventListener('click', run);
loadCfg();

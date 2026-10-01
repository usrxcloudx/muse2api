#!/usr/bin/env python3
"""
CLI helper for interacting with local muse2api service.
Used by Hermes Agent and users to generate images, videos, and chat.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE = os.environ.get("MUSE2API_BASE", "http://127.0.0.1:18610")
DEFAULT_KEY = os.environ.get("MUSE2API_KEY", "")


def _get_env_key():
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("MUSE2API_KEY=") and len(line) > 13:
                        return line.split("=", 1)[1].strip().strip('"\'')
        except Exception:
            pass
    return DEFAULT_KEY


API_KEY = _get_env_key()


def _request(endpoint: str, data: dict | None = None, method: str = "GET", timeout: int = 120) -> dict:
    url = urllib.parse.urljoin(DEFAULT_BASE, endpoint)
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
            msg = err_json.get("error", {}).get("message") or err_json.get("detail") or err_body
        except Exception:
            msg = err_body
        print(f"Error {e.code}: {msg}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Connection error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_status(_args):
    ready = _request("/readyz")
    accounts = _request("/admin/accounts")
    print(json.dumps({
        "readyz": ready,
        "accounts_count": len(accounts),
        "accounts": accounts
    }, indent=2, ensure_ascii=False))


def cmd_image(args):
    payload = {
        "model": "muse-image",
        "prompt": args.prompt,
        "size": args.size,
        "response_format": "url"
    }
    if args.reference_image:
        payload["reference_image"] = args.reference_image

    print(f"Sending image generation request: {args.prompt} (size: {args.size})...")
    res = _request("/v1/images/generations", data=payload, method="POST", timeout=300)
    data = res.get("data", [])
    if not data:
        print("No image data returned", file=sys.stderr)
        sys.exit(1)

    img_url = data[0].get("url")
    print(f"Image generated successfully: {img_url}")

    if args.output:
        out_path = os.path.abspath(args.output)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        print(f"Downloading to {out_path}...")
        urllib.request.urlretrieve(img_url, out_path)
        print(f"Saved: MEDIA:{out_path}")
    else:
        # Check if local file exists in data/media
        fname = os.path.basename(img_url)
        local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "media", fname)
        if os.path.exists(local_path):
            print(f"Saved: MEDIA:{local_path}")


def cmd_video(args):
    payload = {
        "model": "muse-video",
        "prompt": args.prompt,
        "duration": args.duration,
        "size": args.size
    }
    if args.reference_image:
        payload["reference_image"] = args.reference_image

    print(f"Creating video task: {args.prompt} ({args.duration}s, size: {args.size})...")
    task = _request("/v1/videos", data=payload, method="POST")
    task_id = task.get("id") or task.get("task_id")
    print(f"Task created: {task_id}. Polling progress...")

    start_t = time.time()
    while True:
        time.sleep(5)
        status = _request(f"/v1/videos/{task_id}")
        state = status.get("status")
        progress = status.get("progress", 0)
        elapsed = int(time.time() - start_t)
        print(f"[{elapsed}s] Status: {state}, Progress: {progress}%")

        if state == "completed":
            vurl = status.get("url") or status.get("result", {}).get("url")
            print(f"Video completed: {vurl}")
            if args.output:
                out_path = os.path.abspath(args.output)
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                print(f"Downloading to {out_path}...")
                urllib.request.urlretrieve(vurl, out_path)
                print(f"Saved: MEDIA:{out_path}")
            else:
                fname = os.path.basename(vurl)
                local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "media", fname)
                if os.path.exists(local_path):
                    print(f"Saved: MEDIA:{local_path}")
            break
        elif state == "failed":
            print(f"Video task failed: {status.get('error')}", file=sys.stderr)
            sys.exit(1)
        elif elapsed > 650:
            print("Video task timed out", file=sys.stderr)
            sys.exit(1)


def cmd_chat(args):
    payload = {
        "model": args.model or "muse-spark",
        "messages": [{"role": "user", "content": args.prompt}],
        "stream": False
    }
    res = _request("/v1/chat/completions", data=payload, method="POST", timeout=300)
    choices = res.get("choices", [])
    if choices:
        msg = choices[0].get("message", {}).get("content", "")
        print(msg)
    else:
        print(json.dumps(res, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Muse2API CLI tool")
    sub = parser.add_subparsers(dest="command", required=True)

    # Status
    p_stat = sub.add_parser("status", help="Check status and accounts")
    p_stat.set_defaults(func=cmd_status)

    # Image
    p_img = sub.add_parser("image", help="Generate image")
    p_img.add_argument("--prompt", "-p", required=True, help="Image prompt")
    p_img.add_argument("--size", "-s", default="16:9", choices=["1:1", "16:9", "9:16", "4:3", "3:4"], help="Aspect ratio")
    p_img.add_argument("--reference-image", "-r", help="Path or URL to reference image")
    p_img.add_argument("--output", "-o", help="Target output file path")
    p_img.set_defaults(func=cmd_image)

    # Video
    p_vid = sub.add_parser("video", help="Generate video")
    p_vid.add_argument("--prompt", "-p", required=True, help="Video prompt")
    p_vid.add_argument("--duration", "-d", type=int, default=5, choices=[5, 6, 8, 10], help="Duration in seconds")
    p_vid.add_argument("--size", "-s", default="16:9", choices=["16:9", "9:16"], help="Aspect ratio")
    p_vid.add_argument("--reference-image", "-r", help="Path or URL to first frame reference image")
    p_vid.add_argument("--output", "-o", help="Target output file path")
    p_vid.set_defaults(func=cmd_video)

    # Chat
    p_chat = sub.add_parser("chat", help="Chat completion")
    p_chat.add_argument("--prompt", "-p", required=True, help="Chat message")
    p_chat.add_argument("--model", "-m", default="muse-spark", help="Model name")
    p_chat.set_defaults(func=cmd_chat)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

"""
webhook_server.py

Receives Telegram messages (/approve or /reject),
then triggers a GitHub Actions workflow via repository dispatch.
"""

import os
import json
import hmac
import hashlib
import urllib.request
import urllib.parse
from flask import Flask, request, jsonify
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

app = Flask(__name__)

# ── Config (loaded from environment variables) ────────────────────────────────

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GITHUB_TOKEN       = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO        = os.environ.get("GITHUB_REPO", "")  # e.g. "betty/qa-experiment"
ALLOWED_CHAT_ID    = os.environ.get("TELEGRAM_CHAT_ID", "")  # only your chat can trigger


# ── 1. Send Telegram reply ────────────────────────────────────────────────────

def send_telegram_reply(chat_id: str, text: str):
    """Send a message back to the Telegram chat."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=payload, method="POST")
        urllib.request.urlopen(req, timeout=10)
        log.info(f"Telegram reply sent to chat_id={chat_id}")
    except Exception as e:
        log.warning(f"Failed to send Telegram reply: {e}")


# ── 2. Trigger GitHub Actions workflow ───────────────────────────────────────

def trigger_github_workflow(event_type: str):
    """
    Trigger a GitHub Actions workflow via repository dispatch.
    event_type: "qa-approved" or "qa-rejected"
    """
    url = f"https://api.github.com/repos/{GITHUB_REPO}/dispatches"
    payload = json.dumps({
        "event_type": event_type,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            log.info(f"GitHub dispatch sent: event_type={event_type}, status={resp.status}")
            return True
    except Exception as e:
        log.error(f"Failed to trigger GitHub workflow: {e}")
        return False


# ── 3. Webhook endpoint ───────────────────────────────────────────────────────

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)
    if not data:
        log.warning("Received empty or non-JSON request")
        return jsonify({"error": "Invalid request"}), 400

    log.info(f"Received update: {json.dumps(data)[:200]}")

    # Extract message info
    message = data.get("message", {})
    chat_id = str(message.get("chat", {}).get("id", ""))
    text    = message.get("text", "").strip().lower()

    if not chat_id or not text:
        log.info("No message text found — ignoring")
        return jsonify({"ok": True}), 200

    # Security: only allow your own chat ID
    if chat_id != str(ALLOWED_CHAT_ID):
        log.warning(f"Unauthorized chat_id={chat_id} — ignoring")
        return jsonify({"ok": True}), 200

    log.info(f"Command received from chat_id={chat_id}: '{text}'")

    # Handle /approve
    if text == "/approve":
        success = trigger_github_workflow("qa-approved")
        if success:
            send_telegram_reply(chat_id, "✅ Approved — CI will continue.")
        else:
            send_telegram_reply(chat_id, "⚠️ Failed to trigger GitHub workflow. Check server logs.")

    # Handle /reject
    elif text == "/reject":
        success = trigger_github_workflow("qa-rejected")
        if success:
            send_telegram_reply(chat_id, "❌ Rejected — CI will be marked as failed.")
        else:
            send_telegram_reply(chat_id, "⚠️ Failed to trigger GitHub workflow. Check server logs.")

    # Unknown command
    else:
        send_telegram_reply(chat_id, "Unknown command. Please reply /approve or /reject.")

    return jsonify({"ok": True}), 200


# ── 4. Health check ───────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Validate required environment variables
    missing = [v for v in ["TELEGRAM_BOT_TOKEN", "GITHUB_TOKEN", "GITHUB_REPO", "TELEGRAM_CHAT_ID"]
               if not os.environ.get(v)]
    if missing:
        log.error(f"Missing required environment variables: {missing}")
        raise SystemExit(1)

    port = int(os.environ.get("PORT", 5001))
    log.info(f"Starting webhook server for repo: {GITHUB_REPO}")
    app.run(host="0.0.0.0", port=port, debug=False)
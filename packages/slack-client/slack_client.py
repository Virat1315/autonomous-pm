"""
slack_client.py – Shared Slack chat.postMessage client.
Used by Priority Service, Standup Service, and any future service.
"""
import os
import logging
import httpx

logger = logging.getLogger("slack-client")

SLACK_API_URL = "https://slack.com/api/chat.postMessage"
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")


async def post_message(channel: str, text: str, blocks: list = None) -> bool:
    """
    Post a message to Slack. Returns True on success.
    Silently returns False (non-raising) if token is not set.
    """
    if not SLACK_BOT_TOKEN:
        logger.warning("SLACK_BOT_TOKEN not set – skipping Slack post")
        return False

    payload = {"channel": channel, "text": text}
    if blocks:
        payload["blocks"] = blocks

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(
                SLACK_API_URL,
                headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}", "Content-Type": "application/json"},
                json=payload,
            )
            resp.raise_for_status()
            result = resp.json()
            if not result.get("ok"):
                logger.error(f"Slack API error: {result.get('error', 'unknown')}")
                return False
            logger.info(f"Message posted to Slack channel {channel}")
            return True
        except Exception as e:
            logger.error(f"Failed to post to Slack: {e}")
            return False

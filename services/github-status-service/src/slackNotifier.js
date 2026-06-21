const axios = require("axios");

async function notifySlack(text) {
  const token   = process.env.SLACK_BOT_TOKEN;
  const channel = process.env.SLACK_NOTIFY_CHANNEL;
  if (!token || !channel) return;
  try {
    await axios.post("https://slack.com/api/chat.postMessage",
      { channel, text, mrkdwn: true },
      { headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }, timeout: 8000 }
    );
  } catch (err) {
    console.error("[slack] Notification failed:", err.message);
  }
}

module.exports = { notifySlack };

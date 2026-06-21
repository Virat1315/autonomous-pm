/**
 * parser.js – Extracts ticket data from Slack messages.
 */
const TRIGGER_KEYWORDS = [
  "bug", "broken", "error", "issue", "crash", "fail", "failing",
  "not working", "fix", "problem", "incident", "outage", "ticket", "report",
];

const WATCHED_CHANNELS = process.env.WATCHED_CHANNELS
  ? process.env.WATCHED_CHANNELS.split(",").map(c => c.trim())
  : [];

function parseTicketFromMessage(message) {
  if (!message || !message.text) return null;
  if (WATCHED_CHANNELS.length > 0 && !WATCHED_CHANNELS.includes(message.channel)) return null;
  const text = message.text.toLowerCase();
  const hasTrigger = TRIGGER_KEYWORDS.some(kw => text.includes(kw));
  if (!hasTrigger) return null;
  const firstLine = message.text.split("\n")[0].trim();
  const title = firstLine.length > 200 ? firstLine.slice(0, 197) + "..." : firstLine;
  return { title, description: message.text.trim() };
}

module.exports = { parseTicketFromMessage, TRIGGER_KEYWORDS };

/**
 * ticketExtractor.js – Extracts ticket IDs from commit messages / PR titles.
 * Supports: APM-123, JIRA-style PROJ-123, closes #42, [TICKET:APM-5]
 */
const PROJECT_KEYS = process.env.JIRA_PROJECT_KEYS
  ? process.env.JIRA_PROJECT_KEYS.split(",").map(k => k.trim().toUpperCase())
  : null;

// Always include APM (our native prefix)
const APM_PATTERN = /\b(APM-\d+)\b/gi;

const JIRA_PATTERN = PROJECT_KEYS
  ? new RegExp(`\\b(${PROJECT_KEYS.join("|")})-\\d+\\b`, "gi")
  : /\b([A-Z]{2,10}-\d+)\b/gi;

const GITHUB_CLOSES_PATTERN = /(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)/gi;
const FLOWMIND_TAG_PATTERN   = /\[TICKET:([A-Z0-9_-]+)\]/gi;

function extractTicketIds(text) {
  if (!text || typeof text !== "string") return [];
  const found = new Set();

  for (const match of text.matchAll(APM_PATTERN))  found.add(match[0].toUpperCase());
  for (const match of text.matchAll(JIRA_PATTERN)) found.add(match[0].toUpperCase());
  for (const match of text.matchAll(GITHUB_CLOSES_PATTERN)) found.add(`#${match[1]}`);
  for (const match of text.matchAll(FLOWMIND_TAG_PATTERN))  found.add(match[1].toUpperCase());

  return [...found];
}

module.exports = { extractTicketIds };

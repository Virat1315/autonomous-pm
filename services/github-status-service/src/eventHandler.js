const { extractTicketIds } = require("./ticketExtractor");
const { updateTicket }     = require("./ticketClient");
const { notifySlack }      = require("./slackNotifier");

async function handleWebhookEvent(eventType, payload, delivery) {
  console.log(`[handler] Event: ${eventType} | Delivery: ${delivery}`);
  switch (eventType) {
    case "pull_request":  await handlePullRequest(payload); break;
    case "push":          await handlePush(payload);        break;
    case "issues":        await handleIssues(payload);      break;
    default: console.log(`[handler] Ignoring event '${eventType}'`);
  }
}

async function handlePullRequest(payload) {
  const { action, pull_request: pr, repository } = payload;
  if (!pr) return;
  const searchText = `${pr.title} ${pr.body || ""} ${pr.head?.ref || ""}`;
  const ticketIds = extractTicketIds(searchText);
  if (!ticketIds.length) return;

  for (const ticketId of ticketIds) {
    let newStatus = null, message = null;
    if (action === "opened" || action === "reopened") {
      newStatus = "In Progress";
      message = `🔀 PR #${pr.number} opened: <${pr.html_url}|${pr.title}>`;
    } else if (action === "closed" && pr.merged) {
      newStatus = "Done";
      message = `✅ PR #${pr.number} merged: <${pr.html_url}|${pr.title}>`;
    } else if (action === "closed" && !pr.merged) {
      newStatus = "Open";
      message = `❌ PR #${pr.number} closed (not merged): <${pr.html_url}|${pr.title}>`;
    }
    if (newStatus) await updateAndNotify(ticketId, newStatus, message);
  }
}

async function handlePush(payload) {
  const { commits = [], repository } = payload;
  const allIds = new Set();
  for (const commit of commits) {
    extractTicketIds(commit.message || "").forEach(id => allIds.add(id));
  }
  if (!allIds.size) return;
  const branch = payload.ref?.replace("refs/heads/", "") || "unknown";
  for (const ticketId of allIds) {
    await updateAndNotify(ticketId, "In Progress",
      `📦 Commit pushed to \`${branch}\` referencing *${ticketId}*`);
  }
}

async function handleIssues(payload) {
  const { action, issue } = payload;
  if (!issue) return;
  const ticketIds = extractTicketIds(`${issue.title} ${issue.body || ""}`);
  if (!ticketIds.length) return;
  let newStatus = null, message = null;
  if (action === "closed")   { newStatus = "Done"; message = `✅ GitHub Issue #${issue.number} closed`; }
  if (action === "reopened") { newStatus = "Open"; message = `🔁 GitHub Issue #${issue.number} reopened`; }
  if (newStatus) for (const id of ticketIds) await updateAndNotify(id, newStatus, message);
}

async function updateAndNotify(ticketId, status, slackMessage) {
  try {
    await updateTicket(ticketId, { status });
    console.log(`[handler] Ticket ${ticketId} → '${status}'`);
    if (slackMessage && process.env.SLACK_NOTIFY_CHANNEL) await notifySlack(slackMessage);
  } catch (err) {
    console.error(`[handler] Failed to update ${ticketId}:`, err.message);
  }
}

module.exports = { handleWebhookEvent };

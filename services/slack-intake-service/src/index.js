require("dotenv").config();
const { App, ExpressReceiver } = require("@slack/bolt");
const { parseTicketFromMessage } = require("./parser");
const { createTicket } = require("./ticketClient");

const receiver = new ExpressReceiver({
  signingSecret: process.env.SLACK_SIGNING_SECRET || "dev-secret",
  endpoints: "/slack/events",
});

const app = new App({
  token: process.env.SLACK_BOT_TOKEN,
  receiver,
});

receiver.router.get("/health", (req, res) => {
  res.json({ status: "ok", service: "slack-intake-service", port: process.env.PORT || 3006 });
});

app.message(async ({ message, client }) => {
  try {
    if (message.subtype || message.bot_id) return;
    const ticketData = parseTicketFromMessage(message);
    if (!ticketData) return;

    console.log(`[intake] Ticket trigger from ${message.user}: ${ticketData.title}`);
    const ticket = await createTicket({
      title:          ticketData.title,
      description:    ticketData.description,
      reportedBy:     message.user,
      source:         "slack",
      channel:        message.channel,
      slackMessageTs: message.ts,
    });

    await client.chat.postMessage({
      channel:   message.channel,
      thread_ts: message.ts,
      text:      `✅ Ticket created: *${ticket.ticket_id}*`,
    });
    console.log(`[intake] Ticket ${ticket.ticket_id} created`);
  } catch (err) {
    console.error("[intake] Error:", err.message);
  }
});

app.command("/ticket", async ({ command, ack, respond }) => {
  await ack();
  try {
    const text = command.text?.trim();
    if (!text) { await respond("Usage: `/ticket <description>`"); return; }

    const ticket = await createTicket({
      title:       text.split("\n")[0].slice(0, 200),
      description: text,
      reportedBy:  command.user_id,
      source:      "slack-command",
      channel:     command.channel_id,
    });

    await respond({
      text:          `✅ Ticket created: *${ticket.ticket_id}*`,
      response_type: "in_channel",
    });
  } catch (err) {
    console.error("[intake] Command error:", err.message);
    await respond("❌ Failed to create ticket. Please try again.");
  }
});

const PORT = process.env.PORT || 3006;
(async () => {
  await app.start(PORT);
  console.log(`⚡ Slack Intake Service running on port ${PORT}`);
})();

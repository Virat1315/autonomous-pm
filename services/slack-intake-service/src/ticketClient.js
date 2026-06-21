/**
 * ticketClient.js
 * HTTP client to the Ticket Service.
 * Paths: /tickets (NO /api prefix)
 */
const axios = require("axios");

const TICKET_SERVICE_URL = process.env.TICKET_SERVICE_URL || "http://localhost:3001";

async function createTicket(payload) {
  const response = await axios.post(`${TICKET_SERVICE_URL}/tickets`, {
    title:            payload.title,
    description:      payload.description,
    ticket_type:      payload.ticketType || "task",
    priority:         payload.priority   || "Medium",
    reported_by:      payload.reportedBy,
    source:           payload.source     || "slack",
    channel:          payload.channel,
    slack_message_ts: payload.slackMessageTs,
  }, {
    headers: { "Content-Type": "application/json" },
    timeout: 10000,
  });
  return response.data;
}

async function getTicket(ticketId) {
  const response = await axios.get(`${TICKET_SERVICE_URL}/tickets/${ticketId}`, { timeout: 5000 });
  return response.data;
}

module.exports = { createTicket, getTicket };

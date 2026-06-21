/**
 * ticketClient.js – Calls Ticket Service.
 * Paths: /tickets/... (NO /api prefix).
 */
const axios = require("axios");
const TICKET_SERVICE_URL = process.env.TICKET_SERVICE_URL || "http://localhost:3001";

async function updateTicket(ticketId, updates) {
  const encoded = encodeURIComponent(ticketId);
  const response = await axios.put(`${TICKET_SERVICE_URL}/tickets/${encoded}`, updates, {
    headers: { "Content-Type": "application/json" },
    timeout: 10000,
  });
  return response.data;
}

async function getTicket(ticketId) {
  const encoded = encodeURIComponent(ticketId);
  const response = await axios.get(`${TICKET_SERVICE_URL}/tickets/${encoded}`, { timeout: 5000 });
  return response.data;
}

module.exports = { updateTicket, getTicket };

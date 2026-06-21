require("dotenv").config();
const express = require("express");
const { verifyGitHubSignature } = require("./middleware");
const { handleWebhookEvent }    = require("./eventHandler");

const app = express();
app.use(express.json({
  verify: (req, res, buf) => { req.rawBody = buf; },
}));

app.get("/health", (req, res) => {
  res.json({ status: "ok", service: "github-status-service" });
});

app.post("/github-webhook", async (req, res) => {
  const signature = req.headers["x-hub-signature-256"];
  const event     = req.headers["x-github-event"];
  const delivery  = req.headers["x-github-delivery"];
  const secret    = process.env.GITHUB_WEBHOOK_SECRET;

  if (secret) {
    if (!verifyGitHubSignature(secret, signature, req.rawBody)) {
      console.warn(`[webhook] Invalid signature on ${delivery}`);
      return res.status(401).json({ error: "Invalid webhook signature" });
    }
  }

  res.status(200).json({ received: true, delivery });

  try {
    await handleWebhookEvent(event, req.body, delivery);
  } catch (err) {
    console.error(`[webhook] Error processing '${event}':`, err.message);
  }
});

const PORT = process.env.PORT || 3002;
app.listen(PORT, () => console.log(`⚡ GitHub Status Service running on port ${PORT}`));
module.exports = app;

const crypto = require("crypto");

function verifyGitHubSignature(secret, signature, rawBody) {
  if (!secret || !signature || !rawBody) return false;
  const hmac = crypto.createHmac("sha256", secret).update(rawBody).digest("hex");
  const computed = `sha256=${hmac}`;
  try {
    return crypto.timingSafeEqual(Buffer.from(computed), Buffer.from(signature));
  } catch { return false; }
}

module.exports = { verifyGitHubSignature };

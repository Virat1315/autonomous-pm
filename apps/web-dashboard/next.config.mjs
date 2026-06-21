/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  env: {
    TICKET_SERVICE_URL: process.env.TICKET_SERVICE_URL || 'http://localhost:3001',
  },
};

export default nextConfig;

FROM node:20-slim
WORKDIR /app
COPY package.json .
RUN npm install --production
COPY src/ ./src/
ENV PORT=3002
EXPOSE 3002
CMD ["node", "src/index.js"]

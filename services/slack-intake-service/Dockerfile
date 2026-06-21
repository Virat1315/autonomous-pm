FROM node:20-slim
WORKDIR /app
COPY package.json .
RUN npm install --production
COPY src/ ./src/
ENV PORT=3006
EXPOSE 3006
CMD ["node", "src/index.js"]

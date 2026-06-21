FROM python:3.12-slim
WORKDIR /app

COPY services/standup-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY packages/llm-client/ ./packages/llm-client/
COPY packages/slack-client/ ./packages/slack-client/
COPY services/standup-service/src/ ./src/

ENV PORT=3004
EXPOSE 3004
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT}"]

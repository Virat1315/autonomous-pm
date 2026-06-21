FROM python:3.12-slim
WORKDIR /app

# Install dependencies
COPY services/priority-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared packages
COPY packages/llm-client/ ./packages/llm-client/
COPY packages/slack-client/ ./packages/slack-client/

# Copy service source
COPY services/priority-service/src/ ./src/

ENV PORT=3003
EXPOSE 3003
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT}"]

# Autonomous PM

An AI-native project management platform. Describe a product idea in natural language — a hierarchy of AI agents handles planning, prioritisation, standup reporting, and GitHub integration automatically.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Ingestion Layer                        │
│   Slack Intake (:3006)      GitHub Status (:3002)         │
└──────────────────────┬──────────────────┬───────────────┘
                       │  POST /tickets   │ PUT /tickets/{id}
┌──────────────────────▼──────────────────▼───────────────┐
│             Ticket Service (:3001) – PostgreSQL           │
│          Source of truth for all tickets                  │
└──────┬─────────────────────────────────────┬────────────┘
       │                                     │
┌──────▼──────────┐  ┌──────────────┐  ┌────▼────────────┐
│ Priority (:3003) │  │ Standup(3004)│  │Orchestrator(3005)│
│ LLM priority    │  │ LLM standup  │  │ LangGraph flows  │
└─────────────────┘  └──────────────┘  └─────────────────┘
                                                │
┌───────────────────────────────────────────────▼─────────┐
│               Web Dashboard (:3000) – Next.js 14          │
└─────────────────────────────────────────────────────────┘
```

## Services

| Service | Port | Language | Purpose |
|---------|------|----------|---------|
| `web-dashboard` | 3000 | Next.js 14 / TypeScript | UI |
| `ticket-service` | 3001 | Python / FastAPI | Ticket CRUD + stats |
| `github-status-service` | 3002 | Node.js / Express | GitHub webhook receiver |
| `priority-service` | 3003 | Python / FastAPI | LLM ticket prioritisation |
| `standup-service` | 3004 | Python / FastAPI | LLM standup generator |
| `orchestrator-service` | 3005 | Python / FastAPI + LangGraph | Workflow coordinator |
| `slack-intake-service` | 3006 | Node.js / Slack Bolt | Slack event listener |

## Quick Start (Local with Docker)

### Prerequisites
- Docker Desktop (or Docker Engine + Compose plugin)
- At least one: `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`

### 1. Clone and configure

```bash
git clone <your-repo>
cd autonomous-pm
cp .env.example .env
# Edit .env and add your API keys
```

### 2. Start everything

```bash
docker compose up -d --build
```

### 3. Verify

```bash
bash scripts/health-check.sh
```

The dashboard will be at **http://localhost:3000**.

API docs:
- Ticket Service: http://localhost:3001/docs
- Priority Service: http://localhost:3003/docs
- Standup Service: http://localhost:3004/docs
- Orchestrator: http://localhost:3005/docs

---

## Environment Variables

Copy `.env.example` to `.env`:

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes (if using OpenAI) | OpenAI API key |
| `ANTHROPIC_API_KEY` | Yes (if using Anthropic) | Anthropic API key |
| `LLM_PROVIDER` | No | `openai` (default) or `anthropic` |
| `SLACK_BOT_TOKEN` | Optional | `xoxb-...` — enables Slack features |
| `SLACK_SIGNING_SECRET` | Optional | Required for Slack intake service |
| `GITHUB_WEBHOOK_SECRET` | Optional | For GitHub webhook verification |

---

## Deployment on Render

Render supports Docker-based deployments. Deploy each service as a separate **Web Service** using its Docker image, or use the **Infrastructure as Code** approach.

### Deploy each service

1. Go to [render.com](https://render.com) and create a new Web Service
2. Connect your GitHub repository
3. For each service, set:
   - **Environment**: Docker
   - **Dockerfile Path**: `services/ticket-service/Dockerfile` (adjust per service)
   - **Docker Context**: `.` (root) for priority/standup (they need shared packages), otherwise the service directory

### Recommended Render deployment order

1. **PostgreSQL** — Add a Render PostgreSQL database. Copy the `DATABASE_URL` it gives you.
2. **ticket-service** — Deploy first. Set `DATABASE_URL` from step 1.
3. **priority-service** — Deploy. Set `TICKET_SERVICE_URL` to the ticket-service Render URL.
4. **standup-service** — Deploy. Set `TICKET_SERVICE_URL`.
5. **orchestrator-service** — Deploy. Set all three service URLs.
6. **github-status-service** — Deploy. Set `TICKET_SERVICE_URL`.
7. **slack-intake-service** — Deploy. Set `TICKET_SERVICE_URL` + Slack credentials.
8. **web-dashboard** — Deploy last. Set `TICKET_SERVICE_URL`.

### Render environment variables per service

**ticket-service:**
```
DATABASE_URL         = (from Render PostgreSQL – use the "Internal Database URL")
PORT                 = 3001
SERVICE_BASE_URL     = https://your-ticket-service.onrender.com
CORS_ORIGINS         = https://your-dashboard.onrender.com
```

**priority-service:**
```
PORT                 = 3003
TICKET_SERVICE_URL   = https://your-ticket-service.onrender.com
LLM_PROVIDER         = openai
OPENAI_API_KEY       = sk-...
```

**standup-service:**
```
PORT                 = 3004
TICKET_SERVICE_URL   = https://your-ticket-service.onrender.com
LLM_PROVIDER         = openai
OPENAI_API_KEY       = sk-...
SLACK_BOT_TOKEN      = xoxb-...
SLACK_STANDUP_CHANNEL = #standup
```

**orchestrator-service:**
```
PORT                 = 3005
TICKET_SERVICE_URL   = https://your-ticket-service.onrender.com
PRIORITY_SERVICE_URL = https://your-priority-service.onrender.com
STANDUP_SERVICE_URL  = https://your-standup-service.onrender.com
```

**web-dashboard:**
```
PORT                 = 3000
TICKET_SERVICE_URL   = https://your-ticket-service.onrender.com
```

### render.yaml (optional – Infrastructure as Code)

Create this file to deploy all services at once:

```yaml
databases:
  - name: autonomous-pm-db
    databaseName: autonomous_pm
    user: apm_user

services:
  - type: web
    name: ticket-service
    env: docker
    dockerfilePath: services/ticket-service/Dockerfile
    dockerContext: services/ticket-service
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: autonomous-pm-db
          property: connectionString
      - key: PORT
        value: 3001

  - type: web
    name: web-dashboard
    env: docker
    dockerfilePath: apps/web-dashboard/Dockerfile
    dockerContext: apps/web-dashboard
    envVars:
      - key: TICKET_SERVICE_URL
        fromService:
          name: ticket-service
          type: web
          property: host
```

---

## API Reference

### Ticket Service (port 3001)

All paths are canonical. No `/api/` prefix.

```
GET    /health
GET    /stats                         → DashboardStats
GET    /tickets                       → TicketListResponse
POST   /tickets                       → Ticket (201)
GET    /tickets/{id}                  → Ticket
PUT    /tickets/{id}                  → Ticket (PATCH semantics)
POST   /tickets/{id}/assign           → Ticket
DELETE /tickets/{id}                  → { deleted: true }
```

**Canonical enum values** (use these exact strings):

| Field | Valid values |
|---|---|
| `status` | `Open`, `In Progress`, `In Review`, `Done`, `Closed`, `Blocked` |
| `priority` | `Low`, `Medium`, `High`, `Critical` |
| `ticket_type` | `bug`, `feature`, `task`, `incident`, `code_review`, `epic`, `story`, `spike` |

**Ticket ID format:** `APM-{integer}` (e.g. `APM-1`, `APM-42`)

### Orchestrator Service (port 3005)

```
POST /orchestrate/start
GET  /orchestrate/workflows
GET  /health
```

**Trigger kinds:**

| Trigger | Description | Required field |
|---|---|---|
| `slack_message` | Create ticket + prioritise | `slack_payload` |
| `github_event` | Record GitHub event | `github_payload` |
| `manual_standup` | Generate standup now | none |
| `full_pipeline` | Create + prioritise + standup | `slack_payload` |

### Priority Service (port 3003)

```
POST /tickets/prioritize    → PriorityReport
GET  /tickets/priorities    → PriorityReport (cached)
GET  /health
```

### Standup Service (port 3004)

```
POST /standup/generate      → StandupReport
GET  /standup/summary       → StandupReport (cached)
GET  /health
```

### GitHub Status Service (port 3002)

```
POST /github-webhook        → { received: true }
GET  /health
```

GitHub webhook events handled: `pull_request`, `push`, `issues`.
Ticket ID patterns detected: `APM-123`, `closes #42`, `[TICKET:APM-5]`

### Slack Intake Service (port 3006)

- **Bot events:** Detects trigger keywords in watched channels → creates tickets
- **Slash command:** `/ticket <description>` → creates ticket
- **Slack Events URL:** `https://your-slack-service/slack/events`

---

## Slack App Setup

1. Create a new app at [api.slack.com/apps](https://api.slack.com/apps)
2. Add **Bot Token Scopes**: `chat:write`, `channels:history`, `app_mentions:read`, `commands`
3. Enable **Event Subscriptions** → URL: `https://your-slack-intake-service/slack/events`
4. Subscribe to bot events: `message.channels`
5. Add slash command `/ticket` → Request URL: `https://your-slack-intake-service/slack/events`
6. Install app to workspace → copy Bot Token (`xoxb-...`) and Signing Secret

---

## GitHub Webhook Setup

1. Go to your GitHub repo → Settings → Webhooks → Add webhook
2. **Payload URL:** `https://your-github-status-service/github-webhook`
3. **Content type:** `application/json`
4. **Secret:** matches `GITHUB_WEBHOOK_SECRET` env var
5. **Events:** Pull requests, Pushes, Issues

Reference tickets in commits/PRs as: `APM-42`, `closes #42`, or `[TICKET:APM-5]`

---

## Development

### Run a single service

```bash
# Python services
cd services/ticket-service
pip install -r requirements.txt
uvicorn src.main:app --reload --port 3001

# Node services
cd services/slack-intake-service
npm install
npm run dev

# Frontend
cd apps/web-dashboard
npm install
npm run dev
```

### Database (local without Docker)

```bash
# SQLite fallback (no setup needed)
cd services/ticket-service
DATABASE_URL=sqlite+aiosqlite:///./dev.db uvicorn src.main:app --reload

# PostgreSQL
docker run -e POSTGRES_DB=autonomous_pm -e POSTGRES_USER=apm_user \
  -e POSTGRES_PASSWORD=apm_password -p 5432:5432 postgres:16-alpine
```

---

## Project Structure

```
autonomous-pm/
├── README.md
├── docker-compose.yml           # Full-stack local development
├── .env.example                 # Environment variable template
├── .gitignore
│
├── packages/
│   ├── llm-client/              # Shared Python: OpenAI + Anthropic client
│   │   └── llm_client.py
│   └── slack-client/            # Shared Python: Slack chat.postMessage
│       └── slack_client.py
│
├── services/
│   ├── ticket-service/          # Unit 2 – Python/FastAPI + PostgreSQL
│   ├── orchestrator-service/    # Unit 6 – Python/FastAPI + LangGraph
│   ├── priority-service/        # Unit 4 – Python/FastAPI + LLM
│   ├── standup-service/         # Unit 5 – Python/FastAPI + LLM
│   ├── slack-intake-service/    # Unit 1 – Node.js/Slack Bolt
│   └── github-status-service/   # Unit 3 – Node.js/Express
│
├── apps/
│   └── web-dashboard/           # Unit 7 – Next.js 14
│
├── infrastructure/
│   └── postgres/init.sql
│
└── scripts/
    ├── dev-setup.sh
    └── health-check.sh
```

# Razorpay AI Buyer Intelligence Buildathon

Welcome to our submission for the Razorpay Buildathon! This project showcases a robust, reproducible, and secure backend integrating AI capabilities for intelligent buyer evaluation.

## Prerequisites

- Python 3.12+
- Docker and Docker Compose
- Node.js (for the frontend, optional if only testing backend APIs)

## Setup Guide

### 1. Environment Configuration

Copy the example environment file and configure it:

```bash
cd backend
cp ../.env.example .env
```

**Required API Keys**:
To enable the AI capabilities and Webhooks, configure the following inside your `.env`:
- `GROQ_API_KEY`: Required for the primary LLM intent parsing.
- `SARVAM_API_KEY`: (Optional) Fallback LLM provider.
- `RAZORPAY_KEY_ID`: Your Razorpay Test Mode Key ID.
- `RAZORPAY_KEY_SECRET`: Your Razorpay Test Mode Key Secret.
- `RAZORPAY_WEBHOOK_SECRET`: (Optional) Required if you want to test webhooks.

*(Note: Leaving LLM keys empty will trigger the 100% offline, deterministic fallback engine).*

### 2. Database Setup

We use PostgreSQL running in Docker for reliable, reproducible local execution.

1. Start the PostgreSQL container:
```bash
docker-compose up -d
```
*(Note: The database is intentionally mapped to host port `5433` to prevent collision with any existing local PostgreSQL `5432` instances).*

2. Apply the Alembic database migrations:
```bash
cd backend
alembic upgrade head
```

3. Seed the database with demo users, products, and buyer personas:
```bash
python scripts/seed.py
```

### 3. Running the Application

**Start the Backend (FastAPI):**
```bash
cd backend
python -m uvicorn app.main:app --reload
```
The backend will be available at `http://localhost:8000`.

**Start the Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### 4. Running the Test Suite

Our application has a comprehensive test suite (60/60 tests passing) that verifies AI fallbacks, simulation, checkout logic, and idempotency.

```bash
cd backend
python -m pytest tests/ -v
```

## Razorpay Test Mode Configuration

### Generating a Genuine Test Order
We have provided a developer utility script to simulate a complete buyer journey and generate a real Razorpay Order ID. Run this from the `backend` directory:
```bash
python scripts/create_test_order.py
```

### Webhook Configuration
The backend exposes the Razorpay webhook endpoint at:
`POST /api/v1/webhooks/razorpay`

If you wish to test live webhooks against your local machine, you will need a public HTTPS tunnel (e.g., using `cloudflared` or `ngrok`):
```bash
# Example using cloudflared
npx cloudflared tunnel --url http://localhost:8000
```
Then, configure your Razorpay Dashboard Webhook settings to point to:
`https://<YOUR-TUNNEL-URL>/api/v1/webhooks/razorpay`

Make sure to set the `RAZORPAY_WEBHOOK_SECRET` in your `.env` to match the secret configured in the Razorpay Dashboard.
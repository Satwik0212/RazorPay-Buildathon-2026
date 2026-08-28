# Architectural Decisions

This document records the critical architectural decisions made for the Razorpay AI Buildathon 2026 project.

## 1. Synchronous Simulation (No Celery)
**Decision:** We are executing the AI buyer simulation synchronously in-process for the hackathon demo, without introducing asynchronous task queues like Celery or Redis.
**Reasoning:** The hackathon priority is proving the safety model, the API contracts, and the core transactional loop. Introducing complex asynchronous infrastructure would obscure the deterministic API boundaries and add unnecessary overhead for the demo's scale (a few personas evaluating a few dozen products).

## 2. Database-Enforced Idempotency (Order Creation)
**Decision:** Order creation is protected by a database-level `UNIQUE` constraint on `orders.authorization_id`.
**Reasoning:** The order creation flow must be strictly idempotent to protect against double clicks, network retries, agent retries, and concurrent requests. An authorization must only ever result in a single external Razorpay order. 

## 3. Pydantic-Validated LLM Outputs (No direct tool execution)
**Decision:** AI outputs must pass through rigorous structured schemas (Pydantic), business validation, and policy validation before any execution occurs. Untrusted text cannot grant tool permissions.
**Reasoning:** AI is never the source of financial truth. The AI proposes actions based on reasoning, but the deterministic backend strictly gates execution based on merchant policies, valid quotes, and authorization.

## 4. Strict Webhook Validation (Raw body HMAC)
**Decision:** All webhooks from Razorpay must be verified cryptographically using HMAC-SHA256 against the raw request body before parsing. Webhook processing is idempotent and state-aware.
**Reasoning:** We must never trust unverified webhook payloads, and we must assume duplicates or out-of-order events. Safe state transitions ensure that only verified, cryptographically sound webhook events transition the payment state.

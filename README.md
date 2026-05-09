# Distributed Voting System - Supabase Edition
### CS323 Laboratory Activity — Edge-Cloud Architecture with Fault Tolerance

A distributed voting system implementing an event-driven edge-to-cloud pipeline using **Supabase** as the backend infrastructure. Multiple independent edge nodes generate votes, a REST API ingests them, and a worker service processes them asynchronously into persistent storage.

## System Architecture

```
Edge Nodes (Python)
     │
     │  HTTP POST /vote
     ▼
┌─────────────────────────┐
│   Flask API (Local)     │  ← Cloud Run equivalent
│   Validates & enqueues  │
└────────────┬────────────┘
             │  INSERT into vote_queue
             ▼
┌─────────────────────────┐
│  Supabase vote_queue    │  ← replaces GCP Pub/Sub
│  (PostgreSQL table)     │
│  status: pending        │
└────────────┬────────────┘
             │  POLL (every 2s)
             ▼
┌─────────────────────────┐
│   Worker Service        │  ← Cloud Run Worker equivalent
│   Deduplicates & writes │
└────────────┬────────────┘
             │  UPSERT (idempotent)
             ▼
┌─────────────────────────┐
│  Supabase votes table   │  ← replaces GCP Firestore
│  (final persistent DB)  │
└─────────────────────────┘
```

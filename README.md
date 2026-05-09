# Distributed Voting System - Supabase Edition
### CS323 Laboratory Activity — Edge-Cloud Architecture with Fault Tolerance

A distributed voting system implementing an event-driven edge-to-cloud pipeline using **Supabase** as the backend infrastructure. Multiple independent edge nodes generate votes, a REST API ingests them, and a worker service processes them asynchronously into persistent storage.

### Members:
Alex Cassion = Alex Cassion 

potato715 = Michael Pabellan 

CS3C = Jayson Soriano

Michael Andres = Michael Cabot

Bjurnh = Niel Camariosa

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

### Service Mapping

| GCP Service | Supabase Equivalent | Local Service |
|---|---|---|
| Cloud Run (API) | Supabase PostgreSQL | Flask app (port 5000) |
| Pub/Sub Topic | `vote_queue` table | Rows with `status=pending` |
| Pub/Sub Subscription (Pull) | Worker polls every 2s | `worker.py` |
| Firestore | `votes` table | Persistent vote storage |

---

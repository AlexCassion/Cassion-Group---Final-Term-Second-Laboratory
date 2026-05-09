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

## Setup Instructions

### Step 1: Create Supabase Project

1. Go to https://supabase.com and sign up/log in
2. Click **New Project** and create a database
3. Go to **Settings → API** and copy:
   - **Project URL** (SUPABASE_URL)
   - **Service Role Key** (SUPABASE_SERVICE_KEY)

### Step 2: Set Up Database Schema

1. In Supabase, go to **SQL Editor**
2. Create a new query and paste the contents of `supabase_schema.sql`
3. Execute the query

The schema creates:
- **`vote_queue` table**: Message queue (API inserts, worker polls)
- **`votes` table**: Final persistent storage (Firestore equivalent)

### Step 3: Configure Environment

Create a `.env` file:

```
SUPABASE_URL=<the-supabase-project-url>
SUPABASE_SERVICE_KEY=<the-supabase-service-role-key>
API_URL=http://localhost:5000/vote
NODE_ID=edge-node-1
```

For multiple edge nodes, use unique NODE_IDs: `edge-node-1`, `edge-node-2`, etc.

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Running the System

The system has three independent components. Run each in a separate terminal.

### Terminal 1: Start the API

```bash
python app.py
```

Expected output:
```
[API] Starting Vote Ingestion API on port 5000
 * Running on http://0.0.0.0:5000
```

Endpoints:
- **POST /vote** - Receive votes from edge nodes
- **GET /health** - Health check
- **GET /stats** - API statistics (votes received/rejected)

### Terminal 2: Start the Worker

```bash
python worker.py
```

Expected output:
```
[WORKER] Starting worker service. Polling vote_queue for pending messages...
[WORKER] Poll interval: 2s
```

The worker:
- Polls the `vote_queue` table every 2 seconds
- Processes pending votes with idempotency (`doc_id = user_id + poll_id`)
- Writes to the `votes` table (Firestore equivalent)
- Can be stopped/restarted to simulate failures

### Terminal 3+: Start Edge Nodes

```bash
python edge_node.py
```

Expected output:
```
[START] Edge node 'edge-node-1' is running. Sending to: http://localhost:5000/vote
[GEN] Vote #1 | User: <uuid> | Choice: A
[SENT] Vote: <uuid> | Choice: A | Edge: edge-node-1 | Attempt: 1
```

Each edge node:
- Generates votes with unique user IDs
- Sends to the API with retry logic (3 attempts)
- Introduces random delays (1-3 seconds)
- Can run independently per group member

---

## Reflections

-placeholder-

---

## Files Overview
- **`app.py`** - Flask API (Cloud Run equivalent)
- **`edge_node.py`** - Edge node simulator
- **`worker.py`** - Message processor
- **`supabase_schema.sql`** - Database schema
- **`.env`** - Configuration (Supabase credentials) (converted to '.env.example' for visibility since github does not allow to upload an '.env' file)
- **`requirements.txt`** - Python dependencies
- **`README.md`** - This file

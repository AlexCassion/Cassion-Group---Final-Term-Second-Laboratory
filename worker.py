"""
Worker Service - Distributed Voting System
Replaces: GCP Cloud Run (Worker) + Pub/Sub subscription

Continuously polls the Supabase vote_queue table for pending messages,
processes them with idempotency guarantees, writes final votes to
the votes table (replacing Firestore), and marks messages as processed.

Run this independently from the API. It can be stopped and restarted
to simulate fault injection (worker downtime).
"""

import os
import time
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# ─── Supabase Client ──────────────────────────────────────────────────────────
SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY: str = os.environ.get("SUPABASE_SERVICE_KEY", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

POLL_INTERVAL = 2  # seconds between queue checks

# ─── Counters ─────────────────────────────────────────────────────────────────
processed_count = 0
duplicate_count = 0
error_count = 0

"""
Cloud Ingestion API - Distributed Voting System
Replaces: GCP Cloud Run (API service)

Receives vote payloads from edge nodes via HTTP POST,
validates them, and inserts them into the Supabase vote_queue table
which acts as our Pub/Sub equivalent.

Deploy this on Render, Railway, or any platform that supports Python web apps.
"""

import os
import time
from flask import Flask, request, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(_name_)

# ─── Supabase Client ──────────────────────────────────────────────────────────
SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY: str = os.environ.get("SUPABASE_SERVICE_KEY", "")  # Use service role key for server

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

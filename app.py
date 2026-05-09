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

# ─── Counters ─────────────────────────────────────────────────────────────────
received_count = 0
rejected_count = 0


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "vote-api"}), 200


@app.route("/vote", methods=["POST"])
def receive_vote():
    """
    Receive a vote from an edge node.

    Validates the payload and inserts it into the Supabase vote_queue table.
    This table acts as our message queue (replacing GCP Pub/Sub).
    The worker service polls this table to process messages.
    """
    global received_count, rejected_count

    vote = request.get_json()

    # ── Validation ────────────────────────────────────────────────────────────
    if not vote:
        rejected_count += 1
        return jsonify({"error": "Invalid payload: no JSON body"}), 400

    required_fields = ["user_id", "poll_id", "choice"]
    missing = [f for f in required_fields if f not in vote]
    if missing:
        rejected_count += 1
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    valid_choices = ["A", "B", "C"]
    if vote["choice"] not in valid_choices:
        rejected_count += 1
        return jsonify({"error": f"Invalid choice. Must be one of {valid_choices}"}), 400

    # ── Publish to Queue (Supabase vote_queue table = Pub/Sub replacement) ────
    try:
        queue_entry = {
            "user_id": vote["user_id"],
            "poll_id": vote["poll_id"],
            "choice": vote["choice"],
            "edge_id": vote.get("edge_id", "unknown"),
            "timestamp": vote.get("timestamp", time.time()),
            "time_created": vote.get("time_created", time.time()),
            "status": "pending",  # worker will update to 'processed'
        }

        supabase.table("vote_queue").insert(queue_entry).execute()

        received_count += 1
        print(
            f"[API] Accepted vote | user={vote['user_id']} | "
            f"choice={vote['choice']} | edge={vote.get('edge_id')} | "
            f"total_received={received_count}"
        )

        return jsonify({"status": "accepted", "user_id": vote["user_id"]}), 200

    except Exception as e:
        print(f"[API ERROR] Failed to queue vote: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/stats", methods=["GET"])
def stats():
    """Return API-level statistics."""
    return jsonify({
        "received": received_count,
        "rejected": rejected_count,
    }), 200

# ─── Entry Point ──────────────────────────────────────────────────────────────
if _name_ == "_main_":
    port = int(os.environ.get("PORT", 5000))
    print(f"[API] Starting Vote Ingestion API on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)

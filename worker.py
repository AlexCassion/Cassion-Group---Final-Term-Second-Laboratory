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

def process_vote(message: dict) -> bool:
    """
    Process a single vote message from the queue.

    Steps:
    1. Extract vote data from the queue row.
    2. Create an idempotent document ID (user_id + poll_id).
    3. Upsert into the `votes` table (Firestore equivalent).
    4. Mark the queue message as 'processed'.

    Args:
        message: A row from the vote_queue table.

    Returns:
        True if processed successfully, False on error.
    """
    global processed_count, duplicate_count, error_count

    try:
        vote = {
            "user_id": message["user_id"],
            "poll_id": message["poll_id"],
            "choice": message["choice"],
            "edge_id": message.get("edge_id", "unknown"),
            "timestamp": message["timestamp"],
            "time_created": message["time_created"],
            "processed_at": time.time(),
        }

        # ── Idempotency: unique key = user_id + poll_id ───────────────────────
        # Using upsert so that duplicate deliveries don't create duplicate records.
        # This mirrors the doc_id = f"{user_id}_{poll_id}" pattern from the lab.
        doc_id = f"{vote['user_id']}_{vote['poll_id']}"

        existing = (
            supabase.table("votes")
            .select("id")
            .eq("doc_id", doc_id)
            .execute()
        )

        if existing.data:
            duplicate_count += 1
            print(
                f"[WORKER] DUPLICATE detected | doc_id={doc_id} | "
                f"Skipping insertion. Total duplicates={duplicate_count}"
            )
        else:
            vote["doc_id"] = doc_id
            supabase.table("votes").insert(vote).execute()
            processed_count += 1
            print(
                f"[WORKER] Processed vote | user={vote['user_id']} | "
                f"poll={vote['poll_id']} | choice={vote['choice']} | "
                f"worker_time={time.time():.2f} | total_processed={processed_count}"
            )

        # ── Acknowledge: mark message as processed in queue ───────────────────
        supabase.table("vote_queue").update({"status": "processed"}).eq(
            "id", message["id"]
        ).execute()

        return True

    except Exception as e:
        error_count += 1
        print(f"[WORKER ERROR] Failed to process message id={message.get('id')}: {e}")
        # Do NOT mark as processed — it will be retried on next poll
        return False

def run_worker():
    """
    Main worker loop: continuously polls the vote_queue for pending messages
    and processes them. Simulates Pub/Sub Pull subscription behavior.

    Stopping this process simulates worker failure (Step 2 of fault injection).
    Restarting it demonstrates automatic recovery (Step 3).
    """
    print("[WORKER] Starting worker service. Polling vote_queue for pending messages...")
    print(f"[WORKER] Poll interval: {POLL_INTERVAL}s")

    try:
        while True:
            # ── Pull pending messages (batch of 10) ───────────────────────────
            result = (
                supabase.table("vote_queue")
                .select("*")
                .eq("status", "pending")
                .order("id", desc=False)
                .limit(10)
                .execute()
            )

            messages = result.data

 if not messages:
                print(f"[WORKER] No pending messages. Waiting {POLL_INTERVAL}s...")
            else:
                print(f"[WORKER] Found {len(messages)} pending message(s). Processing...")
                for msg in messages:
                    process_vote(msg)

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n[WORKER] Worker stopped.")
        print(
            f"[SUMMARY] Processed: {processed_count} | "
            f"Duplicates skipped: {duplicate_count} | "
            f"Errors: {error_count}"
        )


# ─── Entry Point ──────────────────────────────────────────────────────────────
if _name_ == "_main_":
    run_worker()

"""
Edge Node - Distributed Voting System
Simulates an independent edge device generating and transmitting votes
to the Cloud API (deployed on Render/Railway).

Each group member runs this independently to simulate multiple edge sources.
"""

import uuid
import random
import time
import requests
import os
import argparse

# ─── Configuration ────────────────────────────────────────────────────────────
API_URL = os.environ.get("API_URL", "http://localhost:5000/vote")
NODE_ID = os.environ.get("NODE_ID", f"edge-{uuid.uuid4().hex[:6]}")
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds between retries

# ─── Counters (for debugging / performance tracking) ──────────────────────────
votes_generated = 0
votes_sent = 0
votes_failed = 0


def generate_vote() -> dict:
    """
    Generate a synthetic vote with a unique user_id and edge node identifier.
    Each edge node adds its NODE_ID to distinguish sources in the system.
    """
    return {
        "user_id": str(uuid.uuid4()),
        "poll_id": "poll_1",
        "choice": random.choice(["A", "B", "C"]),
        "timestamp": time.time(),
        "time_created": time.time(),
        "edge_id": NODE_ID,
    }


def send_vote(vote: dict, duplicate: bool = False) -> bool:
    """
    Send a vote to the Cloud API with retry logic.
    Simulates unreliable network conditions by retrying on failure.

    Args:
        vote: The vote payload to send.
        duplicate: If True, logs this as an intentional duplicate.

    Returns:
        True if the vote was successfully sent, False otherwise.
    """
    global votes_sent, votes_failed

    label = "[DUPLICATE]" if duplicate else ""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(API_URL, json=vote, timeout=5)
            if response.status_code == 200:
                votes_sent += 1
                print(
                    f"[SENT] {label} Vote: {vote['user_id']} | "
                    f"Choice: {vote['choice']} | "
                    f"Edge: {NODE_ID} | Attempt: {attempt}"
                )
                return True
            else:
                print(
                    f"[WARN] Server returned {response.status_code} on attempt {attempt}"
                )
        except Exception as e:
            print(f"[ERROR] Transmission failed (attempt {attempt}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    votes_failed += 1
    print(f"[FAIL] Vote {vote['user_id']} could not be delivered after {MAX_RETRIES} attempts.")
    return False


def run_edge_node(simulate_duplicates: bool = False):
    """
    Main loop: continuously generates and sends votes with random delays
    to simulate real-world distributed edge behavior.

    Args:
        simulate_duplicates: If True, sends each vote twice (fault injection).
    """
    global votes_generated

    print(f"[START] Edge node '{NODE_ID}' is running. Sending to: {API_URL}")
    if simulate_duplicates:
        print("[MODE] Duplicate simulation ENABLED (fault injection mode)")

    try:
        while True:
            vote = generate_vote()
            votes_generated += 1

            print(
                f"\n[GEN] Vote #{votes_generated} | "
                f"User: {vote['user_id']} | Choice: {vote['choice']}"
            )

            send_vote(vote)

            # Fault injection: intentionally send the same vote again
            if simulate_duplicates:
                time.sleep(0.1)
                send_vote(vote, duplicate=True)

            # Random delay to simulate real-world edge behavior
            delay = random.uniform(1, 3)
            print(f"[WAIT] Next vote in {delay:.2f}s | Stats: generated={votes_generated}, sent={votes_sent}, failed={votes_failed}")
            time.sleep(delay)

    except KeyboardInterrupt:
        print(f"\n[STOP] Edge node '{NODE_ID}' stopped.")
        print(f"[SUMMARY] Generated: {votes_generated} | Sent: {votes_sent} | Failed: {votes_failed}")


# ─── Entry Point ──────────────────────────────────────────────────────────────
if _name_ == "_main_":
    parser = argparse.ArgumentParser(description="Distributed Voting Edge Node")
    parser.add_argument(
        "--duplicates",
        action="store_true",
        help="Enable duplicate vote transmission (fault injection)",
    )
    args = parser.parse_args()
    run_edge_node(simulate_duplicates=args.duplicates)
localhost

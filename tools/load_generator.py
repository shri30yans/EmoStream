"""Configurable load generator (replaces the hardcoded infinite load_test.py).

Sends reactions at a target rate with a bounded worker pool and an optional
duration, then prints a summary. Always exits -- suitable for CI smoke tests
and real capacity runs alike.

Examples:
    python tools/load_generator.py --rps 200 --duration 30
    python tools/load_generator.py --base-url http://localhost:5000 --workers 16
"""

from __future__ import annotations

import argparse
import random
import threading
import time

import requests

DEFAULT_REACTIONS = ["applause", "heart", "cheer", "wow", "fire"]


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="LivePulse load generator")
    p.add_argument("--base-url", default="http://localhost:5000")
    p.add_argument("--rps", type=float, default=100.0)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--duration", type=float, default=30.0,
                   help="Seconds to run (0 = run until Ctrl-C).")
    p.add_argument("--reactions", nargs="*", default=DEFAULT_REACTIONS)
    return p.parse_args(argv)


def run() -> None:
    args = parse_args()
    endpoint = f"{args.base_url}/v1/reactions"
    stop = time.time() + args.duration if args.duration > 0 else float("inf")
    interval = 1.0 / max(args.rps / max(args.workers, 1), 0.001)

    counters = {"sent": 0, "ok": 0, "fail": 0}
    lock = threading.Lock()

    def worker(worker_id: int) -> None:
        session = requests.Session()
        while time.time() < stop:
            payload = {
                "user_id": f"load-{worker_id}-{random.randint(1, 1_000_000)}",
                "reaction": random.choice(args.reactions),
                "timestamp": time.time(),
            }
            try:
                resp = session.post(endpoint, json=payload, timeout=5)
                ok = resp.status_code in (200, 202)
            except Exception:
                ok = False
            with lock:
                counters["sent"] += 1
                counters["ok" if ok else "fail"] += 1
            time.sleep(interval * random.uniform(0.5, 1.5))

    threads = [threading.Thread(target=worker, args=(i,), daemon=True)
               for i in range(args.workers)]
    for t in threads:
        t.start()
    try:
        for t in threads:
            t.join(timeout=max(0.0, stop - time.time()) + 1)
    except KeyboardInterrupt:
        pass
    elapsed = args.duration if args.duration > 0 else 0
    print(f"sent={counters['sent']} ok={counters['ok']} "
          f"fail={counters['fail']} elapsed={elapsed:.1f}s")


if __name__ == "__main__":
    run()

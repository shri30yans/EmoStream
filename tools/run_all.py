"""One-command local orchestrator (replaces run_script*.py).

Starts the pipeline stages as supervised subprocesses with a single
Ctrl-C shutdown. Cross-platform (no gnome-terminal dependency).

Examples:
    python tools/run_all.py --with-spark --clusters eu,us --subscribers-per-cluster 1
    python tools/run_all.py --no-load --clusters default
"""

from __future__ import annotations

import argparse
import signal
import subprocess
import sys
import time

PROCS: list[subprocess.Popen] = []


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="LivePulse local runner")
    p.add_argument("--with-spark", action="store_true",
                   help="Also launch the Spark streaming job.")
    p.add_argument("--with-load", action="store_true", default=True)
    p.add_argument("--no-load", dest="with_load", action="store_false")
    p.add_argument("--clusters", default="default",
                   help="Comma-separated cluster ids.")
    p.add_argument("--load-rps", type=float, default=50.0)
    p.add_argument("--load-duration", type=float, default=0.0)
    return p.parse_args(argv)


def spawn(cmd: list[str], label: str) -> subprocess.Popen:
    print(f"[run] {label}: {' '.join(cmd)}", flush=True)
    proc = subprocess.Popen(cmd)
    PROCS.append(proc)
    return proc


def shutdown(*_args) -> None:
    print("\n[run] stopping...", flush=True)
    for proc in PROCS:
        try:
            proc.terminate()
        except Exception:  # noqa: BLE001
            pass
    time.sleep(2)
    for proc in PROCS:
        try:
            proc.kill()
        except Exception:  # noqa: BLE001
            pass
    sys.exit(0)


def main() -> None:
    args = parse_args()
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    spawn([sys.executable, "-m", "app.ingest_api"], "ingest-api")
    time.sleep(1)
    if args.with_spark:
        spawn(["spark-submit", "streaming/spark_processor.py"], "spark")
    spawn([sys.executable, "-m", "fanout.main_publisher"], "main-publisher")

    clusters = [c.strip() for c in args.clusters.split(",") if c.strip()]
    ws_port = 8765
    for cluster in clusters:
        spawn([sys.executable, "-m", "fanout.cluster_publisher",
               "--cluster-id", cluster], f"cluster-{cluster}")
        spawn([sys.executable, "-m", "fanout.websocket_bridge",
               "--topic", f"livepulse.fanout.v1.{cluster}" if len(clusters) > 1
               else "livepulse.fanout.v1",
               "--port", str(ws_port)], f"ws-bridge-{cluster}")
        ws_port += 1

    if args.with_load:
        cmd = [sys.executable, "tools/load_generator.py",
               "--rps", str(args.load_rps)]
        if args.load_duration > 0:
            cmd += ["--duration", str(args.load_duration)]
        spawn(cmd, "load")

    print("[run] all stages up. Ctrl-C to stop.", flush=True)
    signal.pause()


if __name__ == "__main__":
    main()

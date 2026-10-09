"""Minimal WebSocket client: prints aggregated windows as they arrive.

Run:
    python client/websocket_client.py [--url ws://localhost:8765] [--limit 20]
"""

from __future__ import annotations

import argparse
import asyncio
import logging

log = logging.getLogger("livepulse.ws_client")


def parse_args(argv=None) -> argparse.Namespace:
    import config

    p = argparse.ArgumentParser(description="LivePulse WebSocket listener")
    p.add_argument("--url", default=f"ws://{config.WS_HOST}:{config.WS_PORT}")
    p.add_argument("--limit", type=int, default=0,
                   help="Stop after N messages (0 = forever).")
    p.add_argument("--reconnect-sec", type=float, default=2.0)
    return p.parse_args(argv)


async def listen(url: str, limit: int, reconnect_sec: float) -> None:
    import websockets

    seen = 0
    while True:
        try:
            async with websockets.connect(url) as ws:
                log.info("connected to %s", url)
                async for message in ws:
                    print(message, flush=True)
                    seen += 1
                    if limit and seen >= limit:
                        return
        except Exception as exc:  # noqa: BLE001 -- reconnect on any drop
            log.warning("connection lost (%s); retrying in %.1fs", exc, reconnect_sec)
            await asyncio.sleep(reconnect_sec)


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    asyncio.run(listen(args.url, args.limit, args.reconnect_sec))


if __name__ == "__main__":
    main()

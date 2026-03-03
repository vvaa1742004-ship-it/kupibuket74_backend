from __future__ import annotations

import asyncio
import logging

from app.main import main as bot_main


def run() -> None:
    logging.basicConfig(level=logging.INFO)
    logging.getLogger(__name__).info("bot started")
    asyncio.run(bot_main())


if __name__ == "__main__":
    run()

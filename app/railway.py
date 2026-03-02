from __future__ import annotations

import asyncio
import os

import uvicorn

from app.main import main as bot_main


async def run() -> None:
    port = int(os.getenv("PORT", "8000"))
    run_bot = os.getenv("RUN_BOT", "true").lower() == "true"

    server = uvicorn.Server(
        uvicorn.Config("app.api.main:app", host="0.0.0.0", port=port, log_level="info")
    )

    tasks = [asyncio.create_task(server.serve(), name="api")]
    if run_bot:
        tasks.append(asyncio.create_task(bot_main(), name="bot"))

    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

    for task in done:
        exc = task.exception()
        if exc:
            for pending_task in pending:
                pending_task.cancel()
            raise exc

    for pending_task in pending:
        await pending_task


if __name__ == "__main__":
    asyncio.run(run())


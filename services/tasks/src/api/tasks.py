import asyncio
from collections.abc import Callable, Coroutine
from typing import Any, TypedDict

from libs.utils_lib.core.rabbitmq import rabbitmq


async def resend_outbox_events(interval: int) -> None:
    """This task runs every 5 minutes"""
    while True:
        await asyncio.sleep(interval)
        await rabbitmq.broker.publish(exchange="resend_outbox_events")


class TaskInfo(TypedDict):
    task: Callable[
        [int], Coroutine[Any, Any, None]
    ]  # task is a callable that takes an int and returns a Coroutine
    interval: int  # interval is in seconds


task_registry: dict[str, TaskInfo] = {
    "resend_outbox_events": {"task": resend_outbox_events, "interval": 60},
}


async def task_scheduler() -> None:
    """Schedule all tasks dynamically based on the task_registry"""
    for task_name, task_info in task_registry.items():
        print(f"Scheduling {task_name} to run every {task_info['interval']} seconds.")

        task = task_info["task"]
        interval = task_info["interval"]
        asyncio.create_task(task(interval))

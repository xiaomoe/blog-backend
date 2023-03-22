"""Run: `wakaq-worker --app src.common.task.app`."""
from wakaq import WakaQ

from src.config import config

from .sms import SMS

app = WakaQ(
    queues=["default-priority-queue"],
    concurrency=2 * 4,
    soft_timeout=30,  # 30秒重试
    hard_timeout=60,  # 超过60秒关闭任务
    max_retries=3,  # 最多重试3次
    max_mem_percent=90,  # 内存占用百分比
    max_tasks_per_worker=5000,  # 5000次后重启 worker
    schedules=[],
    password=config.REDIS_PASSWORD,
)


@app.task(queue="default-priority-queue", max_retries=7)
def send_sms(mobile: str, code: str, expire: int | None = None) -> None:
    SMS.send(mobile, code, expire)

from datetime import timedelta

# from app.util.redis_db import redis
from redis import Redis
from wakaq import WakaQ as _App

from app.config.base import config
from app.util.sms import SMS


class APP(_App):
    def __init__(
        self,
        queues=...,
        schedules=...,
        host="localhost",
        port=6379,
        password=None,
        concurrency=0,
        exclude_queues=...,
        max_retries=None,
        soft_timeout=None,
        hard_timeout=None,
        max_mem_percent=None,
        max_tasks_per_worker=None,
        worker_log_file=None,
        scheduler_log_file=None,
        worker_log_level=None,
        scheduler_log_level=None,
        socket_timeout=15,
        socket_connect_timeout=15,
        health_check_interval=30,
        wait_timeout=1,
    ):
        super().__init__(
            queues,
            schedules,
            host,
            port,
            concurrency,
            exclude_queues,
            max_retries,
            soft_timeout,
            hard_timeout,
            max_mem_percent,
            max_tasks_per_worker,
            worker_log_file,
            scheduler_log_file,
            worker_log_level,
            scheduler_log_level,
            socket_timeout,
            socket_connect_timeout,
            health_check_interval,
            wait_timeout,
        )
        self.broker = Redis(
            host=host,
            port=port,
            password=password,
            charset="utf-8",
            decode_responses=True,
            health_check_interval=health_check_interval,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
        )


app = APP(
    queues=["default-priority-queue"],
    password=config.REDIS_PASSWORD,
    concurrency=2 * 4,
    soft_timeout=30,  # 30秒重试
    hard_timeout=60,  # 超过60秒关闭任务
    max_retries=3,  # 最多重试3次
    max_mem_percent=90,  # 内存占用百分比
    max_tasks_per_worker=5000,  # 5000次后重启 worker
    schedules=[],
)


@app.task(queue="default-priority-queue", max_retries=7)
def mytask(x, y):
    import time

    time.sleep(3)
    print(x + y)


@app.task(queue="default-priority-queue")
def send_sms(mobile: str, code: str, expire: int | timedelta = timedelta(minutes=5)):
    SMS.send(mobile, code, expire)


if __name__ == "__main__":
    mytask.delay(1, 2)

from apscheduler.schedulers.background import BackgroundScheduler

from common.logger import logger

_scheduler = BackgroundScheduler(
    timezone="Asia/Shanghai",
    job_defaults={
        "coalesce": True,
        "max_instances": 1,
        "misfire_grace_time": 60,
    },
)


def start_scheduler():
    _scheduler.start()
    logger.info("定时任务调度器已启动")


def shutdown_scheduler():
    _scheduler.shutdown(wait=False)
    logger.info("定时任务调度器已关闭")


def register_job(func, interval_minutes: int = 5):
    job = _scheduler.add_job(
        func,
        trigger="interval",
        minutes=interval_minutes,
        id=func.__name__,
        replace_existing=True,
    )
    logger.info("已注册定时任务: %s, 间隔: %d 分钟", func.__name__, interval_minutes)
    return job

try:
    from .celery import app as celery_app

    __all__ = ("celery_app",)
except ModuleNotFoundError:
    celery_app = None
    __all__ = ("celery_app",)

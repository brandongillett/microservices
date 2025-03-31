from celery import Celery  # type: ignore

c_app = Celery()

c_app.config_from_object("libs.utils_lib.core.celery")

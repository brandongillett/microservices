import time
from typing import ClassVar

from fastapi import Request
from prometheus_client import Counter, Histogram
from pydantic_settings import BaseSettings
from starlette import status
from starlette.routing import Match
from starlette.types import ASGIApp, Receive, Scope, Send


class metrics(BaseSettings):
    REQUEST_COUNT: ClassVar[Counter] = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status_code"],
    )
    REQUEST_TIME: ClassVar[Histogram] = Histogram(
        "http_request_processing_time",
        "HTTP request processing time in seconds",
        ["method", "endpoint", "status_code"],
    )


metrics = metrics()


class PrometheusMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        skip_endpoints: set[str] | None = None,
        root_path: str | None = None,
    ) -> None:
        self.app = app
        self.skip_endpoints = skip_endpoints or set()

        if root_path:
            self.skip_endpoints |= {f"{root_path}{i}" for i in skip_endpoints or set()}

    def resolve_path(self, request: Request) -> str:
        """
        Resolve the request path to match the defined routes.

        Args:
            request (Request): The incoming HTTP request.
        """
        for route in request.app.routes:
            match, _ = route.matches(request.scope)
            if match == Match.FULL:
                return getattr(route, "path", request.url.path)
        # Fallback to the actual URL path if no route matches
        return request.url.path

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)

        endpoint = self.resolve_path(request)

        if endpoint in self.skip_endpoints:
            await self.app(scope, receive, send)
            return

        method = request.method
        start_time = time.perf_counter()
        status_code = status.HTTP_408_REQUEST_TIMEOUT

        # Define a custom send to intercept the response status
        async def metrics_send(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, metrics_send)
        finally:
            if status_code != 404:
                process_time = time.perf_counter() - start_time
                labels = {
                    "method": method,
                    "endpoint": endpoint,
                    "status_code": status_code,
                }
                try:
                    metrics.REQUEST_COUNT.labels(**labels).inc()
                    metrics.REQUEST_TIME.labels(**labels).observe(process_time)
                except Exception:
                    pass

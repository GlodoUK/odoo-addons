import os
import tempfile
import threading

import odoo
import prometheus_client as prom
from odoo import models
from odoo.http import request
from odoo.service.server import PreforkServer
from prometheus_client import multiprocess

registry = None

# Utility method
def PowersOf(logbase, count, lower=0, include_zero=True):
    """Returns a list of count powers of logbase (from logbase**lower)."""
    INF = float("inf")

    if not include_zero:
        return [logbase ** i for i in range(lower, count + lower)] + [INF]
    else:
        return [0] + [logbase ** i for i in range(lower, count + lower)] + [INF]


# The base metrics we're tracking
class PromMetrics(object):
    # HTTP

    RequestCounter = prom.Counter(
        "http_requests_total", "Total number of HTTP requests.", ["method", "scheme"]
    )

    ResponseCounter = prom.Counter(
        "http_responses_total", "Total number of HTTP responses.", ["status"]
    )

    LatencyHistogram = prom.Histogram(
        "http_latency_seconds", "Overall HTTP transaction latency."
    )

    RequestSizeHistogram = prom.Histogram(
        "http_requests_body_bytes",
        "Breakdown of HTTP requests by content length.",
        buckets=PowersOf(2, 25),
    )

    ResponseSizeHistogram = prom.Histogram(
        "http_responses_body_bytes",
        "Breakdown of HTTP responses by content length.",
        buckets=PowersOf(2, 25),
    )

    # Postgres

    PostgresQueryTime = prom.Histogram("postgresql_query_time", "SQL query time")

    PostgresQueryCount = prom.Histogram(
        "postgresql_query_count",
        "SQL query count per request/cron",
        buckets=PowersOf(2, 10),
    )

    # Cron / Scheduled Actions

    CronJobCounter = prom.Counter(
        "cron_job_executions_total", "Total number of cron jobs.", ["job"]
    )

    # Using a gauge for now, because I think a full histogram per-job (since
    # they probably run infrequently) is unnecessary?
    CronJobTime = prom.Gauge(
        "cron_job_latency_seconds", "Overall Cron transaction latency, per job", ["job"]
    )


if odoo.tools.config.get("prometheus_enabled"):

    class IrHttp(models.AbstractModel):
        _inherit = "ir.http"

        @classmethod
        def _dispatch(cls):
            path_info = request.httprequest.environ.get("PATH_INFO")
            if path_info.startswith("/longpolling/"):
                return super(IrHttp, cls)._dispatch()

            PromMetrics.RequestCounter.labels(
                request.httprequest.method, request.httprequest.scheme
            ).inc()
            content_length = request.httprequest.content_length
            if content_length is not None:
                PromMetrics.RequestSizeHistogram.observe(content_length)

            with PromMetrics.LatencyHistogram.time():
                ret = super(IrHttp, cls)._dispatch()

            current_thread = threading.current_thread()
            if hasattr(current_thread, "query_count"):
                query_count = current_thread.query_count
                query_time = current_thread.query_time

                PromMetrics.PostgresQueryTime.observe(query_time)
                PromMetrics.PostgresQueryCount.observe(query_count)

            PromMetrics.ResponseCounter.labels(ret.status_code).inc()

            content_length = ret.content_length
            if content_length is not None:
                PromMetrics.ResponseSizeHistogram.observe(content_length)

            return ret

    class IrCron(models.AbstractModel):
        _inherit = "ir.cron"

        @classmethod
        def _process_job(cls, job_cr, job, cron_cr):
            ret = None

            PromMetrics.CronJobCounter.labels(job["cron_name"]).inc()

            with PromMetrics.CronJobTime.labels(job["cron_name"]).time():
                ret = super(IrCron, cls)._process_job(job_cr, job, cron_cr)

            return ret

    # Monkey patch the worker exit methods. This is needed for Prometheus
    # multiprocessing mode.
    def pop_wrapper(worker_pop):
        def prometheus_worker_pop(self, pid):
            prom.multiprocess.mark_process_dead(pid)
            worker_pop(self, pid)

        return prometheus_worker_pop

    def kill_wrapper(worker_kill):
        def prometheus_worker_kill(self, pid, sig):
            prom.multiprocess.mark_process_dead(pid)
            worker_kill(self, pid, sig)

        return prometheus_worker_kill

    odoo.service.server.PreforkServer.worker_pop = pop_wrapper(PreforkServer.worker_pop)
    odoo.service.server.PreforkServer.worker_kill = kill_wrapper(
        PreforkServer.worker_kill
    )

    # Setup our prometheus multiprocess temp dir

    tempdir = tempfile.mkdtemp()
    os.environ["prometheus_multiproc_dir"] = tempdir

    registry = prom.CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)

    prom_listen_port = int(odoo.tools.config.get("prometheus_listen_port", "0"))

    if prom_listen_port > 0:
        prom.start_http_server(int(prom_listen_port))
    else:

        class PrometheusController(odoo.http.Controller):
            @odoo.http.route(["/metrics"], auth="none", method=["GET"])
            def metrics(self, **get):
                """
                Provide Prometheus metrics
                """

                data = prom.generate_latest()

                session = odoo.http.request.session
                # We set a custom expiration of 1 second for this request, as we do a
                # lot of health checks, we don't want those anonymous sessions to be
                # kept.
                if not session.uid:
                    # Will change session.should_save to False. It cannot be directly
                    # accessed so we do it like this.
                    session.modified = False
                    session.expiration = 1

                return odoo.http.Response(data, mimetype=prom.CONTENT_TYPE_LATEST)

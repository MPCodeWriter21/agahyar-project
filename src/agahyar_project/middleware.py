"""Custom middleware for security headers and profiling."""

import cProfile
import pstats

from django.db import connection
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add Content-Security-Policy and other security headers."""

    def process_response(self, request, response: HttpResponse) -> HttpResponse:
        response["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline'; "
            "font-src 'self'; "
            "img-src 'self' data: https://tile.openstreetmap.org https://*.tile.openstreetmap.org; "
            "frame-ancestors 'none'; "
            "form-action 'self'"
        )
        response["X-Content-Type-Options"] = "nosniff"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


class ProfilingMiddleware(MiddlewareMixin):
    """Profile each request with cProfile and append stats to the response.

    Enable by setting ``ENABLE_PROFILING=True`` in the environment.
    When active, a ``X-Profile-Queries`` header is added to every response
    with the number of SQL queries executed, and a full cProfile report
    is appended to HTML responses when ``?profile=1`` is in the query
    string.
    """

    def process_request(self, request):
        request._profiler = cProfile.Profile()
        request._profiler.enable()
        request._query_start = len(connection.queries)

    def process_response(self, request, response: HttpResponse) -> HttpResponse:
        profiler = getattr(request, "_profiler", None)
        if profiler is None:
            return response

        profiler.disable()

        query_start = getattr(request, "_query_start", 0)
        query_count = len(connection.queries) - query_start

        response["X-Profile-Queries"] = str(query_count)

        if request.GET.get("profile") == "1" and "text/html" in response.get(
            "Content-Type", ""
        ):
            rows = self._build_table_rows(profiler, query_count)
            block = self._build_html_block(rows)
            content = response.content.decode("utf-8", errors="replace")
            content = content.replace("</body>", f"{block}</body>")
            response.content = content.encode("utf-8")

        return response

    @staticmethod
    def _build_table_rows(profiler, query_count):
        stats = pstats.Stats(profiler)
        stats.sort_stats("cumulative")
        raw = stats.stats

        entries = []
        for func, (cc, nc, tt, ct, callers) in raw.items():
            filename, lineno, funcname = func
            entries.append(
                {
                    "ncalls": nc,
                    "tottime": tt,
                    "cumtime": ct,
                    "percall": tt / nc if nc else 0,
                    "filename": filename,
                    "lineno": lineno,
                    "funcname": funcname,
                }
            )

        entries.sort(key=lambda e: e["cumtime"], reverse=True)
        return entries[:50], query_count

    @staticmethod
    def _build_html_block(rows_data):
        entries, query_count = rows_data
        table_rows = ""
        for i, e in enumerate(entries):
            bg = "#1e1e1e" if i % 2 == 0 else "#252526"
            table_rows += (
                f"<tr style='background:{bg};'>"
                f"<td style='padding:6px 10px;border-bottom:1px solid #333;'>{e['ncalls']}</td>"
                f"<td style='padding:6px 10px;border-bottom:1px solid #333;text-align:right;'>{e['tottime']:.6f}</td>"
                f"<td style='padding:6px 10px;border-bottom:1px solid #333;text-align:right;'>{e['cumtime']:.6f}</td>"
                f"<td style='padding:6px 10px;border-bottom:1px solid #333;text-align:right;'>{e['percall']:.6f}</td>"
                f"<td style='padding:6px 10px;border-bottom:1px solid #333;'>{e['filename']}:{e['lineno']}</td>"
                f"<td style='padding:6px 10px;border-bottom:1px solid #333;'>{e['funcname']}</td>"
                f"</tr>\n"
            )

        return (
            "\n<div id='profiler-report' style='margin-top:24px;border-top:3px solid #1a5f7a;"
            "background:#1e1e1e;color:#d4d4d4;padding:16px;font-family:monospace;"
            "font-size:12px;direction:ltr;text-align:left;'>"
            f"<h3 style='margin:0 0 12px;color:#569cd6;'>Profiling Report</h3>"
            f"<p style='margin:0 0 12px;color:#9cdcfe;'>SQL queries: {query_count} &middot; "
            f"Top 50 functions by cumulative time</p>"
            "<div style='overflow:auto;max-height:80vh;'>"
            "<table style='width:100%;border-collapse:collapse;'>"
            "<thead><tr style='background:#2d2d2d;position:sticky;top:0;'>"
            "<th style='padding:6px 10px;text-align:left;border-bottom:2px solid #569cd6;'>ncalls</th>"
            "<th style='padding:6px 10px;text-align:right;border-bottom:2px solid #569cd6;'>tottime</th>"
            "<th style='padding:6px 10px;text-align:right;border-bottom:2px solid #569cd6;'>cumtime</th>"
            "<th style='padding:6px 10px;text-align:right;border-bottom:2px solid #569cd6;'>percall</th>"
            "<th style='padding:6px 10px;text-align:left;border-bottom:2px solid #569cd6;'>location</th>"
            "<th style='padding:6px 10px;text-align:left;border-bottom:2px solid #569cd6;'>function</th>"
            "</tr></thead>\n"
            f"<tbody>\n{table_rows}</tbody>"
            "</table></div></div>\n"
        )

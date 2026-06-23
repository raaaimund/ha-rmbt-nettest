"""Synchronous RMBT speed test runner — always executed in a thread-pool executor."""

from __future__ import annotations

import threading
import time
from typing import Any
from urllib.parse import urlparse

from rmbt_nettest import connection, control, pretest, tests

_MAX_THREADS = 20


def _run_phase(
    n: int,
    addr: str,
    port: int,
    use_tls: bool,
    no_tls_verify: bool,
    protocol: str,
    token: str,
    duration: int,
    chunk_size: int,
    phase: str,
) -> list:
    barrier = threading.Barrier(n)
    results: list = [None] * n

    def worker(i: int) -> None:
        try:
            conn = connection.RmbtConn.connect(addr, port, use_tls, no_tls_verify, protocol)
            conn.greeting(token)
        except Exception:
            barrier.wait()
            return
        barrier.wait()
        try:
            if phase == "download":
                results[i] = tests.run_download(conn, duration, chunk_size, i)
            else:
                results[i] = tests.run_upload(conn, duration, chunk_size, i, False)
            conn.quit()
        except Exception:
            pass
        finally:
            conn.close()

    pool = [threading.Thread(target=worker, args=(i,), daemon=True) for i in range(n)]
    for t in pool:
        t.start()
    for t in pool:
        t.join()

    return [r for r in results if r is not None]


def run_speedtest(
    host: str,
    client_uuid: str | None = None,
    threads: int = 0,
    duration: int = 0,
    no_tls_verify: bool = False,
    version: str = "1.0.0",
) -> dict[str, Any]:
    """Run a full RMBT speed test and return a results dict.

    Blocks for the duration of the test (~30–60 s). Must be called via
    hass.async_add_executor_job() from async context.
    """
    if not host.startswith(("http://", "https://")):
        host = "https://" + host

    uuid = control.request_settings(host, client_uuid, version, False)
    params = control.request_test(host, uuid, version, False, False)

    proto = (
        connection.PROTO_WS
        if params.server_type == "RMBTws"
        else connection.PROTO_HTTP
    )

    if params.wait > 0:
        time.sleep(params.wait)

    port = params.server_port
    test_duration = duration or params.duration
    server_cap = min(params.num_threads, _MAX_THREADS)

    pt = pretest.run_pretest(
        params.server_addr, port, params.encryption, no_tls_verify,
        proto, params.token, server_cap,
    )

    dl_threads = max(1, min(threads or pt.dl_threads, server_cap))
    ul_threads = max(1, min(threads or pt.ul_threads, server_cap))
    dl_chunk = pt.chunk_size
    ul_chunk = min(dl_chunk, tests.MAX_UL_CHUNK)

    test_begin_ms = int(time.time() * 1000)

    # Ping phase
    ping_conn = connection.RmbtConn.connect(
        params.server_addr, port, params.encryption, no_tls_verify, proto,
    )
    ping_conn.greeting(params.token)
    ping_results = tests.run_ping(ping_conn, 1.0, 10, 100)
    ping_conn.quit()
    ping_conn.close()

    # Download phase
    dl_results = _run_phase(
        dl_threads, params.server_addr, port, params.encryption, no_tls_verify,
        proto, params.token, test_duration, dl_chunk, "download",
    )
    if not dl_results:
        raise RuntimeError("All download threads failed")

    # Upload phase
    ul_results = _run_phase(
        ul_threads, params.server_addr, port, params.encryption, no_tls_verify,
        proto, params.token, test_duration, ul_chunk, "upload",
    )
    if not ul_results:
        raise RuntimeError("All upload threads failed")

    # Aggregate
    dl_bytes = sum(r.bytes for r in dl_results)
    dl_ns = max(r.elapsed_ns for r in dl_results)
    ul_bytes = sum(r.bytes for r in ul_results)
    ul_ns = max(r.elapsed_ns for r in ul_results)

    dl_mbps = dl_bytes * 8.0 / (dl_ns / 1e9) / 1e6
    ul_mbps = ul_bytes * 8.0 / (ul_ns / 1e9) / 1e6

    sorted_pings = sorted(r.client_ns for r in ping_results)
    ping_min_ms = sorted_pings[0] / 1e6 if sorted_pings else 0.0
    ping_median_ms = sorted_pings[len(sorted_pings) // 2] / 1e6 if sorted_pings else 0.0
    ping_shortest_server = min(r.server_ns for r in ping_results) if ping_results else 0

    _parsed = urlparse(host)
    result_url = (
        f"{_parsed.scheme}://{_parsed.netloc}/share/{params.open_test_uuid}"
        if params.open_test_uuid
        else None
    )

    speed_detail = [
        {"direction": "download", "thread": r.thread_id, "time": t, "bytes": b}
        for r in dl_results
        for b, t in r.samples
    ] + [
        {"direction": "upload", "thread": r.thread_id, "time": t, "bytes": b}
        for r in ul_results
        for b, t in r.samples
    ]

    control.submit_result(host, {
        "client_language": "en",
        "client_name": "RMBTws" if proto == connection.PROTO_WS else "RMBT",
        "client_uuid": uuid,
        "client_version": version,
        "client_software_version": version,
        "geoLocations": [],
        "model": "Home Assistant",
        "network_type": 98,
        "platform": "HA",
        "product": "rmbt-nettest-ha",
        "pings": [
            {"value": r.client_ns, "value_server": r.server_ns, "time_ns": r.time_ns}
            for r in ping_results
        ],
        "test_bytes_download": dl_bytes,
        "test_bytes_upload": ul_bytes,
        "test_nsec_download": dl_ns,
        "test_nsec_upload": ul_ns,
        "test_num_threads": len(dl_results),
        "num_threads_ul": len(ul_results),
        "test_ping_shortest": ping_shortest_server,
        "test_speed_download": int(dl_bytes * 8e6 / dl_ns),
        "test_speed_upload": int(ul_bytes * 8e6 / ul_ns),
        "test_token": params.token,
        "test_uuid": params.test_uuid,
        "time": test_begin_ms,
        "timezone": "UTC",
        "type": "DESKTOP",
        "version_code": "1",
        "speed_detail": speed_detail,
        "user_server_selection": False,
        "test_status": "0",
        "test_port_remote": port,
    }, False)

    return {
        "uuid": uuid,
        "download_mbps": dl_mbps,
        "upload_mbps": ul_mbps,
        "ping_min_ms": ping_min_ms,
        "ping_median_ms": ping_median_ms,
        "ping_count": len(ping_results),
        "result_url": result_url,
        "test_uuid": params.test_uuid,
        "open_test_uuid": params.open_test_uuid,
    }

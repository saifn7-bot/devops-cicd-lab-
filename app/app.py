import os
import time

from flask import Flask, Response, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

app = Flask(__name__)
APP_VERSION = os.getenv("APP_VERSION", "dev")

REQUESTS = Counter(
    "app_requests_total", "Total HTTP requests", ["endpoint", "method", "status"]
)
LATENCY = Histogram(
    "app_request_latency_seconds", "Request latency in seconds", ["endpoint"]
)


@app.before_request
def start_timer():
    g.start = time.perf_counter()


@app.after_request
def record_metrics(response):
    if request.path != "/metrics":
        endpoint = request.url_rule.rule if request.url_rule else "unknown"
        LATENCY.labels(endpoint).observe(time.perf_counter() - g.start)
        REQUESTS.labels(endpoint, request.method, str(response.status_code)).inc()
    return response


@app.route("/")
def index():
    return jsonify(message="Hello from the DevOps CI/CD lab message is added", version=APP_VERSION)


@app.route("/health")
def health():
    return jsonify(status="ok"), 200


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

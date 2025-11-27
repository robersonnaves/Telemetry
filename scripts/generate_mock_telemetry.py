#!/usr/bin/env python3
"""
Script para gerar e enviar dados mockados de telemetria (traces, metrics, logs)
para a stack de observabilidade via OpenTelemetry Collector.

Requisitos:
    pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc faker requests

Uso:
    python generate_mock_telemetry.py --duration 300 --interval 5
"""

import argparse
import random
import time
import sys
from datetime import datetime
from typing import List

try:
    from opentelemetry import trace, metrics
    from opentelemetry.metrics import Observation
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.trace import Status, StatusCode
    from faker import Faker
    import requests
except ImportError as e:
    print(f"Erro: Dependência ausente. Instale com:")
    print("pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc faker requests")
    sys.exit(1)


# Configuração
# Usa localhost para enviar ao collector exposto na máquina host (porta 4317) e Loki em 3100.
OTEL_ENDPOINT = "http://localhost:4317"  # OpenTelemetry Collector gRPC
LOKI_ENDPOINT = "http://localhost:3100/loki/api/v1/push"  # Loki para logs

fake = Faker()


def setup_telemetry(service_name: str = "mock-telemetry-generator"):
    """Configura providers de trace e metrics para OTLP"""
    resource = Resource.create({"service.name": service_name, "environment": "development"})
    
    # Traces
    trace_provider = TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True)
    trace_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(trace_provider)
    
    # Metrics
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=OTEL_ENDPOINT, insecure=True),
        export_interval_millis=10000
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)
    
    return trace.get_tracer(__name__), metrics.get_meter(__name__)


def generate_traces(tracer, count: int = 5):
    """Gera traces mockados simulando operações de API"""
    endpoints = ["/api/users", "/api/products", "/api/orders", "/api/payments", "/api/inventory"]
    methods = ["GET", "POST", "PUT", "DELETE"]
    
    for _ in range(count):
        endpoint = random.choice(endpoints)
        method = random.choice(methods)
        user_id = fake.uuid4()
        
        with tracer.start_as_current_span(f"{method} {endpoint}") as span:
            span.set_attribute("http.method", method)
            span.set_attribute("http.url", f"https://api.example.com{endpoint}")
            span.set_attribute("http.status_code", random.choice([200, 200, 200, 201, 400, 404, 500]))
            span.set_attribute("user.id", user_id)
            span.set_attribute("client.ip", fake.ipv4())
            
            # Simula processamento
            processing_time = random.uniform(0.01, 0.5)
            time.sleep(processing_time)
            
            # Simula chamadas de banco de dados
            with tracer.start_as_current_span("db.query") as db_span:
                db_span.set_attribute("db.system", "postgresql")
                db_span.set_attribute("db.statement", f"SELECT * FROM {endpoint.split('/')[-1]} WHERE id = $1")
                time.sleep(random.uniform(0.005, 0.1))
            
            # Simula falhas ocasionais
            if random.random() < 0.1:
                span.set_status(Status(StatusCode.ERROR, "Random simulated error"))
                span.set_attribute("error", True)
            else:
                span.set_status(Status(StatusCode.OK))


def generate_metrics(request_counter, error_counter, latency_histogram):
    """Gera métricas mockadas usando instrumentos pré-criados"""
    # Gera dados
    endpoints = ["/api/users", "/api/products", "/api/orders"]
    methods = ["GET", "POST", "PUT"]
    
    for _ in range(random.randint(10, 30)):
        endpoint = random.choice(endpoints)
        method = random.choice(methods)
        status = random.choice([200, 200, 200, 201, 400, 404, 500])
        
        attributes = {
            "endpoint": endpoint,
            "method": method,
            "status": str(status)
        }
        
        request_counter.add(1, attributes)
        
        if status >= 400:
            error_counter.add(1, attributes)
        
        latency_histogram.record(random.uniform(0.01, 2.0), attributes)


def generate_logs(count: int = 10):
    """Gera logs mockados e envia para Loki"""
    log_levels = ["DEBUG", "INFO", "INFO", "INFO", "WARN", "ERROR"]
    services = ["api-gateway", "user-service", "order-service", "payment-service"]
    
    logs = []
    for _ in range(count):
        level = random.choice(log_levels)
        service = random.choice(services)
        timestamp = int(time.time() * 1e9)  # nanoseconds
        
        messages = {
            "DEBUG": f"Processing request for user {fake.uuid4()}",
            "INFO": f"{fake.user_name()} logged in from {fake.ipv4()}",
            "WARN": f"High latency detected: {random.randint(1000, 3000)}ms",
            "ERROR": f"Failed to connect to database: {fake.word()}"
        }
        
        log_entry = {
            "stream": {
                "service": service,
                "level": level,
                "environment": "development"
            },
            "values": [
                [str(timestamp), messages.get(level, "Generic log message")]
            ]
        }
        logs.append(log_entry)
    
    # Envia para Loki
    try:
        payload = {"streams": logs}
        response = requests.post(LOKI_ENDPOINT, json=payload, timeout=5)
        if response.status_code != 204:
            print(f"⚠️  Loki returned status {response.status_code}")
    except Exception as e:
        print(f"⚠️  Failed to send logs to Loki: {e}")


def main():
    parser = argparse.ArgumentParser(description="Generate mock telemetry data")
    parser.add_argument("--duration", type=int, default=300, help="Duration in seconds (default: 300)")
    parser.add_argument("--interval", type=int, default=5, help="Interval between batches in seconds (default: 5)")
    parser.add_argument("--service", type=str, default="mock-telemetry-generator", help="Service name")
    parser.add_argument("--traces", type=int, default=5, help="Number of traces per batch (default: 5)")
    parser.add_argument("--logs", type=int, default=10, help="Number of logs per batch (default: 10)")
    parser.add_argument("--no-traces", action="store_true", help="Disable trace generation")
    parser.add_argument("--no-metrics", action="store_true", help="Disable metrics generation")
    parser.add_argument("--no-logs", action="store_true", help="Disable log generation")
    
    args = parser.parse_args()
    
    print(f"🚀 Mock Telemetry Generator")
    print(f"   Service: {args.service}")
    print(f"   Duration: {args.duration}s | Interval: {args.interval}s")
    print(f"   OTLP Endpoint: {OTEL_ENDPOINT}")
    print(f"   Loki Endpoint: {LOKI_ENDPOINT}")
    print(f"   Traces: {'✓' if not args.no_traces else '✗'} | Metrics: {'✓' if not args.no_metrics else '✗'} | Logs: {'✓' if not args.no_logs else '✗'}")
    print()
    
    tracer, meter = setup_telemetry(args.service)
    
    # Create metrics instruments once to avoid duplicate warnings
    request_counter = meter.create_counter(
        "http_requests_total",
        description="Total HTTP requests",
        unit="1"
    )
    
    error_counter = meter.create_counter(
        "http_errors_total",
        description="Total HTTP errors",
        unit="1"
    )
    
    latency_histogram = meter.create_histogram(
        "http_request_duration_seconds",
        description="HTTP request latency",
        unit="s"
    )
    
    def get_active_connections():
        return random.randint(10, 100)
    
    def active_connections_callback(options):
        value = get_active_connections()
        return [Observation(value, {})]

    meter.create_observable_gauge(
        "active_connections",
        callbacks=[active_connections_callback],
        description="Number of active connections"
    )
    
    start_time = time.time()
    iteration = 0
    
    try:
        while time.time() - start_time < args.duration:
            iteration += 1
            batch_start = time.time()
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Batch #{iteration}", end=" ")
            
            if not args.no_traces:
                generate_traces(tracer, args.traces)
                print("| Traces ✓", end=" ")
            
            if not args.no_metrics:
                generate_metrics(request_counter, error_counter, latency_histogram)
                print("| Metrics ✓", end=" ")
            
            if not args.no_logs:
                generate_logs(args.logs)
                print("| Logs ✓", end=" ")
            
            elapsed = time.time() - batch_start
            print(f"| {elapsed:.2f}s")
            
            # Aguarda próximo intervalo
            sleep_time = max(0, args.interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Interrompido pelo usuário")
    
    print(f"\n✅ Gerados {iteration} batches em {time.time() - start_time:.1f}s")


if __name__ == "__main__":
    main()

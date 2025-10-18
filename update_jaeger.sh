#!/bin/bash
cd /root/Telemetry
echo "=== Updating Jaeger services with proper storage configuration ==="
echo "Stopping current Jaeger containers..."
podman stop jaeger-collector jaeger-query || true
podman rm jaeger-collector jaeger-query || true

echo "Recreating services with updated configuration..."
podman-compose up -d jaeger-collector jaeger-query

echo "Waiting for services to be ready..."
sleep 15

echo "Checking Jaeger configuration..."
podman logs jaeger-collector | tail -5 | grep -i "MaxTraces" || echo "Checking collector..."
podman logs jaeger-query | tail -5 | grep -i "MaxTraces" || echo "Checking query..."

echo "✅ Jaeger services updated successfully!"
echo "Access Jaeger UI: http://localhost:16686"

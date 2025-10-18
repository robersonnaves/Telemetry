# Stack de Telemetria com OpenTelemetry

Uma stack simplificada de observabilidade usando Docker Compose com OpenTelemetry Collector e Jaeger All-in-One.

## 🏗️ Arquitetura

```
Applications → OpenTelemetry Collector → Traces → Jaeger All-in-One
                    (OTLP)                    ↓
                                         Metrics → Prometheus
```

### Por que três serviços?

- **OpenTelemetry Collector**: Coletor universal que recebe dados via OTLP de diferentes aplicações e protocolos
- **Jaeger All-in-One**: Sistema completo de tracing distribuído com interface web para visualização
- **Prometheus**: Sistema de monitoramento e armazenamento de métricas em séries temporais

## 📋 Pré-requisitos

- Docker e Docker Compose instalados
- Pelo menos 2GB de RAM disponível
- Pelo menos 1GB de espaço em disco

## 🚀 Como Usar

### 1. Iniciar a Stack

```bash
# Clone ou baixe este repositório
cd /path/to/Telemetry

# Iniciar todos os serviços
docker-compose up -d

# Verificar status dos serviços
docker-compose ps
```

### 2. Acessar os Serviços

| Serviço | URL | Descrição |
|---------|-----|-----------|
| **Jaeger UI** | http://localhost:16686 | Interface web para visualização de traces |
| **Prometheus** | http://localhost:9090 | Interface web para visualização de métricas |
| **OTLP gRPC** | localhost:4317 | Endpoint para envio de traces e métricas via OTLP gRPC |

### 3. Enviar Dados de Teste

#### Enviar Traces via OTLP gRPC

```bash
# Exemplo usando grpcurl para enviar trace via gRPC
grpcurl -plaintext -d '{
  "resourceSpans": [{
    "resource": {
      "attributes": [{
        "key": "service.name",
        "value": {"stringValue": "test-service"}
      }]
    },
    "scopeSpans": [{
      "spans": [{
        "traceId": "12345678901234567890123456789012",
        "spanId": "1234567890123456",
        "name": "test-span",
        "startTimeUnixNano": "1640995200000000000",
        "endTimeUnixNano": "1640995201000000000"
      }]
    }]
  }]
}' localhost:4317 opentelemetry.proto.collector.trace.v1.TraceService/Export
```

#### Usando SDKs OpenTelemetry

##### Python
```python
# Exemplo Python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configurar o exporter
exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Adicionar o exporter
span_processor = BatchSpanProcessor(exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Criar uma trace
with tracer.start_as_current_span("test-operation") as span:
    span.set_attribute("service.name", "test-service")
    span.set_attribute("operation", "test")
```

##### C# (.NET)
```csharp
// Exemplo C# - Program.cs
using OpenTelemetry;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;
using OpenTelemetry.Metrics;
using System.Diagnostics;

// Configurar o OpenTelemetry
using var tracerProvider = Sdk.CreateTracerProviderBuilder()
    .SetResourceBuilder(ResourceBuilder.CreateDefault()
        .AddService(serviceName: "test-service", serviceVersion: "1.0.0"))
    .AddSource("MyApplication")
    .AddOtlpExporter(options =>
    {
        options.Endpoint = new Uri("http://localhost:4317");
    })
    .Build();

// Configurar métricas
using var meterProvider = Sdk.CreateMeterProviderBuilder()
    .SetResourceBuilder(ResourceBuilder.CreateDefault()
        .AddService(serviceName: "test-service", serviceVersion: "1.0.0"))
    .AddMeter("MyApplication")
    .AddOtlpExporter(options =>
    {
        options.Endpoint = new Uri("http://localhost:4317");
    })
    .Build();

// Criar um ActivitySource e Meter
using var activitySource = new ActivitySource("MyApplication");
using var meter = new Meter("MyApplication");

// Criar contadores de métricas
var requestCounter = meter.CreateCounter<int>("requests_total", "Total number of requests");
var responseTimeHistogram = meter.CreateHistogram<double>("response_time_seconds", "Response time in seconds");

// Criar uma trace
using var activity = activitySource.StartActivity("test-operation");
activity?.SetTag("service.name", "test-service");
activity?.SetTag("operation", "test");
activity?.SetTag("http.method", "GET");
activity?.SetTag("http.url", "http://localhost:5000/api/test");

// Simular trabalho e registrar métricas
var stopwatch = Stopwatch.StartNew();
await Task.Delay(100);
stopwatch.Stop();

// Registrar métricas
requestCounter.Add(1, new KeyValuePair<string, object?>("method", "GET"));
responseTimeHistogram.Record(stopwatch.Elapsed.TotalSeconds);

Console.WriteLine($"Trace ID: {activity?.TraceId}");
Console.WriteLine($"Span ID: {activity?.SpanId}");
Console.WriteLine($"Response time: {stopwatch.ElapsedMilliseconds}ms");
```

##### Dependências NuGet para C#
```xml
<!-- Exemplo de PackageReference no .csproj -->
<PackageReference Include="OpenTelemetry" Version="1.7.0" />
<PackageReference Include="OpenTelemetry.Exporter.OpenTelemetryProtocol" Version="1.7.0" />
<PackageReference Include="OpenTelemetry.Extensions.Hosting" Version="1.7.0" />
<PackageReference Include="System.Diagnostics.DiagnosticSource" Version="8.0.0" />
```

### 4. Parar a Stack

```bash
# Parar todos os serviços
docker-compose down

# Parar e remover volumes (CUIDADO: apaga todos os dados)
docker-compose down -v
```

## 📊 Funcionalidades Disponíveis

### Jaeger UI
- **Search**: Busca de traces por serviço, operação, tags e tempo
- **Trace Details**: Visualização detalhada de spans e dependências
- **Service Map**: Mapa de dependências entre serviços
- **Compare**: Comparação de traces
- **Dependencies**: Análise de dependências entre serviços

### Prometheus UI
- **Targets**: Status dos endpoints sendo monitorados
- **Graph**: Visualização de métricas com queries PromQL
- **Alerts**: Configuração e visualização de alertas
- **Status**: Informações sobre configuração e armazenamento

### Exemplos de Queries PromQL
```promql
# Taxa de requisições por segundo
rate(requests_total[5m])

# Tempo de resposta percentil 95
histogram_quantile(0.95, rate(response_time_seconds_bucket[5m]))

# Total de requisições por método HTTP
sum by (method) (requests_total)

# Uso de CPU do OpenTelemetry Collector
rate(otelcol_processor_batch_batch_send_size_sum[5m])
```

## 🔧 Configuração

### OpenTelemetry Collector

O collector está configurado para:
- **Receber dados via OTLP gRPC**: porta 4317 (traces e métricas)
- **Exportar traces para Jaeger**: via OTLP para jaeger:4317
- **Exportar métricas para Prometheus**: porta 8889

### Jaeger All-in-One

Configurado com:
- **Storage**: Memória (dados perdidos ao reiniciar)
- **UI**: Interface web na porta 16686
- **OTLP**: Recebe traces na porta 4317

### Prometheus

Configurado com:
- **Storage**: Volume persistente (dados mantidos entre reinicializações)
- **Retention**: 7 dias
- **UI**: Interface web na porta 9090
- **Scraping**: OpenTelemetry Collector (porta 8889) e auto-monitoramento

## 🐛 Troubleshooting

### Verificar Logs dos Serviços

```bash
# Ver logs de todos os serviços
docker-compose logs

# Ver logs de um serviço específico
docker-compose logs otel-collector
docker-compose logs jaeger
docker-compose logs prometheus
```

### Verificar Status dos Serviços

```bash
# Status dos containers
docker-compose ps

# Health checks
docker-compose ps --format "table {{.Name}}\t{{.Status}}"
```

### Problemas Comuns

1. **Porta já em uso**:
   ```bash
   # Verificar portas em uso
   netstat -tulpn | grep :16686
   netstat -tulpn | grep :4317
   netstat -tulpn | grep :9090
   
   # Parar serviço conflitante ou alterar porta no docker-compose.yml
   ```

2. **Jaeger não recebe traces**:
   ```bash
   # Verificar se o collector está enviando dados
   docker-compose logs otel-collector
   
   # Verificar se o Jaeger está recebendo
   docker-compose logs jaeger
   ```

3. **Prometheus não coleta métricas**:
   ```bash
   # Verificar se o collector está exportando métricas
   curl http://localhost:8889/metrics
   
   # Verificar logs do Prometheus
   docker-compose logs prometheus
   ```

4. **Falta de memória**:
   ```bash
   # Verificar uso de memória
   docker stats
   
   # Ajustar limites no docker-compose.yml se necessário
   ```

5. **Traces não aparecem na UI**:
   - Verificar se os dados estão sendo enviados corretamente
   - Verificar logs: `docker-compose logs jaeger`
   - Reiniciar serviços: `docker-compose restart`

### Resetar Tudo

```bash
# Parar e remover tudo
docker-compose down -v

# Remover imagens (opcional)
docker-compose down --rmi all

# Iniciar novamente
docker-compose up -d
```

## 📁 Estrutura de Arquivos

```
Telemetry/
├── docker-compose.yml              # Orquestração dos serviços
├── config/
│   ├── otel-collector.yaml         # Configuração do OpenTelemetry Collector
│   └── prometheus.yml              # Configuração do Prometheus
└── README.md                       # Este arquivo
```

## 🔗 Links Úteis

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [OTLP Protocol](https://opentelemetry.io/docs/specs/otlp/)

## 📝 Notas

- Esta stack é ideal para desenvolvimento e testes
- Para produção, considere usar storage persistente (Elasticsearch/Cassandra) para o Jaeger
- Traces são armazenados em memória e são perdidos ao reiniciar os containers
- Métricas são armazenadas persistentemente no Prometheus (7 dias de retenção)
- Use SDKs OpenTelemetry para integração com suas aplicações

## 🤝 Contribuição

Sinta-se à vontade para sugerir melhorias ou reportar problemas!

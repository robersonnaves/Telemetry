# Stack de Telemetria com OpenTelemetry

Uma stack simplificada de observabilidade usando Docker Compose com OpenTelemetry Collector e Jaeger All-in-One.

## 🏗️ Arquitetura

```
Applications → OpenTelemetry Collector → Jaeger All-in-One
                    (OTLP)                    (Traces + UI)
```

### Por que dois serviços?

- **OpenTelemetry Collector**: Coletor universal que recebe dados via OTLP de diferentes aplicações e protocolos
- **Jaeger All-in-One**: Sistema completo de tracing distribuído com interface web para visualização

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
| **OTLP gRPC** | localhost:4317 | Endpoint para envio de traces via OTLP gRPC |

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

// Criar um ActivitySource
using var activitySource = new ActivitySource("MyApplication");

// Criar uma trace
using var activity = activitySource.StartActivity("test-operation");
activity?.SetTag("service.name", "test-service");
activity?.SetTag("operation", "test");
activity?.SetTag("http.method", "GET");
activity?.SetTag("http.url", "http://localhost:5000/api/test");

// Simular trabalho
await Task.Delay(100);

Console.WriteLine($"Trace ID: {activity?.TraceId}");
Console.WriteLine($"Span ID: {activity?.SpanId}");
```

##### Dependências NuGet para C#
```xml
<!-- Exemplo de PackageReference no .csproj -->
<PackageReference Include="OpenTelemetry" Version="1.7.0" />
<PackageReference Include="OpenTelemetry.Exporter.OpenTelemetryProtocol" Version="1.7.0" />
<PackageReference Include="OpenTelemetry.Extensions.Hosting" Version="1.7.0" />
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

## 🔧 Configuração

### OpenTelemetry Collector

O collector está configurado para:
- **Receber dados via OTLP gRPC**: porta 4317
- **Exportar traces para Jaeger**: via OTLP para jaeger:4317

### Jaeger All-in-One

Configurado com:
- **Storage**: Memória (dados perdidos ao reiniciar)
- **UI**: Interface web na porta 16686
- **OTLP**: Recebe traces na porta 4317

## 🐛 Troubleshooting

### Verificar Logs dos Serviços

```bash
# Ver logs de todos os serviços
docker-compose logs

# Ver logs de um serviço específico
docker-compose logs otel-collector
docker-compose logs jaeger
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
   
   # Parar serviço conflitante ou alterar porta no docker-compose.yml
   ```

2. **Jaeger não recebe traces**:
   ```bash
   # Verificar se o collector está enviando dados
   docker-compose logs otel-collector
   
   # Verificar se o Jaeger está recebendo
   docker-compose logs jaeger
   ```

3. **Falta de memória**:
   ```bash
   # Verificar uso de memória
   docker stats
   
   # Ajustar limites no docker-compose.yml se necessário
   ```

4. **Traces não aparecem na UI**:
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
│   └── otel-collector.yaml         # Configuração do OpenTelemetry Collector
└── README.md                       # Este arquivo
```

## 🔗 Links Úteis

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [OTLP Protocol](https://opentelemetry.io/docs/specs/otlp/)

## 📝 Notas

- Esta stack é ideal para desenvolvimento e testes
- Para produção, considere usar storage persistente (Elasticsearch/Cassandra) para o Jaeger
- Os dados são armazenados em memória e são perdidos ao reiniciar os containers
- Use SDKs OpenTelemetry para integração com suas aplicações

## 🤝 Contribuição

Sinta-se à vontade para sugerir melhorias ou reportar problemas!

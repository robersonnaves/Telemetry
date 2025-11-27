# Mock Telemetry Generator

Script Python para gerar dados mockados de observabilidade (traces, métricas, logs) e enviá-los para a stack de telemetria.

## Instalação

```powershell
# Criar ambiente virtual (opcional mas recomendado)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt
```

## Uso Básico

```powershell
# Gerar telemetria por 5 minutos (padrão)
python .\scripts\generate_mock_telemetry.py

# Gerar por 10 minutos com intervalo de 3 segundos
python .\scripts\generate_mock_telemetry.py --duration 600 --interval 3

# Gerar apenas traces (sem métricas e logs)
python .\scripts\generate_mock_telemetry.py --no-metrics --no-logs

# Customizar quantidade por batch
python .\scripts\generate_mock_telemetry.py --traces 10 --logs 20
```

## Opções de Linha de Comando

| Opção | Descrição | Padrão |
|-------|-----------|--------|
| `--duration` | Duração total em segundos | 300 |
| `--interval` | Intervalo entre batches em segundos | 5 |
| `--service` | Nome do serviço | mock-telemetry-generator |
| `--traces` | Número de traces por batch | 5 |
| `--logs` | Número de logs por batch | 10 |
| `--no-traces` | Desabilitar geração de traces | - |
| `--no-metrics` | Desabilitar geração de métricas | - |
| `--no-logs` | Desabilitar geração de logs | - |

## Dados Gerados

### Traces (via OTLP gRPC → OpenTelemetry Collector → Jaeger/Tempo)
- Operações HTTP mockadas (GET/POST/PUT/DELETE)
- Spans de banco de dados (queries simuladas)
- Atributos: método HTTP, URL, status code, user ID, IP do cliente
- 10% de traces com erro simulado

### Métricas (via OTLP gRPC → OpenTelemetry Collector → Prometheus → Telegraf → QuestDB)
- `http_requests_total` (counter): Total de requisições HTTP
- `http_errors_total` (counter): Total de erros HTTP
- `http_request_duration_seconds` (histogram): Latência de requisições
- `active_connections` (gauge): Conexões ativas simuladas

### Logs (via HTTP POST → Loki)
- Níveis: DEBUG, INFO, WARN, ERROR
- Serviços simulados: api-gateway, user-service, order-service, payment-service
- Mensagens contextuais aleatórias

## Endpoints Utilizados

- **OpenTelemetry Collector (OTLP gRPC)**: `http://localhost:4317`
- **Loki (Push API)**: `http://localhost:3100/loki/api/v1/push`

## Validação

Após executar o script, valide a ingestão:

1. **Traces**: Acesse Jaeger em `http://localhost:16686`
2. **Métricas**: Prometheus em `http://localhost:9090` (query: `http_requests_total`)
3. **Logs**: Grafana → Explore → Loki
4. **QuestDB**: Console web em `http://localhost:9001` → `SELECT * FROM tables();`

## Exemplo de Saída

```
🚀 Mock Telemetry Generator
   Service: mock-telemetry-generator
   Duration: 300s | Interval: 5s
   OTLP Endpoint: http://localhost:4317
   Loki Endpoint: http://localhost:3100/loki/api/v1/push
   Traces: ✓ | Metrics: ✓ | Logs: ✓

[14:23:10] Batch #1 | Traces ✓ | Metrics ✓ | Logs ✓ | 0.45s
[14:23:15] Batch #2 | Traces ✓ | Metrics ✓ | Logs ✓ | 0.38s
[14:23:20] Batch #3 | Traces ✓ | Metrics ✓ | Logs ✓ | 0.42s
...
```

## Troubleshooting

### Erro: "Failed to connect to OTLP endpoint"
- Verifique se o OpenTelemetry Collector está rodando: `docker ps | findstr otel-collector`
- Teste conectividade: `curl http://localhost:4317` (deve retornar erro gRPC, mas confirma porta aberta)

### Erro: "Failed to send logs to Loki"
- Verifique se Loki está rodando: `docker ps | findstr loki`
- Confirme porta 3100: `docker logs telemetry-loki --tail 50`

### Métricas não aparecem no Prometheus
- Aguarde até 30s (scrape_interval + processamento OTEL)
- Verifique targets do Prometheus: `http://localhost:9090/targets`

### Dados não chegam no QuestDB
- Confirme que Telegraf está rodando: `docker logs telemetry-telegraf --tail 100`
- Verifique conexão Telegraf → QuestDB na porta 9009
- Use dashboard Grafana "QuestDB Ingestion Check" para diagnóstico

## Cenários de Teste

### Carga contínua leve (monitoramento 24h)
```powershell
python .\scripts\generate_mock_telemetry.py --duration 86400 --interval 10 --traces 3 --logs 5
```

### Burst de alta carga (teste de estresse)
```powershell
python .\scripts\generate_mock_telemetry.py --duration 60 --interval 1 --traces 50 --logs 100
```

### Apenas traces para Jaeger/Tempo
```powershell
python .\scripts\generate_mock_telemetry.py --no-metrics --no-logs --traces 20
```

## Integração com CI/CD

Para testes automatizados em pipelines:

```yaml
# GitHub Actions exemplo
- name: Generate test telemetry
  run: |
    pip install -r requirements.txt
    python scripts/generate_mock_telemetry.py --duration 30 --interval 2
```

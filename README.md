# Stack de Telemetria com OpenTelemetry

Uma stack completa de observabilidade usando Docker Compose com OpenTelemetry Collector, Jaeger, Grafana Loki, Prometheus, cAdvisor e Grafana.

## 🏗️ Arquitetura

```
Applications → OpenTelemetry Collector → {
  - Jaeger (traces)
  - Loki (logs)  
  - Prometheus (metrics)
}
                                         ↓
                                     Grafana (dashboards)
                                         
Containers → cAdvisor → Prometheus → Grafana
```

## 📋 Pré-requisitos

- Docker e Docker Compose instalados
- Podman com socket Docker compatível em `/var/run/docker.sock`
- Pelo menos 4GB de RAM disponível
- Pelo menos 10GB de espaço em disco

## 🚀 Como Usar

### 1. Iniciar a Stack

```bash
# Clone ou baixe este repositório
cd /mnt/d/dev/Telemetry

# Iniciar todos os serviços
docker-compose up -d

# Verificar status dos serviços
docker-compose ps
```

### 2. Acessar os Serviços

| Serviço | URL | Descrição |
|---------|-----|-----------|
| **Grafana** | http://localhost:3000 | Dashboards e visualização (admin/admin) |
| **Prometheus** | http://localhost:9090 | Métricas e alertas |
| **Jaeger UI** | http://localhost:16686 | Traces distribuídos |
| **Loki** | http://localhost:3100 | Logs (API) |
| **cAdvisor** | http://localhost:8080 | Métricas de containers |

### 3. Enviar Dados de Teste

#### Enviar Traces via OTLP

```bash
# Exemplo usando curl para enviar trace
curl -X POST http://localhost:4318/v1/traces \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

#### Enviar Logs via OTLP

```bash
# Exemplo usando curl para enviar logs
curl -X POST http://localhost:4318/v1/logs \
  -H "Content-Type: application/json" \
  -d '{
    "resourceLogs": [{
      "resource": {
        "attributes": [{
          "key": "service.name",
          "value": {"stringValue": "test-service"}
        }]
      },
      "scopeLogs": [{
        "logRecords": [{
          "timeUnixNano": "1640995200000000000",
          "severityNumber": 9,
          "severityText": "INFO",
          "body": {"stringValue": "Test log message"}
        }]
      }]
    }]
  }'
```

### 4. Parar a Stack

```bash
# Parar todos os serviços
docker-compose down

# Parar e remover volumes (CUIDADO: apaga todos os dados)
docker-compose down -v
```

## 📊 Dashboards Disponíveis

### cAdvisor Dashboard
- **CPU Usage por Container**: Uso de CPU em percentual
- **Memory Usage por Container**: Uso de memória em bytes
- **Network I/O por Container**: Tráfego de rede (RX/TX)
- **Disk I/O por Container**: Operações de disco (leitura/escrita)
- **Total de Containers**: Contador de containers ativos
- **CPU Cores Disponíveis**: Número de cores do sistema
- **Memória Total do Sistema**: Memória total disponível
- **CPU Usage Total (%)**: Uso total de CPU do sistema

## 🔧 Configuração

### OpenTelemetry Collector

O collector está configurado para receber dados via:
- **OTLP gRPC**: porta 4317
- **OTLP HTTP**: porta 4318
- **Jaeger gRPC**: porta 14250
- **Jaeger HTTP**: porta 14268

E exportar para:
- **Jaeger**: traces
- **Loki**: logs
- **Prometheus**: métricas

### Prometheus

Configurado para fazer scraping de:
- OpenTelemetry Collector (porta 8888)
- cAdvisor (porta 8080)
- Próprio Prometheus (porta 9090)
- Jaeger components
- Loki
- Grafana

### Loki

- **Retention**: 7 dias (168h)
- **Storage**: filesystem local
- **Schema**: v11 com TSDB

## 🐛 Troubleshooting

### Verificar Logs dos Serviços

```bash
# Ver logs de todos os serviços
docker-compose logs

# Ver logs de um serviço específico
docker-compose logs grafana
docker-compose logs prometheus
docker-compose logs otel-collector
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
   netstat -tulpn | grep :3000
   
   # Parar serviço conflitante ou alterar porta no docker-compose.yml
   ```

2. **cAdvisor não consegue acessar Docker socket**:
   ```bash
   # Verificar permissões do socket
   ls -la /var/run/docker.sock
   
   # Ajustar permissões se necessário
   sudo chmod 666 /var/run/docker.sock
   ```

3. **Falta de memória**:
   ```bash
   # Verificar uso de memória
   docker stats
   
   # Ajustar limites no docker-compose.yml se necessário
   ```

4. **Grafana não carrega dashboards**:
   - Verificar se os arquivos de provisioning estão corretos
   - Verificar logs: `docker-compose logs grafana`
   - Reiniciar Grafana: `docker-compose restart grafana`

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
/mnt/d/dev/Telemetry/
├── docker-compose.yml              # Orquestração dos serviços
├── otel-collector/
│   └── config.yaml                 # Configuração do OpenTelemetry Collector
├── prometheus/
│   └── prometheus.yml              # Configuração do Prometheus
├── loki/
│   └── loki-config.yml             # Configuração do Loki
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── datasources.yml     # Datasources do Grafana
│   │   └── dashboards/
│   │       ├── dashboards.yml      # Configuração de dashboards
│   │       └── cadvisor-dashboard.json # Dashboard do cAdvisor
└── README.md                       # Este arquivo
```

## 🔗 Links Úteis

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Loki Documentation](https://grafana.com/docs/loki/)
- [cAdvisor Documentation](https://github.com/google/cadvisor)

## 📝 Notas

- Esta stack é ideal para desenvolvimento e testes
- Para produção, considere usar volumes persistentes e configurações de segurança
- O cAdvisor monitora containers via Docker socket, incluindo Podman com compatibilidade Docker
- Todos os dados são armazenados localmente nos volumes do Docker

## 🤝 Contribuição

Sinta-se à vontade para sugerir melhorias ou reportar problemas!

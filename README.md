# CscTrackerPyCore

[![PyPI version](https://img.shields.io/pypi/v/csctracker-py-core.svg)](https://pypi.org/project/csctracker-py-core/)
[![Python versions](https://img.shields.io/pypi/pyversions/csctracker-py-core.svg)](https://pypi.org/project/csctracker-py-core/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

CscTrackerPyCore é uma biblioteca Python base desenvolvida para padronizar e acelerar o desenvolvimento de microserviços. Ela oferece integração nativa com Flask, fornecendo recursos essenciais como logging estruturado em JSON, telemetria com Prometheus, documentação automática via Swagger e gerenciamento de tarefas agendadas.

## Principais Funcionalidades

- **Starter Facilitado**: Inicialização rápida de aplicações Flask com suporte a CORS e tratamento de variáveis de ambiente.
- **Logging Estruturado**: Formatação automática de logs em JSON com inclusão de `requestId`, `appName` e `appVersion` para melhor rastreabilidade.
- **Observabilidade**:
    - Integração nativa com **Prometheus** para coleta de métricas de endpoints.
    - **Interceptor de Requisições**: Registro detalhado de chamadas HTTP (método, path, status, duração) com opção de persistência remota para auditoria.
- **Documentação Automática**: Geração de especificação **Swagger (OpenAPI)** simplificada.
- **Processamento em Background**: Integração com `csctracker-queue-scheduler` para execução de tarefas assíncronas e agendadas.
- **Repositórios Remotos**: Abstração para comunicação entre serviços via HTTP com tratamento de headers e correlação.

## Requisitos

- Python 3.9+
- Flask
- Flask-CORS
- Prometheus Flask Exporter
- Flask Swagger Generator
- Python JSON Logger
- Python Dotenv

## Instalação

As dependências podem ser instaladas via `pip`:

```bash
pip install csctracker-py-core
```

Ou via `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Configuração

A biblioteca é configurada principalmente via variáveis de ambiente, suportando arquivos `.env` localizados na pasta `config/` (ex: `config/dev.env`).

### Variáveis de Ambiente Suportadas

| Variável | Descrição | Exemplo |
| :--- | :--- | :--- |
| `PROFILE` | Perfil de configuração (define o arquivo .env) | `dev` |
| `PORT` | Porta de execução do servidor Flask | `5000` |
| `LOG_LEVEL` | Nível de detalhamento do log | `INFO`, `DEBUG` |
| `LOG_REQUEST_BODY` | Se `True`, inclui o corpo da requisição nos logs | `True` |
| `LOG_RESPONSE_BODY` | Se `True`, inclui o corpo da resposta nos logs | `False` |
| `URL_BFF` | URL base para persistência de logs de requisição | `http://api-gateway/` |
| `API_TOKEN` | Token de autorização para chamadas externas | `seu_token_aqui` |
| `DEBUG` | Ativa o modo debug do Flask se definido como `1` | `0` |

## Uso Didático

### 1. Inicialização do `Starter`

A classe `Starter` centraliza a configuração do Flask.

```python
from csctracker_py_core.starter import Starter

# Inicializa o starter (static_folder define a pasta de arquivos estáticos)
# save_request=True ativa a persistência remota de logs de requisição
starter = Starter(save_request=False)

# Obtém a instância do Flask configurada
app = starter.get_app()

@app.route('/')
def hello():
    return {"message": "CscTrackerPyCore is running!"}

if __name__ == '__main__':
    starter.start()
```

### 2. Logging e Interceptação

Uma vez iniciado o `Starter`, todos os logs do sistema usarão o formato JSON e as requisições serão interceptadas automaticamente para gerar telemetria.

### 3. Acesso aos Repositórios

```python
# Acesso ao repositório HTTP para chamadas externas padronizadas
http_repo = starter.get_http_repository()
```

## Estrutura do Projeto

- `Starter`: Orquestrador principal que configura Flask, CORS, Métricas e Swagger.
- `Configs`: Gerencia o carregamento de variáveis de ambiente e a configuração do logger JSON.
- `Interceptor`: Middleware Flask que captura dados de performance e logs de entrada/saída.
- `HttpRepository`: Facilita requisições HTTP externas com injeção de headers de segurança e rastreio.
- `RequestInfo`: Utilitário para gerenciar IDs de correlação (Correlation IDs) entre threads.

## Licença

Este projeto está sob a licença MIT. Consulte o arquivo `LICENSE` para mais detalhes.
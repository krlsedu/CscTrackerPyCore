---
project: CscTrackerPyCore
kind: changelog
tier: episodic
updated_at: 2026-11-26
---

# 📜 Changelog de Sessões — `CscTrackerPyCore`

## 2026-11-26 — Task #121: Pool HTTP (`requests.Session`) e Timeout `600s` no `RemoteRepository`
- Configurada `requests.Session()` persistente com `HTTPAdapter` (`pool_connections=10`, `pool_maxsize=32`) e `timeout=600` padrão em todos os métodos do `RemoteRepository`, com override via `REMOTE_REPOSITORY_TIMEOUT` (e parse seguro para strings vazias/inválidas).
- Registrado `self.remote_repository.close` como hook no `GracefulShutdown` via `Starter.__init__()`.
- Adicionados testes unitários offline em `tests/test_remote_repository.py` (`28/28` passando na suíte completa em Python `3.15.2`).

## 2026-11-24 — Refinamento Final da Task #108 (Pronta para Implementação — Parte 1)
- Fechada arquitetura da Parte 1 no `CscTrackerPyCore` (absorvendo a Task #107): inclusão de `paho-mqtt>=2.0,<3`, semântica `seen_fingerprints` (desconhecido/`CRITICAL` imediato com cooldown vs. conhecido `>= 3` em `5 min`), header `Authorization: Bearer <TOKEN_CSCTRACKER|API_TOKEN>` na chamada ao `CscTrackerIA` (compatível com Task #109) e encerramento limpo do client MQTT via `GracefulShutdown`.

## 2026-11-24 — Task #109: Resolução de E-mail via Token Bearer em `RequestInfo`
- Adicionado `RequestInfo.get_user_email()` em `csctracker_py_core/utils/request_info.py` com consulta a `/oauth/check_token` e cache thread-safe em RAM por SHA-256 (TTL 5 min).
- Adicionados testes unitários offline em `tests/test_request_info.py` (`6/6` OK).

## 2026-11-21 — ID 94: Python 3.15, Atualização de Dependências e Drain Seguro do Waitress
- Atualizadas dependências para Python `>=3.11` / `3.15` (`csctracker-queue-scheduler>=26.47.1`, `flask-swagger-init>=26.47.2`, `flask>=3.1,<4`, `python-json-logger>=3.0,<5`, `flask-cors>=6.0,<7`, `prometheus-flask-exporter>=0.23.2,<1`, `beautifulsoup4>=4.12,<5`, `pytz>=2026.1`), `setup.cfg`, `MANIFEST.in` e `.github/workflows/build.yml`.
- Migrado `configs.py` para `pythonjsonlogger.json.JsonFormatter` e `http_repository.py` para `find_all(string=...)`.
- Implementado drain seguro em duas fases para o Waitress (`wasyncore.dispatcher.close(server)` no início + `503` keep-alive com `g._counted_request` no `Interceptor` + `task_dispatcher.shutdown`/`total_outbufs_len`/`trigger.close()` no pós-drain) e adicionados testes de regressão em `tests/test_starter_wsgi.py`.

## 2026-11-21 — ID 90: Waitress WSGI nativo no `Starter.start()` + Provisionamento de Governança
- Refinada e implementada a **ID 90**: `Starter.start()` agora sobe **Waitress** por padrão (`WSGI_THREADS=32`, `WSGI_CHANNEL_TIMEOUT=600`, `PORT=5000`) e usa Werkzeug somente quando `DEBUG=1`.
- Integrado `server.close` do Waitress ao `GracefulShutdown` (`set_server_close_hook`) e adicionada idempotência ao `SwaggerView.init(...)`.
- Adicionados testes unitários offline em `tests/test_starter_wsgi.py` e provisionados `.agents/`, `.ai-memory/`, `.junie/guidelines.md` e `.github/workflows/notify-cicd.yml`.

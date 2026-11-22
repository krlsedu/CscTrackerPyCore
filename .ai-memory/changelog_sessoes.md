---
project: CscTrackerPyCore
kind: changelog
tier: episodic
updated_at: 2026-11-21
---

# 📜 Changelog de Sessões — `CscTrackerPyCore`

## 2026-11-21 — ID 94: Python 3.15, Atualização de Dependências e Drain Seguro do Waitress
- Atualizadas dependências para Python `>=3.11` / `3.15` (`csctracker-queue-scheduler>=26.47.1`, `flask-swagger-init>=26.47.2`, `flask>=3.1,<4`, `python-json-logger>=3.0,<5`, `flask-cors>=6.0,<7`, `prometheus-flask-exporter>=0.23.2,<1`, `beautifulsoup4>=4.12,<5`, `pytz>=2026.1`), `setup.cfg`, `MANIFEST.in` e `.github/workflows/build.yml`.
- Migrado `configs.py` para `pythonjsonlogger.json.JsonFormatter` e `http_repository.py` para `find_all(string=...)`.
- Implementado drain seguro em duas fases para o Waitress (`wasyncore.dispatcher.close(server)` no início + `503` keep-alive com `g._counted_request` no `Interceptor` + `task_dispatcher.shutdown`/`total_outbufs_len`/`trigger.close()` no pós-drain) e adicionados testes de regressão em `tests/test_starter_wsgi.py`.

## 2026-11-21 — ID 90: Waitress WSGI nativo no `Starter.start()` + Provisionamento de Governança
- Refinada e implementada a **ID 90**: `Starter.start()` agora sobe **Waitress** por padrão (`WSGI_THREADS=32`, `WSGI_CHANNEL_TIMEOUT=600`, `PORT=5000`) e usa Werkzeug somente quando `DEBUG=1`.
- Integrado `server.close` do Waitress ao `GracefulShutdown` (`set_server_close_hook`) e adicionada idempotência ao `SwaggerView.init(...)`.
- Adicionados testes unitários offline em `tests/test_starter_wsgi.py` e provisionados `.agents/`, `.ai-memory/`, `.junie/guidelines.md` e `.github/workflows/notify-cicd.yml`.

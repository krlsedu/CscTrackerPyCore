---
project: CscTrackerPyCore
kind: changelog
tier: episodic
updated_at: 2026-11-21
---

# 📜 Changelog de Sessões — `CscTrackerPyCore`

## 2026-11-21 — ID 90: Waitress WSGI nativo no `Starter.start()` + Provisionamento de Governança
- Refinada e implementada a **ID 90**: `Starter.start()` agora sobe **Waitress** por padrão (`WSGI_THREADS=32`, `WSGI_CHANNEL_TIMEOUT=600`, `PORT=5000`) e usa Werkzeug somente quando `DEBUG=1`.
- Integrado `server.close` do Waitress ao `GracefulShutdown` (`set_server_close_hook`) e adicionada idempotência ao `SwaggerView.init(...)`.
- Adicionados testes unitários offline em `tests/test_starter_wsgi.py` e provisionados `.agents/`, `.ai-memory/`, `.junie/guidelines.md` e `.github/workflows/notify-cicd.yml`.

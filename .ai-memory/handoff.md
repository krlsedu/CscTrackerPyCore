---
project: CscTrackerPyCore
kind: handoff
tier: working
updated_at: 2026-11-24
---

# 🤝 Handoff Ativo — `CscTrackerPyCore`

> **Escopo do Projeto:** Biblioteca Python base (`csctracker-py-core` no PyPI) compartilhada pelos microsserviços Flask do ecossistema (Starter, Waitress WSGI, GracefulShutdown, Interceptor, Logging JSON, Prometheus, Swagger e HttpRepository).

## 1. Onde Paramos / Contexto Atual (`WIP`)
- **[2026-11-24] Implementação da Task #109 (`Por Publicar` — 6/6 testes novos OK em `tests/test_request_info.py`):**
  - Adicionado `RequestInfo.get_user_email(auth_url=None, cache_ttl_seconds=300)` e `clear_user_email_cache()` em `csctracker_py_core/utils/request_info.py`, extraindo o token `Bearer` de `Authorization`, consultando `POST {AUTH_URL}/oauth/check_token` (`AUTH_CLIENT_ID`/`AUTH_CLIENT_SECRET`, padrão `OAUTH`/`OAUTH`, `timeout=5`) e cacheando em RAM por SHA-256 (TTL 300s, thread-safe, sem armazenar/logar token bruto).
- **[2026-11-21] Implementação da ID 94 (`v26.47.003` / `26.47.3`, `Em Homologação`):**
  - Atualizado `requirements.txt` com versões compatíveis com Python `3.15` (`csctracker-queue-scheduler>=26.47.1`, `flask-swagger-init>=26.47.2`, `flask>=3.1,<4`, `python-json-logger>=3.0,<5`, `python-dotenv>=1.0,<2`, `requests>=2.32,<3`, `beautifulsoup4>=4.12,<5`, `flask-cors>=6.0,<7`, `prometheus-flask-exporter>=0.23.2,<1`, `pytz>=2026.1`, `waitress>=3.0.0,<4`).
  - Atualizados `setup.py` (`python_requires=">=3.11"`, classifiers `3.11`–`3.15`), `setup.cfg` (`description_file = README.md`), `MANIFEST.in`, `.github/workflows/build.yml` (Python `3.15` + `unittest` + `python -m build`) e `README.md` (`Python 3.11+` / `python:3.15-slim`).
  - Corrigidos `configs.py` (`from pythonjsonlogger.json import JsonFormatter`) e `http_repository.py` (`soup.find_all(string=...)`).
  - Corrigido o drain seguro do Waitress (`starter.py`, `graceful_shutdown.py`, `interceptor.py`): `wasyncore.dispatcher.close(server)` no início, rejeição `503` + `Connection: close` no `Interceptor` com guarda `g._counted_request`, pós-drain com `task_dispatcher.shutdown(cancel_pending=False)` + flush de `total_outbufs_len` e fechamento final de canais e `server.trigger.close()`.
  - Expandida suíte offline em `tests/test_starter_wsgi.py` (incluindo regressão real com Waitress em porta efêmera `0`).

## 2. Tentativas Descartadas / O que Falhou (`Failed Approaches`)
- Na **ID 90**, registrar `server.close` diretamente no `GracefulShutdown` fechava `server.trigger` antes do término das requisições ativas, causando `OSError` no `pull_trigger()` do Waitress durante drain de respostas em voo. Substituído pelo fechamento em duas fases (`close_listener` + `finalize_server`).

## 3. Estado dos Arquivos / Branch / Build
- **Fonte Primária:** GitHub (`master`, com espelho `.zip` em `projects/repositorys/CscTrackerPyCore/`).
- **Testes e Build offline:** `python -B -m unittest discover -s tests -v` (`17/17` passando) e `python -m build` OK em Python `3.15.2`.

## 4. Próximos Passos / Pendências Abertas
- Publicar nova versão de `csctracker-py-core` (`v26.47.002` / `26.47.2`) no PyPI para desbloquear a **Etapa 3 (ID 97 — `CscTrackerAiCore`)** e a **Etapa 4 (ID 93 — `CscTrackerRepository`)**.

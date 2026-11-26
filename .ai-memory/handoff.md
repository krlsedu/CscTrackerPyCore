---
project: CscTrackerPyCore
kind: handoff
tier: working
updated_at: 2026-11-26
---

# 🤝 Handoff Ativo — `CscTrackerPyCore`

> **Escopo do Projeto:** Biblioteca Python base (`csctracker-py-core` no PyPI) compartilhada pelos microsserviços Flask do ecossistema (Starter, Waitress WSGI, GracefulShutdown, Interceptor, Logging JSON, Prometheus, Swagger e HttpRepository).

## 1. Onde Paramos / Contexto Atual (`WIP`)
- **[2026-11-26] Implementação da Task #125 (`Por Publicar` — `31/31` testes OK em Python `3.15.2`):**
  - Configurada compatibilidade no `Starter.start()` (`_configure_waitress_legacy_compat`, `_LegacyCompatibleHTTPRequestParser`, `_LegacyCompatibleHTTPChannel`) para ignorar `Content-Length > 0` em requisições `GET`/`HEAD` sem corpo enviadas por clientes legados (evitando bloqueio de `600s` no `FixedStreamReceiver` do Waitress).
  - Corrigido retorno de `RequestInfo.get_headers()` / `HttpRepository.get_headers()` (antes retornavam `request.headers` bruto em vez do dicionário filtrado `headers_`) e removidos cabeçalhos hop-by-hop (`content-length`, `host`, `transfer-encoding`, `connection`), além de `_sanitize_headers()` nos 6 métodos HTTP de `RemoteRepository`.
  - Adicionados testes offline de regressão em `tests/test_starter_wsgi.py`, `tests/test_request_info.py` e `tests/test_remote_repository.py` (`31/31` testes OK em Python `3.15.2`).
- **[2026-11-26] Implementação da Task #121 (`Em Homologação` — `v26.48.002` / `26.48.2`):**
  - Configurada `requests.Session()` única no `RemoteRepository` (`csctracker_py_core/repository/remote_repository.py`) com `HTTPAdapter(pool_connections=10, pool_maxsize=32)` configurável via `REMOTE_REPOSITORY_POOL_CONNECTIONS` / `REMOTE_REPOSITORY_POOL_MAXSIZE`.
  - Aplicado `timeout=600` (10 min) em todos os métodos (`insert`, `update`, `delete`, `get_object`, `get_objects`, `execute_select`) com override seguro via `REMOTE_REPOSITORY_TIMEOUT` (fallback para `600` em string vazia, inválida ou `<= 0`).
  - Adicionadas chaves em `csctracker_py_core/models/emuns/config.py`, método `RemoteRepository.close()` e registro automático do hook no `GracefulShutdown` em `Starter.__init__()`.
  - Adicionada suíte offline em `tests/test_remote_repository.py` e atualizado `tests/test_graceful_shutdown.py` (`28/28` testes passando).
- **[2026-11-24] Implementação da Task #109 (`Em Homologação` — `v26.48.001` / `26.48.1`):**
  - Adicionado `RequestInfo.get_user_email(auth_url=None, cache_ttl_seconds=300)` e `clear_user_email_cache()` em `csctracker_py_core/utils/request_info.py`.
- **[2026-11-21] Implementação da ID 94 (`v26.47.003` / `26.47.3`, `Em Homologação`):**
  - Suporte Python `>=3.11`/`3.15`, `python-json-logger` v4+, `MANIFEST.in`, `setup.cfg` e drain seguro em duas fases para o Waitress.

## 2. Tentativas Descartadas / O que Falhou (`Failed Approaches`)
- Na **ID 90**, registrar `server.close` diretamente no `GracefulShutdown` fechava `server.trigger` antes do término das requisições ativas, causando `OSError` no `pull_trigger()` do Waitress durante drain de respostas em voo. Substituído pelo fechamento em duas fases (`close_listener` + `finalize_server`).

## 3. Estado dos Arquivos / Branch / Build
- **Fonte Primária:** GitHub (`master`, com espelho `.zip` em `projects/repositorys/CscTrackerPyCore/`).
- **Testes offline:** `python -B -m unittest discover -s tests -v` (`31/31` passando em Python `3.15.2`).

## 4. Próximos Passos / Pendências Abertas
- Publicar nova release `v26.48.003` (`26.48.3`, Tasks #121 + #125) de `csctracker-py-core` no PyPI e atualizar `csctracker-py-core==26.48.3` no `CscTrackerRepository/requirements.txt` para destravar as Tasks #93, #120, #123 e #124.

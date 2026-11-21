---
project: CscTrackerPyCore
kind: handoff
tier: working
updated_at: 2026-11-21
---

# 🤝 Handoff Ativo — `CscTrackerPyCore`

> **Escopo do Projeto:** Biblioteca Python base (`csctracker-py-core` no PyPI) compartilhada pelos microsserviços Flask do ecossistema (Starter, Waitress WSGI, GracefulShutdown, Interceptor, Logging JSON, Prometheus, Swagger e HttpRepository).

## 1. Onde Paramos / Contexto Atual (`WIP`)
- **[2026-11-21] Implementação da ID 90 (`Por Publicar`, `13/13` testes offline OK):**
  - `Starter.start()` atualizado para subir **Waitress** por padrão (`PORT=5000`, `WSGI_THREADS=32`, `WSGI_CHANNEL_TIMEOUT=600`) mantendo via única de start, com fallback para Werkzeug apenas quando `DEBUG=1`.
  - `GracefulShutdown` atualizado com `set_server_close_hook(server.close)` para encerrar o listener HTTP logo no início do drain (`SIGTERM`/`SIGINT`).
  - `requirements.txt` atualizado com `waitress>=3.0.0`, `README.md` atualizado e suíte offline expandida em `tests/test_starter_wsgi.py`.
  - Provisionados `.agents/skills/csctracker/SKILL.md`, `.ai-memory/`, `.junie/guidelines.md` e `.github/workflows/notify-cicd.yml`.

## 2. Tentativas Descartadas / O que Falhou (`Failed Approaches`)
- Descartada a ideia inicial de `init_wsgi()` + Gunicorn em duas vias de start: substituída por **Waitress** embarcado no `Starter.start()` (via única, sem `fork()` e 100% compatível com `SchedulerService` e `GracefulShutdown`).

## 3. Estado dos Arquivos / Branch / Build
- **Fonte Primária:** GitHub (`master`, com espelho `.zip` em `projects/repositorys/CscTrackerPyCore/`).
- **Testes offline:** `venv\Scripts\python.exe -B -m unittest discover -s tests -v` (`13/13` passando).

## 4. Próximos Passos / Pendências Abertas
- Configurar secret `TOKEN_CSCTRACKER` (e opcionalmente `CICD_WEBHOOK_URL`) no GitHub Actions do repositório para o workflow `notify-cicd.yml`.
- Publicar nova versão da biblioteca `csctracker-py-core` no PyPI e homologar a **ID 90** nos microsserviços consumidores.

---
project: CscTrackerPyCore
kind: decisions
tier: semantic
pinned: true
updated_at: 2026-11-21
---

# 🏛️ Decisões Arquiteturais — `CscTrackerPyCore`

## Cláusulas Pétreas `[PINNED]`
- **Via Única de Inicialização (`Starter.start()`):** Todo microsserviço consumidor inicia exclusivamente via `starter.start()`, sem duplicar rotas de boot nem exigir alterações em `app.py`.
- **Produção WSGI com Waitress (Sem `fork()`):** Por padrão (`DEBUG != 1`), `starter.start()` sobe o servidor WSGI **Waitress** (`threads=WSGI_THREADS` default `32`, `channel_timeout=WSGI_CHANNEL_TIMEOUT` default `600`) no mesmo processo. É proibido introduzir `os.fork()` dentro de `Starter.start()`, pois `SchedulerService.init(10)` e threads de background dos serviços consumidores (ex.: `ClickHouseDb`) já estão ativos antes do `start()` e morreriam no processo filho.
- **Modo Dev Local via `DEBUG=1`:** Apenas quando `DEBUG=1` (`Configs.is_debug()`), `starter.start()` utiliza o servidor de desenvolvimento Werkzeug (`self.app.run(host="0.0.0.0", port=port)`). Não usar `PROFILE=dev` como chave de modo dev, pois composes de produção frequentemente omitem `PROFILE`.
- **Graceful Shutdown Integrado:** Ao iniciar o Waitress, `Starter.start()` registra `server.close` no `GracefulShutdown` (`set_server_close_hook`) para parar imediatamente de aceitar novas conexões no `SIGTERM`/`SIGINT` antes de aguardar `active_requests == 0` ➔ drenar `SchedulerService` ➔ executar `shutdown_hooks`.
- **Testes Locais Offline:** Executar via `venv\Scripts\python.exe -B -m unittest discover -s tests -v` (sem bater em rede ou portas reais).

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
- **Suporte Mínimo Python `>=3.11` (Validado até `3.15`) e `python-json-logger` v4+:** `setup.py` exige `python_requires=">=3.11"` (classifiers `3.11`–`3.15`), `configs.py` importa diretamente `from pythonjsonlogger.json import JsonFormatter`, e `http_repository.py` usa `soup.find_all(string=...)`.
- **Empacotamento PyPI (`MANIFEST.in` + `setup.cfg`):** Manter `MANIFEST.in` na raiz (`version.py`, `version.txt`, `requirements.txt`, `README.md`, `LICENSE`) e `description_file = README.md` no `setup.cfg` para compatibilidade com `python -m build` e `setuptools>=84`.
- **Produção WSGI com Waitress (Sem `fork()`):** Por padrão (`DEBUG != 1`), `starter.start()` sobe o servidor WSGI **Waitress** (`threads=WSGI_THREADS` default `32`, `channel_timeout=WSGI_CHANNEL_TIMEOUT` default `600`) no mesmo processo. É proibido introduzir `os.fork()` dentro de `Starter.start()`, pois `SchedulerService.init(10)` e threads de background dos serviços consumidores (ex.: `ClickHouseDb`) já estão ativos antes do `start()` e morreriam no processo filho.
- **Modo Dev Local via `DEBUG=1`:** Apenas quando `DEBUG=1` (`Configs.is_debug()`), `starter.start()` utiliza o servidor de desenvolvimento Werkzeug (`self.app.run(host="0.0.0.0", port=port)`). Não usar `PROFILE=dev` como chave de modo dev, pois composes de produção frequentemente omitem `PROFILE`.
- **Graceful Shutdown Seguro com Waitress:** No início do drain (`SIGTERM`/`SIGINT`), fechar **apenas** o socket listener (`wasyncore.dispatcher.close(server)`) mantendo `server.trigger` aberto; no `Interceptor.before_request`, rejeitar novas requisições em keep-alive com `503` + `Connection: close` usando guarda `g._counted_request`; após `active_requests == 0`, rodar `task_dispatcher.shutdown(cancel_pending=False)`, aguardar `total_outbufs_len == 0` nos canais de `server._map` e só então fechar canais ociosos e `server.trigger.close()`, antes de drenar `SchedulerService` e executar `shutdown_hooks`.
- **Testes Locais Offline:** Executar via `python -B -m unittest discover -s tests -v` (sem bater em APIs externas).

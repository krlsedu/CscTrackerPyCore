---
project: CscTrackerPyCore
kind: gotchas
tier: semantic
updated_at: 2026-11-21
---

# ⚠️ Armadilhas Conhecidas (`Gotchas`) — `CscTrackerPyCore`

- **`fork()` após `Starter.__init__()` mata threads de background:** `Starter.__init__()` inicia `SchedulerService.init(10)` (threads) antes de `starter.start()`. Usar Gunicorn programaticamente (`BaseApplication`) dentro de `starter.start()` faria `os.fork()` e mataria as threads do `SchedulerService` e de serviços consumidores (ex.: fila assíncrona do `ClickHouseDb`) no worker filho. Por isso adotamos **Waitress** (single-process multi-thread) no `starter.start()`.
- **`BaseWSGIServer.close()` fecha `server.trigger` cedo demais:** No `waitress`, chamar `server.close()` no início do drain fecha `self.trigger` imediatamente. Se houver requisição HTTP em andamento que termine após isso, `pull_trigger()` lança `OSError` sobre o `trigger` fechado antes do flush da resposta. Por isso usamos `wasyncore.dispatcher.close(server)` no início e `trigger.close()` somente no pós-drain após `task_dispatcher.shutdown(cancel_pending=False)` e `total_outbufs_len == 0`.
- **`python-json-logger` v4+ removeu `pythonjsonlogger.jsonlogger`:** Em Python `3.10+`/`3.15`, usar sempre `from pythonjsonlogger.json import JsonFormatter`.
- **`BeautifulSoup.find_all(text=...)` depreciado:** Usar sempre `string=` no `beautifulsoup4>=4.12`.
- **`PROFILE` tem default `"dev"` no `Starter`:** Composes de produção nem sempre definem `PROFILE=prod`, fazendo `os.getenv("PROFILE", "dev")` retornar `"dev"` em produção. Nunca usar `PROFILE == "dev"` para desligar recursos de produção — usar `DEBUG=1` (`Configs.is_debug()`).
- **ENVs numéricas vazias em Compose:** `Configs.get_env_variable` retorna `""` (string vazia) se a variável estiver definida vazia no ambiente. Sempre converter inteiros de configuração com fallback seguro (`Starter._get_int_env`).

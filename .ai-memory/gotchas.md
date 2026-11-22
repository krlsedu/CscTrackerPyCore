---
project: CscTrackerPyCore
kind: gotchas
tier: semantic
updated_at: 2026-11-22
---

# ⚠️ Armadilhas Conhecidas (`Gotchas`) — `CscTrackerPyCore`

- **`fork()` após `Starter.__init__()` mata threads de background:** `Starter.__init__()` inicia `SchedulerService.init(10)` (threads) antes de `starter.start()`. Usar Gunicorn programaticamente (`BaseApplication`) dentro de `starter.start()` faria `os.fork()` e mataria as threads do `SchedulerService` e de serviços consumidores (ex.: fila assíncrona do `ClickHouseDb`) no worker filho. Por isso adotamos **Waitress** (single-process multi-thread) no `starter.start()`.
- **`BaseWSGIServer.close()` fecha `server.trigger` cedo demais e `close()` fora da thread do `wasyncore` atrasa o fechamento no Linux:** No `waitress`, chamar `server.close()` no início do drain fecha `self.trigger` imediatamente, causando `OSError` em `pull_trigger()` de requisições in-flight. Além disso, no Linux (`ubuntu-latest`/Docker), chamar `wasyncore.dispatcher.close(server)` a partir de outra thread enquanto `server.run()` está bloqueado em `select.select(..., timeout=1)` mantém a referência `fget` do kernel sobre o socket em `LISTEN` até o timeout do `select`, aceitando novas conexões TCP por até 1s. Por isso, tanto o fechamento do listener (`sock.shutdown(SHUT_RDWR)` + `wasyncore.dispatcher.close(srv)`) quanto o fechamento pós-drain de canais e `trigger.close()` devem ser despachados na thread do `wasyncore` via `trigger.pull_trigger(thunk)` (`Starter._run_on_waitress_loop`).
- **`python-json-logger` v4+ removeu `pythonjsonlogger.jsonlogger`:** Em Python `3.10+`/`3.15`, usar sempre `from pythonjsonlogger.json import JsonFormatter`.
- **`BeautifulSoup.find_all(text=...)` depreciado:** Usar sempre `string=` no `beautifulsoup4>=4.12`.
- **`PROFILE` tem default `"dev"` no `Starter`:** Composes de produção nem sempre definem `PROFILE=prod`, fazendo `os.getenv("PROFILE", "dev")` retornar `"dev"` em produção. Nunca usar `PROFILE == "dev"` para desligar recursos de produção — usar `DEBUG=1` (`Configs.is_debug()`).
- **ENVs numéricas vazias em Compose:** `Configs.get_env_variable` retorna `""` (string vazia) se a variável estiver definida vazia no ambiente. Sempre converter inteiros de configuração com fallback seguro (`Starter._get_int_env`).

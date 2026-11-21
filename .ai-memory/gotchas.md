---
project: CscTrackerPyCore
kind: gotchas
tier: semantic
updated_at: 2026-11-21
---

# ⚠️ Armadilhas Conhecidas (`Gotchas`) — `CscTrackerPyCore`

- **`fork()` após `Starter.__init__()` mata threads de background:** `Starter.__init__()` inicia `SchedulerService.init(10)` (threads) antes de `starter.start()`. Usar Gunicorn programaticamente (`BaseApplication`) dentro de `starter.start()` faria `os.fork()` e mataria as threads do `SchedulerService` e de serviços consumidores (ex.: fila assíncrona do `ClickHouseDb`) no worker filho. Por isso adotamos **Waitress** (single-process multi-thread) no `starter.start()`.
- **`PROFILE` tem default `"dev"` no `Starter`:** Composes de produção nem sempre definem `PROFILE=prod`, fazendo `os.getenv("PROFILE", "dev")` retornar `"dev"` em produção. Nunca usar `PROFILE == "dev"` para desligar recursos de produção — usar `DEBUG=1` (`Configs.is_debug()`).
- **ENVs numéricas vazias em Compose:** `Configs.get_env_variable` retorna `""` (string vazia) se a variável estiver definida vazia no ambiente. Sempre converter inteiros de configuração com fallback seguro (`Starter._get_int_env`).

Release Notes - v26.47.003

Abaixo estão as notas de atualização para a versão v26.47.003. Esta versão tem como foco principal aprimorar a resiliência operacional da aplicação por meio da correção do mecanismo de desligamento gracioso (graceful shutdown) do servidor Waitress em ambientes Linux. As modificações garantem o tratamento adequado de sinais de encerramento do sistema operacional, prevenindo processos zumbis ou paradas forçadas durante o ciclo de vida dos containers e serviços.

## 🚀 Features
*(Nenhuma alteração desta categoria nesta versão)*

## 🐛 Fixes
* **Servidor WSGI / Ciclo de Vida:** Correção no gerenciamento do ciclo de vida e encerramento (shutdown) do servidor WSGI Waitress em plataformas Linux. A implementação aprimorou o tratamento de sinais do sistema operacional (como SIGTERM e SIGINT) e ajustou o fluxo de controle de threads/processos no inicializador da aplicação, resolvendo o comportamento de bloqueio ou encerramento inadequado em ambientes Unix-like. Com essa correção, os containers e serviços em produção passam a responder de forma previsível e limpa às ordens de encerramento dos orquestradores (como Docker e Kubernetes), evitando interrupções abruptas de requisições ativas e prevenindo travamentos no desligamento (`csctracker_py_core/starter.py`).
  * *Commit: `40495ad` | Autor: @krlsedu*

## 🔧 Chore
*(Nenhuma alteração desta categoria nesta versão)*
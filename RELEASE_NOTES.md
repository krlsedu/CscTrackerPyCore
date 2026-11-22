Release Notes - v26.47.002

Abaixo estão as notas de atualização para a versão v26.47.002. Esta versão introduz a preparação do ecossistema do core para compatibilidade com o Python 3.15, atualizando dependências-chave e matrizes de CI/CD. Além disso, implementa um mecanismo de drain seguro e graceful shutdown na inicialização da aplicação, garantindo o processamento completo de requisições em trânsito antes da finalização de serviços e aumentando a resiliência operacional.

## 🚀 Features
* **Inicialização e Resiliência (Starter / Graceful Shutdown):** Implementação de suporte preliminar ao runtime Python 3.15 e introdução de um fluxo de encerramento controlado (drain seguro) durante o ciclo de vida da aplicação WSGI. A mudança intercepta sinais de término do sistema operacional para suspender a aceitação de novas conexões HTTP e aguardar o escoamento de requisições ativas por um tempo limite parametrizado, evitando encerramentos abruptos e consequentes falhas de comunicação interna em ambiente de container. Adicionalmente, as suítes de testes foram expandidas e as dependências e rotinas de pipeline do GitHub Actions foram ajustadas para assegurar compatibilidade e cobertura sobre o novo fluxo de shutdown (`csctracker_py_core/starter.py`).
  * *Commit: `fb4cd23` | Autor: @krlsedu*

## 🐛 Fixes
*(Nenhuma alteração desta categoria nesta versão)*

## 🔧 Chore
*(Nenhuma alteração desta categoria nesta versão)*
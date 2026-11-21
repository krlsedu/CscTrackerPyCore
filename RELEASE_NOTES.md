Release Notes - v26.47.001

Abaixo estão as notas de atualização para a versão v26.47.001. Esta versão introduz o servidor WSGI de nível de produção Waitress ao Starter da biblioteca central, fornecendo uma alternativa robusta e compatível com múltiplos ambientes ao servidor de desenvolvimento padrão do Flask. A atualização também engloba mecanismos avançados de graceful shutdown, documentação técnica expandida e uma cobertura abrangente de testes unitários para a inicialização e encerramento do serviço.

## 🚀 Features
* **Starter / WSGI:** Implementação do servidor de aplicação WSGI Waitress no ciclo de inicialização do Starter, possibilitando a execução da aplicação Flask sobre um servidor de produção puro Python por meio de novas chaves de configuração (`csctracker_py_core/starter.py`). A alteração inclui o enriquecimento dos utilitários de graceful shutdown para interceptar sinais do sistema operacional e encerrar o Waitress de maneira controlada, mitigando a perda de requisições em voo, além de adicionar suite de testes dedicada, atualização das dependências e documentação arquitetural no repositório.
  * *Commit: `fdb68d1` | Autor: @krlsedu*

## 🐛 Fixes
*(Nenhuma alteração desta categoria nesta versão)*

## 🔧 Chore
*(Nenhuma alteração desta categoria nesta versão)*
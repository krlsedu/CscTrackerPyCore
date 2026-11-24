Release Notes - v26.48.001

Abaixo estão as notas de atualização para a versão v26.48.001. Esta versão introduz a função utilitária `get_user_email` no módulo de extração de informações de requisições (`request_info`), permitindo a recuperação consistente e padronizada do e-mail do usuário autenticado no contexto da aplicação. A implementação conta com cobertura abrangente de testes unitários automatizados para validar diferentes cenários de payload e cabeçalhos, além da devida documentação de sessão interna.

## 🚀 Features
* **Request Info (Core / Auth):** Implementação da função `get_user_email` para viabilizar a extração direta, padronizada e segura do endereço de e-mail do usuário a partir dos dados e metadados contextuais da requisição (`request_info.py`). Essa funcionalidade supre a necessidade de obter a identidade do solicitante de forma centralizada nos microsserviços e bibliotecas dependentes, garantindo conformidade com o fluxo de autenticação e facilitando trilhas de auditoria, enriquecimento de logs operacionais e regras de negócio baseadas no operador (`csctracker_py_core/utils/request_info.py`).
  * *Commit: `0366bfe` | Autor: @krlsedu*

## 🐛 Fixes
*(Nenhuma alteração desta categoria nesta versão)*

## 🔧 Chore
*(Nenhuma alteração desta categoria nesta versão)*
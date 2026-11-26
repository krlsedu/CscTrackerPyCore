Release Notes - v26.48.004

Abaixo estão as notas de atualização para a versão v26.48.004. Esta versão foca na padronização e robustez no consumo e manipulação de cabeçalhos HTTP dentro do ecossistema da aplicação. A principal entrega assegura o tratamento case-insensitive dos headers em requisições e respostas, prevenindo inconsistências e falhas de comunicação entre clientes e serviços remotos.

## 🚀 Features
* **HTTP & Request Info:** Implementação de suporte e tratamento nativo para cabeçalhos HTTP case-insensitive na camada de utilitários de requisição e repositórios remotos. A alteração visa mitigar problemas comuns onde a variação no padrão de capitalização dos headers (ex.: `Content-Type` vs `content-type`) causava falhas de leitura ou inconsistências em integrações externas e repositórios HTTP, garantindo conformidade com a especificação RFC e tornando o consumo de dados mais seguro e transparente para os módulos integradores (`csctracker_py_core/utils/request_info.py`).
  * *Commit: `0781790` | Autor: @krlsedu*

## 🐛 Fixes
*(Nenhuma alteração desta categoria nesta versão)*

## 🔧 Chore
*(Nenhuma alteração desta categoria nesta versão)*
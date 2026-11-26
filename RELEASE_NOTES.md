Release Notes - v26.48.003

Abaixo estão as notas de atualização para a versão v26.48.003. Esta versão tem como objetivo principal corrigir o tratamento e encaminhamento de requisições HTTP do tipo GET que continham o cabeçalho `Content-Length`, prevenindo falhas de integração e rejeições de protocolo em chamadas downstream e camadas WSGI. A entrega refatora os repositórios remotos, a extração de metadados das requisições e a inicialização da aplicação, acompanhada por uma robusta suíte de testes unitários que valida a sanitização dos cabeçalhos.

## 🚀 Features
*(Nenhuma alteração desta categoria nesta versão)*

## 🐛 Fixes
* **HTTP / WSGI Handling:** Correção do tratamento indevido do cabeçalho `Content-Length` em requisições HTTP GET, que causava anomalias no parse de payloads inexistentes e falhas de protocolo em clientes ou servidores downstream. A implementação higieniza os headers na camada de abstração de requisição (`request_info.py`), nos repositórios HTTP/remotos (`http_repository.py` e `remote_repository.py`) e na camada de inicialização WSGI (`starter.py`), garantindo que requisições GET sem corpo não propaguem comprimento de conteúdo inválido e evitando falhas de comunicação entre microsserviços (`csctracker_py_core/repository/remote_repository.py`).
  * *Commit: `25b1248` | Autor: @krlsedu*

## 🔧 Chore
*(Nenhuma alteração desta categoria nesta versão)*
Aqui estão as Notas de Lançamento para a versão **v26.09.001**, elaboradas com foco em clareza técnica e padronização.

---

# 📝 Release Notes - v26.09.001

## 🚀 Features
- **Centralização de Configurações de Ambiente:** Implementação de métodos estáticos no utilitário de configuração (`csctracker_py_core/utils/configs.py`) para a recuperação padronizada das URLs do **BFF** e do **Repositório**. 
    - As URLs agora são extraídas diretamente de variáveis de ambiente, facilitando a gestão de diferentes contextos (staging/production) e promovendo o desacoplamento do código.

## 🐛 Fixes
- Nenhuma correção de bug incluída nesta versão.

## 🔧 Chore
- Nenhuma alteração de infraestrutura, dependências ou manutenção interna.

---
**Tech Lead:** Carlos Eduardo Duarte Schwalm  
**Commit de Referência:** `b522c55`
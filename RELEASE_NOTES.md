Aqui estão as Notas de Lançamento para a versão **v26.09.003**, focadas em manutenção e saúde do código.

---

# 📝 Release Notes - v26.09.003

## 🔧 Chore
- **Refatoração e Limpeza Técnica (`csctracker_py_core`):**
    - Remoção de imports não utilizados no utilitário `request_info.py`, otimizando o tempo de carregamento do módulo.
    - Exclusão definitiva do método depreciado `get_api_token`. Esta ação visa reduzir o débito técnico e garantir que a biblioteca utilize apenas padrões atualizados de autenticação.
    - *Commit:* `d0544e0`

---
**Tech Lead Note:** Esta versão foca exclusivamente na estabilidade e limpeza do core da aplicação. Não há alterações de breaking changes para as funcionalidades atuais, uma vez que o método removido já estava marcado como depreciado.
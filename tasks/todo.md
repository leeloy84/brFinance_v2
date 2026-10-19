# Planejamento de Testes e Robustez - brFinance_v2

## [ ] Diagnóstico e Pesquisa
- [ ] Analisar `constants.py` para identificar todos os endpoints da CVM. <!-- id: 0 -->
- [ ] Analisar `http_client.py` para verificar tratamento de timeouts e retries. <!-- id: 1 -->
- [ ] Verificar `backend.py` para entender como a lista de empresas é buscada. <!-- id: 2 -->

## [ ] Melhorias de Robustez
- [ ] Implementar política de retries (backoff exponencial) no `http_client.py`. <!-- id: 3 -->
- [ ] Adicionar timeouts configuráveis. <!-- id: 4 -->
- [ ] Melhorar logs de erro para facilitar depuração. <!-- id: 5 -->

## [ ] Plano de Testes
- [ ] **Testes Unitários**: Mockar respostas da CVM para testar lógica de parsing e tratamento de erros. <!-- id: 6 -->
- [ ] **Testes de Integração**: Testar chamadas reais (com cautela para evitar bloqueios) ou usar VCR/recordings. <!-- id: 7 -->
- [ ] **Testes de Regressão**: Criar teste específico que simule timeout para garantir que o retry funciona. <!-- id: 8 -->

## [ ] Implementação de Testes
- [ ] Criar `tests/test_cvm_robustness.py`. <!-- id: 9 -->
- [ ] Expandir `tests/test_backend.py` com todas as requisições disponíveis. <!-- id: 10 -->
- [ ] Garantir que todos os testes passem. <!-- id: 11 -->

## [ ] Documentação e Finalização
- [ ] Atualizar `tasks/lessons.md` se necessário. <!-- id: 12 -->
- [ ] Entregar relatório de verificações (walkthrough.md). <!-- id: 13 -->

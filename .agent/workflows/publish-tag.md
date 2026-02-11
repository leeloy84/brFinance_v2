---
description: Como publicar uma nova versão da biblioteca brFinance_v2 usando tags do Git (Automático)
---

Este workflow descreve os passos necessários para lançar uma nova versão estável usando o sistema de versionamento automático por Tags.

### 1. Definição da Versão
A versão agora é **automática**. Você não precisa mais editar o `setup.py` ou o `__init__.py`. A versão do seu pacote será definida exatamente pelo nome da Tag que você criar no Git.

### 2. Sincronização e Commit
Certifique-se de que todas as alterações desejadas foram commitadas.
```powershell
git add .
git commit -m "Finalizando alterações para a versão 0.1.0"
git push origin master
```

### 3. Criação da Tag (Início da Versão 0.1.0)
Para garantir que a primeira versão seja a **0.1.0**, crie a tag exatamente com este nome:
```powershell
git tag -a v0.1.0 -m "Versão inicial 0.1.0"
```

### 4. Push da Tag e Publicação Automática
Ao enviar a tag, o GitHub Actions iniciará o processo de build. O `setuptools_scm` lerá a tag `v0.1.0` e gerará os arquivos `.tar.gz` e `.whl` com a versão correta automaticamente.
```powershell
git push origin --tags
```

### 5. Como o sistema funciona:
- O arquivo `setup.py` usa o `setuptools_scm` para detectar a tag mais recente.
- O arquivo `brfinance_v2/__init__.py` lê a versão em tempo de execução usando `importlib.metadata`.
- Se não houver tags ou o pacote não estiver instalado, ele assume `0.1.0` como fallback.

---
**Nota:** Para que a automação GitHub -> PyPI funcione, certifique-se de ter configurado o segredo `PYPI_API_TOKEN` no seu repositório GitHub.

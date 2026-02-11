[![Participantes][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Estrelas][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![Licença MIT][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]

# brFinance v2

**brFinance v2** é uma biblioteca Python projetada para facilitar o acesso e a extração de dados financeiros de empresas brasileiras listadas na B3 e reguladas pela CVM.

Com ela, você pode acessar facilmente:
*   **Demonstrativos Financeiros (ITR e DFP):**
    *   Balanço Patrimonial (Ativo e Passivo)
    *   Demonstração do Resultado (DRE)
    *   Demonstração do Resultado Abrangente (DRA)
    *   Demonstração do Fluxo de Caixa (DFC)
    *   Demonstração das Mutações do Patrimônio Líquido (DMPL)
    *   Demonstração de Valor Adicionado (DVA)
*   **Dados Cadastrais da CVM e B3**
*   **Informações sobre Emissores e Instrumentos Financeiros**

---

## 📦 Instalação

Você pode instalar a biblioteca diretamente do PyPI:

```bash
pip install brfinance_v2
```

## 🚀 Como Usar

Abaixo está um exemplo completo de como utilizar a biblioteca para buscar empresas, encontrar documentos e baixar relatórios financeiros.

### 1. Inicializando o Backend
A classe principal para interação é a `CVMBackend`.

```python
from brfinance_v2 import CVMBackend
from datetime import date
import pandas as pd

# Inicializa o cliente
cvm_client = CVMBackend()
```

### 2. Buscando Códigos CVM
Obtenha um dicionário com todas as empresas registradas e seus respectivos códigos CVM.

```python
# Retorna dict {codigo_cvm: nome_empresa}
cvm_codes = cvm_client.get_cvm_codes()

# Exemplo: Imprimir o código da PETROBRAS
print("Código da PETROBRAS:", {k: v for k, v in cvm_codes.items() if 'PETROBRAS' in v})
```

### 3. Buscando Documentos (ITR, DFP, etc.)
Você pode buscar por documentos específicos usando códigos CVM e intervalos de datas.

```python
# Parâmetros de busca
start_date = date(2023, 1, 1)
end_date = date.today()
cvm_codes_list = ['9512']  # Código CVM da PETROBRAS (Exemplo)
categories = ["EST_4", "EST_3"]  # EST_4 = DFP, EST_3 = ITR

# Realiza a busca
search_results = cvm_client.search_document_results(
    cod_cvm=cvm_codes_list,
    start_date=start_date,
    end_date=end_date,
    category=categories,
    last_ref_date=False  # Se True, retorna apenas o último documento por data de referência
)

# Filtra apenas DFP e ITR válido
search_results = search_results[
    search_results['categoria'].isin(["DFP - Demonstrações Financeiras Padronizadas", "ITR - Informações Trimestrais"])
]
search_results = search_results[pd.to_numeric(search_results['numero_seq_documento'], errors='coerce').notnull()]

print(search_results[['data_referencia', 'categoria', 'numero_seq_documento']].head())
```

### 4. Baixando Relatórios Financeiros
Com o `numero_seq_documento` obtido na busca anterior, você pode baixar as tabelas financeiras.

```python
# Lista de relatórios desejados (se None, baixa todos disponíveis)
reports_list = [
    'Balanço Patrimonial Ativo',
    'Demonstração do Resultado',
    'Demonstração do Fluxo de Caixa'
]

# Itera sobre os resultados da busca e baixa os relatórios
for index, row in search_results.iterrows():
    print(f"Baixando relatórios para: {row['nome_empresa']} - Ref: {row['data_referencia']}")

    financial_reports = cvm_client.get_report(
        numero_sequencial_documento=row["numero_seq_documento"],
        codigo_tipo_instituicao=row["codigo_tipo_instituicao"],
        reports_list=reports_list
    )

    for report_name, data_frame in financial_reports.items():
        print(f"--- {report_name} ---")
        print(data_frame.head())
```

## 📚 Documentação da API

### `CVMBackend`

| Método | Parâmetros Principais | Descrição |
| :--- | :--- | :--- |
| `get_cvm_codes()` | Nenhum | Retorna dicionário com códigos CVM de todas as empresas. |
| `get_search_categories()` | Nenhum | Retorna dicionário com categorias de documentos disponíveis (DFP, ITR, Fato Relevante, etc.). |
| `get_participant_types()` | Nenhum | Retorna dicionário com tipos de participantes. |
| `search_document_results(...)` | `cod_cvm`, `start_date`, `end_date`, `category` | Realiza a busca de documentos na base da CVM. Retorna um DataFrame. |
| `get_report(...)` | `numero_sequencial_documento`, `codigo_tipo_instituicao` | Baixa o conteúdo (tabelas) de um documento específico. |
| `get_b3_instruments(...)` | `ref_date` | Baixa o cadastro de instrumentos/ativos da B3 para uma data. |
| `get_b3_issuers()` | Nenhum | Baixa a lista de emissores da B3. |
| `get_cvm_public_companies()` | Nenhum | Retorna cadastro completo de cias abertas da CVM. |

## 🛠 Desenvolvimento

Para configurar o ambiente de desenvolvimento:

1.  Clone o repositório.
2.  Crie um ambiente virtual: `python -m venv .venv`
3.  Instale as dependências: `pip install -r requirements.txt`
4.  Execute os testes: `pytest`

## ⚖️ Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

<!-- MARKDOWN LINKS & IMAGES -->
[contributors-shield]: https://img.shields.io/github/contributors/leeloy84/brFinance_v2.svg?style=for-the-badge
[contributors-url]: https://github.com/leeloy84/brFinance_v2/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/leeloy84/brFinance_v2.svg?style=for-the-badge
[forks-url]: https://github.com/leeloy84/brFinance_v2/network/members
[stars-shield]: https://img.shields.io/github/stars/leeloy84/brFinance_v2.svg?style=for-the-badge
[stars-url]: https://github.com/leeloy84/brFinance_v2/stargazers
[issues-shield]: https://img.shields.io/github/issues/leeloy84/brFinance_v2.svg?style=for-the-badge
[issues-url]: https://github.com/leeloy84/brFinance_v2/issues
[license-shield]: https://img.shields.io/github/license/leeloy84/brFinance_v2.svg?style=for-the-badge
[license-url]: https://github.com/leeloy84/brFinance_v2/blob/master/LICENSE
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/leandro-eloy-sousa

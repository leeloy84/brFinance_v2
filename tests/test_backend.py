"""
Testes unitários para o módulo backend.py.
"""
import sys
from pathlib import Path


# Configuração de path para imports do projeto
pasta_raiz = Path(__file__).parent.parent
if str(pasta_raiz) not in sys.path:
    sys.path.insert(0, str(pasta_raiz))

from datetime import date
import pandas as pd
import pytest
from brfinance_v2.backend import CVMBackend



def test_cvm_backend_instantiation():
    """Testa se a classe backend pode ser instanciada."""
    backend = CVMBackend()

    assert backend is not None


def test_get_cvm_codes_structure():
    """Testa se get_cvm_codes retorna um dicionário (mock ou real)."""
    # Nota: Este teste pode exigir conexão se não for mockado
    backend = CVMBackend()

    codes = backend.get_cvm_codes()
    assert isinstance(codes, dict)
    if codes:
        # Verifica se as chaves são strings de números (geralmente)
        first_key = next(iter(codes))
        assert isinstance(first_key, str)
def test_get_search_categories_structure():
    """Testa se get_search_categories retorna um dicionário."""
    backend = CVMBackend()
    categories = backend.get_search_categories()
    assert isinstance(categories, dict)
    if categories:
        assert len(categories) > 0

def test_get_participant_types_structure():
    """Testa se get_participant_types retorna um dicionário."""
    backend = CVMBackend()
    ptypes = backend.get_participant_types()
    assert isinstance(ptypes, dict)
    if ptypes:
        assert len(ptypes) > 0

def test_get_cvm_public_companies_execution():
    """Testa se get_cvm_public_companies pode ser chamado e retorna DataFrame."""
    backend = CVMBackend()
    # Este teste faz uma requisição real para a CVM
    try:
        companies = backend.get_cvm_public_companies()
        # O retorno correto é um pd.DataFrame (conforme responses.py)
        assert isinstance(companies, pd.DataFrame)
        if not companies.empty:
            print("\n--- PRIMEIRAS EMPRESAS ENCONTRADAS NA CVM ---")
            print(companies[['nome', 'cnpj', 'cod_cvm']].head())
            print(f"Total de empresas: {len(companies)}")
            assert 'nome' in companies.columns
            assert 'cnpj' in companies.columns
    except Exception as e:
        print(f"Aviso: Falha na requisição real da CVM: {e}")
        # Se for um erro de rede/timeout, não falha o teste obrigatoriamente
        # mas logamos para saber que ocorreu.
        if "Timeout" in str(e) or "Max retries exceeded" in str(e):
             pytest.skip("Ignorando falha de rede externa da CVM")
        else:
             raise e


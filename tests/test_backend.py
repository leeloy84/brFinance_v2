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

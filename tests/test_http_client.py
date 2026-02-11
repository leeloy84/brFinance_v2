"""
Testes unitários para o módulo http_client.py.
"""
import sys
from pathlib import Path

# Configuração de path para imports do projeto
pasta_raiz = Path(__file__).parent.parent
if str(pasta_raiz) not in sys.path:
    sys.path.insert(0, str(pasta_raiz))

from brfinance_v2.http_client import CVMHttpClient
from brfinance_v2.connector import CVMHttpClientConnector


def test_http_client_instantiation():
    """Testa se o cliente HTTP pode ser instanciado."""
    connector = CVMHttpClientConnector()
    client = CVMHttpClient(session=connector.get_connector())
    assert client is not None

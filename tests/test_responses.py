"""
Testes unitários para o módulo responses.py.
"""
import sys
from pathlib import Path

# Configuração de path para imports do projeto
pasta_raiz = Path(__file__).parent.parent
if str(pasta_raiz) not in sys.path:
    sys.path.insert(0, str(pasta_raiz))

import pandas as pd
import pytest
from brfinance_v2.responses import CVMCodesResponse



class MockResponse:
    """Mock simples para objetos de resposta HTTP."""
    def __init__(self, text):
        self.text = text


def test_parse_get_cvm_codes():
    """Testa o parsing de códigos CVM a partir de HTML mockado."""
    html_content = '''
    <html>
        <body>
            <input id="hdnEmpresas" value="[{ key: '021610', value: '021610 - B3' }, { key: '023264', value: '023264 - AMBEV' }]" />
        </body>
    </html>
    '''
    mock_resp = MockResponse(html_content)
    processor = CVMCodesResponse(mock_resp)

    data = processor.data()

    assert isinstance(data, dict)
    assert data["021610"] == "B3"
    assert data["023264"] == "AMBEV"

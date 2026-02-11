"""
Módulo responsável pela gestão de sessões HTTP.
"""
import sys
from pathlib import Path

# Configuração de path para imports do projeto
pasta_raiz = Path(__file__).parent.parent
if str(pasta_raiz) not in sys.path:
    sys.path.insert(0, str(pasta_raiz))

import requests
import urllib3
from requests import Session

# Desabilita avisos de segurança de forma redundante para garantir silêncio total
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.packages.urllib3.disable_warnings()

try:
    # Compatibilidade com urllib3 < 2.0
    if hasattr(requests.packages.urllib3.util.ssl_, "DEFAULT_CIPHERS"):
        requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += "HIGH:!DH:!aNULL"

    if hasattr(requests.packages.urllib3.contrib, "pyopenssl"):
        requests.packages.urllib3.contrib.pyopenssl.DEFAULT_SSL_CIPHER_LIST += (
            "HIGH:!DH:!aNULL"
        )
except (AttributeError, TypeError):
    # Em urllib3 2.0+ o DEFAULT_CIPHERS não existe mais ou é imutável
    pass


class CVMHttpClientConnector:
    """Gerencia a sessão HTTP persistente para as requisições."""

    def __init__(self) -> None:
        """Inicializa uma nova sessão requests."""
        self._connector = Session()

    def get_connector(self) -> Session:
        """Retorna a sessão ativa.

        Returns:
            Session: Objeto de sessão do requests.
        """
        return self._connector

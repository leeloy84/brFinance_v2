"""
Constantes utilizadas na biblioteca brFinance.
"""
import sys
from pathlib import Path

# Configuração de path para imports do projeto
pasta_raiz = Path(__file__).parent.parent
if str(pasta_raiz) not in sys.path:
    sys.path.insert(0, str(pasta_raiz))

REPORT_TYPE_MAPPER = {"ITR": "EST_3", "DFP": "EST_4"}

BOOL_STRING_MAPPER = {True: "true", False: "false"}

ENET_URL = "https://www.rad.cvm.gov.br/ENET/"

"""
Módulo de utilitários para a biblioteca brFinance.
"""
import sys
from pathlib import Path

# Configuração de path para imports do projeto
pasta_raiz = Path(__file__).parent.parent
if str(pasta_raiz) not in sys.path:
    sys.path.insert(0, str(pasta_raiz))

from typing import Union, Any
import re
from brfinance_v2.constants import ENET_URL


def extract_substring(start: str, end: str, string: str) -> str:
    """Extrai uma substring entre dois limitadores.

    Args:
        start: Limitador inicial.
        end: Limitador final.
        string: String completa.

    Returns:
        str: Substring extraída.
    """
    try:
        return string.split(start)[-1].split(end)[0]
    except (IndexError, AttributeError):
        return ""


def get_enet_download_url(
    num_sequencia: Union[str, int],
    num_versao: Union[str, int],
    num_protocolo: Union[str, int],
    desc_tipo: str,
) -> str:
    """Gera a URL de download para documentos do sistema ENET.

    Args:
        num_sequencia: Número sequencial.
        num_versao: Número da versão.
        num_protocolo: Número do protocolo.
        desc_tipo: Descrição do tipo de documento.

    Returns:
            str: URL completa para download.
    """
    return (
        f"{ENET_URL}frmDownloadDocumento.aspx?Tela=ext&"
        f"numSequencia={num_sequencia}&numVersao={num_versao}&"
        f"numProtocolo={num_protocolo}-79&descTipo={desc_tipo}&"
        f"CodigoInstituicao=1"
    )


def clean_numeric_string(value: Any) -> Union[float, Any]:
    """Limpa e converte uma string numérica no formato PT-BR para float.

    Remove pontos de milhar e substitui vírgula decimal por ponto.

    Args:
        value: O valor a ser convertido (pode ser str, int, float ou None).

    Returns:
        Union[float, Any]: O valor convertido para float ou o valor original se falhar.
    """
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    try:
        # Remove espaços e limpa caracteres não numéricos comuns (exceto vírgula e ponto)
        clean_val = str(value).strip()

        # Lógica para formato PT-BR: 1.234,56 -> 1234.56
        if "," in clean_val and "." in clean_val:
            # Se tem ambos, assume que ponto é separador de milhar
            clean_val = clean_val.replace(".", "").replace(",", ".")
        elif "," in clean_val:
            # Se tem apenas vírgula, assume que é o decimal
            clean_val = clean_val.replace(",", ".")

        return float(clean_val)
    except (ValueError, TypeError):
        return value

def sanitize_filename(filename: str) -> str:
    """Remove caracteres inválidos para nomes de arquivos.

    Args:
        filename: Nome do arquivo original.

    Returns:
        str: Nome do arquivo sanitizado.
    """
    # Remove caracteres inválidos: < > : " / \ | ? *
    return re.sub(r'[<>:"/\\|?*]', '', filename).strip()

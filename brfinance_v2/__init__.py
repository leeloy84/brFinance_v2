import sys
import warnings
import urllib3

# 1. Verificação de Ambiente Virtual
# Alerta o usuário se o projeto não estiver rodando no .venv
if sys.prefix == sys.base_prefix:
    print(
        "\n" + "!" * 60 +
        "\nAVISO: O projeto não está sendo executado em um ambiente virtual (.venv).\n"
        "Isso pode causar conflitos de versões. Ative o ambiente antes de rodar.\n" +
        "!" * 60 + "\n",
        file=sys.stderr
    )

# 2. Silenciamento de Warnings (Aprimorado)
# Desabilita InsecureRequestWarning globalmente (necessário p/ conexões legadas da CVM)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Suprime aviso de depreciação específico do BeautifulSoup/lxml no Python 3.12+
# "The 'strip_cdata' option of HTMLParser() has never done anything"
warnings.filterwarnings("ignore", message="The 'strip_cdata' option of HTMLParser()")

from brfinance_v2.backend import CVMBackend  # noqa: F401

try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:  # pragma: no cover
    from importlib_metadata import version, PackageNotFoundError  # type: ignore

try:
    __version__ = version("brfinance_v2")
except PackageNotFoundError:
    # pacote não instalado
    __version__ = "0.1.0"

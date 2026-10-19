"""
Módulo responsável pelas requisições HTTP para a CVM e B3.
"""
import sys
from pathlib import Path

# Configuração de path para imports do projeto
pasta_raiz = Path(__file__).parent.parent
if str(pasta_raiz) not in sys.path:
    sys.path.insert(0, str(pasta_raiz))

import logging
from datetime import date
from typing import Dict, List, Optional, Any, Union

from bs4 import BeautifulSoup

from brfinance_v2.connector import CVMHttpClientConnector
from brfinance_v2.constants import BOOL_STRING_MAPPER, ENET_URL
from brfinance_v2.utils import extract_substring

logger = logging.getLogger(__name__)


class CVMHttpClient:
    """Cliente HTTP para comunicação com os sistemas da CVM e B3."""

    ENETCONSULTA_URL = "https://www.rad.cvm.gov.br/ENETCONSULTA/"
    LISTAR_DOCUMENTOS_URL = f"{ENET_URL}frmConsultaExternaCVM.aspx/ListarDocumentos"
    ENET_CONSULTA_EXTERNA = f"{ENET_URL}frmConsultaExternaCVM.aspx"

    def __init__(self, session: Any, timeout: int = 30) -> None:
        """Inicializa o cliente com uma sessão ativa.

        Args:
            session: Objeto de sessão (ex: aiohttp.ClientSession ou requests.Session).
            timeout: Timeout padrão para as requisições em segundos.
        """
        self.session = session
        self.timeout = timeout

    def get_search_results(
        self,
        cod_cvm: List[Union[str, int]],
        start_date: Optional[date],
        end_date: Optional[date],
        participant_type: str,
        category: str,
        last_ref_date: bool,
    ) -> Any:
        # ... (mantendo o código anterior até a chamada session) ...
        # (Ajuste de payload oculto por brevidade na instrução de substituição)
        # ...
        
        resp = self.session.post(
            self.LISTAR_DOCUMENTOS_URL, 
            data=payload, 
            headers=headers, 
            verify=False,
            timeout=self.timeout
        )
        return resp

    def get_reports(
        self,
        numero_sequencial_documento: Union[str, int],
        codigo_tipo_instituicao: Union[str, int],
        reports_list: Optional[List[str]] = None,
        category: str = "DFs Consolidadas",
    ) -> Dict[str, Any]:
        """Obtém os relatórios financeiros de um documento específico.
        # ...
        """
        url = (
            f"{ENET_URL}frmGerenciaPaginaFRE.aspx?"
            f"NumeroSequencialDocumento={numero_sequencial_documento}&"
            f"CodigoTipoInstituicao={codigo_tipo_instituicao}"
        )

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/96.0.4664.110 Safari/537.36"
            )
        }

        # 1. Requisição inicial GET
        response = self.session.get(url, headers=headers, verify=False, timeout=self.timeout)
        soup = BeautifulSoup(response.text, features="lxml")

        # 2. Identifica opções de categoria (cmbGrupo)
        cmb_grupo = soup.find(id="cmbGrupo")

        target_value = None
        current_value = None

        if cmb_grupo:
            options = cmb_grupo.find_all("option")
            for option in options:
                # Verifica qual está selecionado
                if option.has_attr("selected"):
                    current_value = option.attrs.get("value")

                # Verifica se é a categoria desejada (case insensitive)
                opt_text = option.getText().strip()
                if category.lower() == opt_text.lower():
                    target_value = option.attrs.get("value")

        # 3. Se precisamos trocar de categoria
        if target_value and target_value != current_value:
            logger.info(f"Trocando categoria de {current_value} para {target_value} ({category})")

            # Extrai campos ocultos necessários para o PostBack
            hidden_fields = {}
            for hidden in soup.find_all("input", type="hidden"):
                name = hidden.attrs.get("name")
                value = hidden.attrs.get("value", "")
                if name:
                    hidden_fields[name] = value

            # Configura payload para o PostBack
            hidden_fields["__EVENTTARGET"] = "cmbGrupo"
            hidden_fields["__EVENTARGUMENT"] = ""
            hidden_fields["cmbGrupo"] = target_value

            # Realiza POST
            response = self.session.post(
                url, 
                data=hidden_fields, 
                headers=headers, 
                verify=False,
                timeout=self.timeout
            )
            soup = BeautifulSoup(response.text, features="lxml")

        # 4. Processa a lista de relatórios (cmbQuadro)
        # ... (omitindo parte interna inalterada para brevidade)
        def get_hidden_value(element_id: str) -> str:
            element = soup.find(id=element_id)
            if element and "value" in element.attrs:
                return element.attrs["value"]
            logger.warning(f"Elemento {element_id} não encontrado ou sem atributo 'value'")
            return ""

        hdn_num_seq = get_hidden_value("hdnNumeroSequencialDocumento")
        hdn_tipo_doc = get_hidden_value("hdnCodigoTipoDocumento")
        hdn_inst = get_hidden_value("hdnCodigoInstituicao")
        hdn_hash = get_hidden_value("hdnHash")

        reg_cvm = extract_substring("NumeroSequencialRegistroCvm=", "&", response.text)

        end_of_url = (
            f"&CodTipoDocumento={hdn_tipo_doc}&"
            f"NumeroSequencialDocumento={hdn_num_seq}&"
            f"NumeroSequencialRegistroCvm={reg_cvm}&"
            f"CodigoTipoInstituicao={hdn_inst}&"
            f"Hash={hdn_hash}"
        )

        options_elem = soup.find(id="cmbQuadro")
        if not options_elem:
            logger.warning("Combo de relatórios (cmbQuadro) não encontrado.")
            return {}

        reports_options = options_elem.find_all("option")

        if reports_list is None:
            reports_list = [item.getText() for item in reports_options]

        reports = {}
        for item in reports_options:
            if item.getText() in reports_list:
                report_url = ENET_URL + item.attrs["value"] + end_of_url
                report_resp = self.session.get(
                    report_url, 
                    headers=headers, 
                    verify=False,
                    timeout=self.timeout
                )
                reports[item.getText()] = report_resp

        return reports

    def get_enet_search_page(self) -> Any:
        """Obtém a página principal de consulta externa da CVM."""
        return self.session.get(self.ENET_CONSULTA_EXTERNA, verify=False, timeout=self.timeout)

    def get_b3_instruments_token(self, ref_date: date) -> Any:
        """Obtém o token para download de instrumentos da B3."""
        date_str = ref_date.strftime("%Y-%m-%d")
        url = (
            "https://arquivos.b3.com.br/api/download/requestname?"
            f"fileName=InstrumentsConsolidated&date={date_str}"
        )
        return self.session.get(url, verify=False, timeout=self.timeout)

    def get_b3_instruments_file(self, token: str) -> Any:
        """Realiza o download dos instrumentos da B3."""
        url = f"https://arquivos.b3.com.br/api/download/?token={token}"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/96.0.4664.110 Safari/537.36"
            )
        }
        return self.session.get(url, headers=headers, verify=False, timeout=240) # Maior timeout para arquivos grandes

    def get_b3_issuers_file(self) -> Any:
        """Obtém o arquivo de emissores da B3."""
        url = "https://sistemaswebb3-listados.b3.com.br/isinProxy/IsinCall/GetFileDownload/NTE3ODA="
        return self.session.get(url, verify=False, timeout=60)

    def get_cvm_public_companies_page(self) -> Any:
        """Pesquisa companhias abertas no site da CVM."""
        url = (
            "https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/CPublica/"
            "CiaAb/ResultBuscaParticCiaAb.aspx?CNPJNome=&TipoConsult=C"
        )
        return self.session.get(url, verify=False, timeout=self.timeout)


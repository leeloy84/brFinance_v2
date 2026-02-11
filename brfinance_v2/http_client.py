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

    def __init__(self, session: Any) -> None:
        """Inicializa o cliente com uma sessão ativa.

        Args:
            session: Objeto de sessão (ex: aiohttp.ClientSession ou requests.Session).
        """
        self.session = session

    def get_search_results(
        self,
        cod_cvm: List[Union[str, int]],
        start_date: Optional[date],
        end_date: Optional[date],
        participant_type: str,
        category: str,
        last_ref_date: bool,
    ) -> Any:
        """Busca resultados de documentos na CVM.

        Args:
            cod_cvm: Lista de códigos CVM.
            start_date: Data inicial.
            end_date: Data final.
            participant_type: Tipo de participante (ex: "1").
            category: Categorias (ex: "EST_4").
            last_ref_date: Se deve retornar apenas a última data de referência.

        Returns:
            Resposta da requisição.
        """
        cod_cvm_string = ""

        if len(cod_cvm) > 0:
            cod_cvm_string = str(",".join([f"{item}".zfill(6) for item in cod_cvm]))

        data_de = ""
        data_ate = ""
        periodo = "0"

        if start_date or end_date:
            try:
                data_de = start_date.strftime("%d/%m/%Y") if start_date else ""
            except (AttributeError, ValueError):
                data_de = ""

            try:
                data_ate = end_date.strftime("%d/%m/%Y") if end_date else ""
            except (AttributeError, ValueError):
                data_ate = ""

            periodo = "2"

        categoria = category
        ultima_dt_ref = BOOL_STRING_MAPPER.get(last_ref_date, "N")

        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Content-Type": "application/json; charset=UTF-8",
            "DNT": "1",
            "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/96.0.4664.110 Safari/537.36"
            ),
            "X-Requested-With": "XMLHttpRequest",
        }

        # Payload JSON formatado para a CVM
        payload = (
            "{"
            + f"""
                dataDe: '{data_de}',
                dataAte: '{data_ate}' ,
                empresa: '{cod_cvm_string}',
                setorAtividade: '-1',
                categoriaEmissor: '-1',
                situacaoEmissor: '-1',
                tipoParticipante: '{participant_type}',
                dataReferencia: '',
                categoria: '{categoria}',
                periodo: '{periodo}',
                horaIni: '',
                horaFim: '',
                palavraChave:'',
                ultimaDtRef:'{ultima_dt_ref}',
                tipoEmpresa:'0',
                token: '',
                versaoCaptcha: ''
                """
            + "}"
        )

        resp = self.session.post(
            self.LISTAR_DOCUMENTOS_URL, data=payload, headers=headers, verify=False
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

        Args:
            numero_sequencial_documento: ID sequencial do documento.
            codigo_tipo_instituicao: Código do tipo de instituição.
            reports_list: Lista de nomes de relatórios desejados.
            category: Categoria dos relatórios (ex: "DFs Individuais", "Notas Explicativas").

        Returns:
            Dict[str, Any]: Mapeamento nome do relatório -> resposta HTTP.
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
        response = self.session.get(url, headers=headers, verify=False)
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

                # Tenta match parcial se não achou exato (ex: "DFs Individuais" vs "DFs Individuais - ...")
                # Mas cuidado para não pegar errado.

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
            # __EVENTTARGET é o controle que disparou o evento (cmbGrupo)
            hidden_fields["__EVENTTARGET"] = "cmbGrupo"
            hidden_fields["__EVENTARGUMENT"] = ""
            hidden_fields["cmbGrupo"] = target_value

            # Remove campos que não devem ser enviados ou ajusta se necessário
            # Geralmente enviamos todos os hidden + o valor do dropdown alterado

            # Realiza POST
            response = self.session.post(url, data=hidden_fields, headers=headers, verify=False)
            soup = BeautifulSoup(response.text, features="lxml")


        # 4. Processa a lista de relatórios (cmbQuadro) do HTML (seja original ou pós-postback)
        # Busca os elementos e seus valores de forma segura (reutilizando lógica auxiliar)
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
        if not reg_cvm:
             # Tenta extrair de outra forma ou do HTML se o regex falhar no text postback
             # As vezes a CVM muda a ordem. Vamos tentar pegar do URL do form action ou similar se falhar
             pass

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

        # Se reports_list for None, pega todos na categoria atual
        if reports_list is None:
            reports_list = [item.getText() for item in reports_options]

        reports = {}
        for item in reports_options:
            # Verifica se o relatório está na lista desejada
            # (Pode ser match exato ou parcial, aqui mantemos exato por enquanto conforme original)
            if item.getText() in reports_list:
                report_url = ENET_URL + item.attrs["value"] + end_of_url
                report_resp = self.session.get(report_url, headers=headers, verify=False)
                reports[item.getText()] = report_resp

        return reports

    def get_enet_search_page(self) -> Any:
        """Obtém a página principal de consulta externa da CVM."""
        return self.session.get(self.ENET_CONSULTA_EXTERNA, verify=False)

    def get_b3_instruments_token(self, ref_date: date) -> Any:
        """Obtém o token para download de instrumentos da B3."""
        date_str = ref_date.strftime("%Y-%m-%d")
        url = (
            "https://arquivos.b3.com.br/api/download/requestname?"
            f"fileName=InstrumentsConsolidated&date={date_str}"
        )
        return self.session.get(url, verify=False)

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
        return self.session.get(url, headers=headers, verify=False)

    def get_b3_issuers_file(self) -> Any:
        """Obtém o arquivo de emissores da B3."""
        url = "https://sistemaswebb3-listados.b3.com.br/isinProxy/IsinCall/GetFileDownload/NTE3ODA="
        return self.session.get(url, verify=False)

    def get_cvm_public_companies_page(self) -> Any:
        """Pesquisa companhias abertas no site da CVM."""
        url = (
            "https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/CPublica/"
            "CiaAb/ResultBuscaParticCiaAb.aspx?CNPJNome=&TipoConsult=C"
        )
        return self.session.get(url, verify=False)

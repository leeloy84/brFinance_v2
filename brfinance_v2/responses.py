"""
Módulo responsável por processar as respostas da API da CVM e B3.
"""
import sys
from pathlib import Path

# Configuração de path para imports do projeto
pasta_raiz = Path(__file__).parent.parent
if str(pasta_raiz) not in sys.path:
    sys.path.insert(0, str(pasta_raiz))

import logging
import json
import io
import zipfile
import os
from typing import Dict, List, Any, Union, Optional


import pandas as pd
from bs4 import BeautifulSoup

from brfinance_v2.utils import extract_substring, clean_numeric_string, sanitize_filename


from brfinance_v2.constants import ENET_URL

logger = logging.getLogger(__name__)


class SearchResponse:
    """Processa a resposta de busca de documentos na CVM."""

    def __init__(self, response: Any) -> None:
        """Inicializa com a resposta da requisição.

        Args:
            response: Objeto de resposta da biblioteca requests ou aiohttp.
        """
        self.response = response

    def data(self) -> pd.DataFrame:
        """Extrai os dados da resposta em um DataFrame.

        Returns:
            pd.DataFrame: Dados processados da busca.
        """
        response_json = self.response.json()
        return self._parse_get_search(response_json)

    def _parse_get_search(self, response_json: Dict[str, Any]) -> pd.DataFrame:
        """Realiza o parsing interno do JSON de busca.

        Args:
            response_json: Dicionário contendo a resposta JSON.

        Returns:
            pd.DataFrame: DataFrame com os resultados da busca.
        """
        columns = [
            "cod_cvm",
            "empresa",
            "categoria",
            "tipo",
            "especie",
            "ref_date",
            "data_entrega",
            "status",
            "version",
            "modalidade",
            "acoes",
            "outros",
        ]
        additional_columns = ["view_url", "numero_seq_documento", "codigo_tipo_instituicao"]
        download_columns = ["numSequencia", "numVersao", "numProtocolo", "descTipo"]

        response_df = pd.DataFrame(columns=columns + additional_columns + download_columns)

        dados = response_json.get("d", {}).get("dados")

        if dados:
            data_str = dados.replace("<spanOrder>", "")

            # Cria DataFrame a partir da string serializada customizada da CVM
            search_results_df = pd.DataFrame(
                [x.split("$&") for x in data_str.split("$&&*")], columns=columns
            ).iloc[:, :11]

            search_results_df = search_results_df[pd.notnull(search_results_df["acoes"])]

            if not search_results_df.empty:
                # Obtém coluna de links
                mask_popup = search_results_df["acoes"].str.contains(r"OpenPopUpVer\('")
                search_results_df.loc[mask_popup, "view_url"] = ENET_URL + search_results_df[
                    "acoes"
                ].str.extract(r"OpenPopUpVer\(\'(.*?)\'\)", expand=False)

                # Extrai dados de download
                download_info = (
                    search_results_df["acoes"]
                    .str.extract(r"OpenDownloadDocumentos\(\'(.*?)\'\)", expand=False)
                    .str.replace("'", "", regex=True)
                    .str.split(",", expand=True)
                )

                # Garante que temos o número correto de colunas de download
                for i, col in enumerate(download_columns):
                    if i < download_info.shape[1]:
                        search_results_df[col] = download_info[i]

                search_results_df.loc[mask_popup, "numero_seq_documento"] = (
                    search_results_df["acoes"].str.extract(
                        r"NumeroSequencialDocumento\=(.*?)\&", expand=False
                    )
                )

                search_results_df.loc[mask_popup, "codigo_tipo_instituicao"] = (
                    search_results_df["acoes"].str.extract(
                        r"CodigoTipoInstituicao\=(.*?)\'\)", expand=False
                    )
                )

                # Processa datas
                new_delivery = search_results_df["data_entrega"].str.split(
                    "</spanOrder>", n=-1, expand=True
                )
                search_results_df["data_entrega"] = pd.to_datetime(
                    new_delivery[1].str.strip(), format="%d/%m/%Y %H:%M"
                )

                new_ref = search_results_df["ref_date"].str.split(
                    "</spanOrder>", n=-1, expand=True
                )
                search_results_df["ref_date"] = pd.to_datetime(
                    new_ref[0].str.strip(), format="%Y%m%d"
                )

                search_results_df["cod_cvm"] = search_results_df["cod_cvm"].str.replace(
                    r"\D+", "", regex=True
                )

                search_results_df = search_results_df.replace(
                    {"</spanOrder>": ""}, regex=True
                ).sort_values("data_entrega", ascending=False)

                # Substituição de df.append por pd.concat (Pandas 2.0+)
                response_df = pd.concat([response_df, search_results_df], ignore_index=True)

        return response_df


class FinancialReportCollection(dict):
    """Coleção estruturada de relatórios financeiros.

    Permite acessar relatórios como um dicionário ou através de métodos auxiliares.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def get_report(self, report_name: str) -> Optional[pd.DataFrame]:
        """Obtém um relatório específico pelo nome.

        Args:
            report_name: Nome exato ou parte do nome do relatório.

        Returns:
            Optional[pd.DataFrame]: O relatório encontrado ou None.
        """
        if report_name in self:
            return self[report_name]

        # Busca parcial (case-insensitive)
        for key in self.keys():
            if report_name.lower() in key.lower():
                return self[key]
        return None

    def list_reports(self) -> List[str]:
        """Lista todos os nomes de relatórios disponíveis na coleção."""
        return list(self.keys())

    def to_dict(self) -> Dict[str, pd.DataFrame]:
        """Retorna a coleção como um dicionário padrão."""
        return dict(self)

    def save_all(self, folder: str, file_format: str = "xlsx") -> None:
        """Salva todos os relatórios em uma pasta especificada.

        Args:
            folder: Caminho para a pasta de destino (será criada se não existir).
            file_format: Formato para salvar ('csv', 'xlsx', 'json').
        """
        output_dir = Path(folder)
        output_dir.mkdir(parents=True, exist_ok=True)

        for report_name, df in self.items():
            safe_name = sanitize_filename(report_name)

            if file_format.lower() == "csv":
                file_path = output_dir / f"{safe_name}.csv"
                df.to_csv(file_path, index=False, sep=";", encoding="utf-8-sig")

            elif file_format.lower() == "xlsx":
                file_path = output_dir / f"{safe_name}.xlsx"
                df.to_excel(file_path, index=False)

            elif file_format.lower() == "json":
                file_path = output_dir / f"{safe_name}.json"
                df.to_json(file_path, orient="records", force_ascii=False, indent=2)

            else:
                logger.warning(f"Formato desconhecido: {file_format}. Ignorando {report_name}.")
                continue

            logger.info(f"Relatório salvo: {file_path}")



class ReportResponse:
    """Processa a resposta de relatórios financeiros detalhados."""

    def __init__(self, response: Dict[str, Any], previous_results: bool) -> None:
        """Inicializa com as respostas e flag de resultados anteriores.

        Args:
            response: Dicionário de respostas (key=nome do relatório).
            previous_results: Se deve considerar resultados anteriores.
        """
        self.response = response
        self.previous_results = previous_results

    def data(self) -> FinancialReportCollection:
        """Extrai os dados de todos os relatórios em uma coleção estruturada.

        Returns:
            FinancialReportCollection: Relatórios processados.
        """
        data = FinancialReportCollection()
        for key, html_resp in self.response.items():
            processed_df = self._parse_get_reports(html_resp.text, key)
            if not processed_df.empty:
                data[key] = processed_df

        return data

    def _parse_get_reports(self, html: str, report_name: str) -> pd.DataFrame:
        """Realiza o parsing de um relatório individual em HTML.

        Args:
            html: Conteúdo HTML do relatório.
            report_name: Nome do relatório sendo processado.

        Returns:
            pd.DataFrame: DataFrame com os dados do relatório.
        """
        soup = BeautifulSoup(html, features="lxml")
        titulo_elem = soup.find(id="TituloTabelaSemBorda")
        currency_unit = titulo_elem.getText() if titulo_elem else ""

        index_moeda = -1
        if report_name == "Demonstração do Fluxo de Caixa":
            index_moeda = -2

        if " - " in currency_unit:
            currency_unit = (
                currency_unit.split(" - ")[index_moeda].replace("(", "").replace(")", "")
            )

        table_index = 0
        if report_name == "Demonstração das Mutações do Patrimônio Líquido":
            table_index = 1

        # Uso de pd.read_html otimizado - Lemos apenas uma vez como texto para controle total
        try:
            dfs = pd.read_html(io.StringIO(html), header=0, decimal=",", thousands=".")
            if not dfs or len(dfs) <= table_index:
                return pd.DataFrame()

            df = dfs[table_index].copy()

            for column in df.columns:
                col_strip = column.strip()

                # Identifica colunas de texto (Conta e Descrição)
                if any(kw in col_strip for kw in ["Conta", "Descri", "Legenda"]):
                    df[column] = df[column].astype(str).str.strip()
                else:
                    # Aplica limpeza numérica robusta
                    df[column] = df[column].apply(clean_numeric_string)
                    # Força conversão para numérico onde possível, mantendo NaN para falhas
                    df[column] = pd.to_numeric(df[column], errors="coerce")

            if report_name != "Demonstração das Mutações do Patrimônio Líquido":
                if not self.previous_results:
                    # Obtém apenas colunas essenciais: Geralmente [Conta, Descrição, Valor]
                    # As 3 primeiras colunas costumam ser as principais
                    df = df.iloc[:, 0:3]
                    new_columns = list(df.columns[:-1]) + ["Valor"]
                    df.columns = new_columns

            df["currency_unit"] = currency_unit
            return df

        except Exception as e:
            logger.error(f"Erro ao processar relatório {report_name}: {str(e)}")
            return pd.DataFrame()



class CVMCodesResponse:
    """Processa a lista de códigos CVM das empresas."""

    def __init__(self, response: Any) -> None:
        self.response = response

    def data(self) -> Dict[str, str]:
        """Extrai os códigos CVM e nomes das empresas.

        Returns:
            Dict[str, str]: Mapeamento código -> nome.
        """
        return self._parse_get_cvm_codes(self.response.text)

    def _parse_get_cvm_codes(self, html: str) -> Dict[str, str]:
        hdn_empresas_elem = BeautifulSoup(html, features="lxml").find(id="hdnEmpresas")
        if not hdn_empresas_elem:
            return {}

        hdn_empresas = hdn_empresas_elem.attrs.get("value", "[]")

        # O formato retornado pela CVM é um pseudo-JSON: [{ key: '...', value: '...' }, ...]
        # Para evitar problemas com aspas simples nos nomes das empresas, usamos ast.literal_eval
        # após garantir que as chaves tenham aspas.
        import ast

        try:
            cleaned = hdn_empresas.replace("key:", "'key':").replace("value:", "'value':")
            empresas_json = ast.literal_eval(cleaned)
        except (ValueError, SyntaxError):
            # Fallback para o método anterior se falhar
            hdn_empresas_clean = (
                hdn_empresas.replace("{ key:", '{ "key":')
                .replace(", value:", ', "value":')
                .replace("'", '"')
            )
            empresas_json = json.loads(hdn_empresas_clean)

        empresas = {}
        for empresa in empresas_json:
            empresa_value = empresa["value"].split(" - ")
            empresas[empresa_value[0]] = empresa_value[-1]
        return empresas


class SearchCategoriesResponse:
    """Processa as categorias de busca da CVM."""

    def __init__(self, response: Any) -> None:
        self.response = response

    def data(self) -> Dict[str, str]:
        """Extrai as categorias disponíveis.

        Returns:
            Dict[str, str]: Mapeamento código -> descrição.
        """
        return self._parse_get_consulta_externa_cvm_categories(self.response.text)

    def _parse_get_consulta_externa_cvm_categories(self, html: str) -> Dict[str, str]:
        hdn_combo = BeautifulSoup(html, features="lxml").find(
            id="hdnComboCategoriaTipoEspecie"
        )
        if not hdn_combo:
            return {}

        hdn_value = hdn_combo.attrs.get("value", "")
        options = BeautifulSoup(hdn_value, features="lxml").find_all("option")

        categories = {}
        for option in options:
            val = option.attrs.get("value")
            if val:
                categories[val] = option.getText().replace("\xa0", "")

        return categories


class ParticipantTypesResponse:
    """Processa os tipos de participantes disponíveis."""

    def __init__(self, response: Any) -> None:
        self.response = response

    def data(self) -> Dict[str, str]:
        """Extrai os tipos de participantes.

        Returns:
            Dict[str, str]: Mapeamento ID -> descrição.
        """
        return self._parse_get_consulta_externa_cvm_tipo_participante(self.response.text)

    def _parse_get_consulta_externa_cvm_tipo_participante(self, html: str) -> Dict[str, str]:
        cbo_elem = BeautifulSoup(html, features="lxml").find(id="cboTipoParticipante")
        if not cbo_elem:
            return {}

        options = cbo_elem.find_all("option")
        tipo_participante = {}
        for option in options:
            val = option.attrs.get("value")
            if val:
                tipo_participante[val] = option.getText()

        return tipo_participante


class B3InstrumentsTokenResponse:
    """Processa o token para cadastro de instrumentos da B3."""

    def __init__(self, response: Any) -> None:
        self.response = response

    def data(self) -> Optional[str]:
        """Extrai o token da resposta JSON.

        Returns:
            Optional[str]: Token B3.
        """
        json_resp = self.response.json()
        return json_resp.get("token")


class B3InstrumentsResponse:
    """Processa o CSV de cadastro de instrumentos da B3."""

    def __init__(self, response: Any) -> None:
        self.response = response

    def data(self) -> pd.DataFrame:
        """Extrai os ativos em um DataFrame.

        Returns:
            pd.DataFrame: Dados dos ativos.
        """
        return self._parse_get_cadastro_instrumentos(self.response.text)

    def _parse_get_cadastro_instrumentos(self, csv_data: str) -> pd.DataFrame:
        return pd.read_csv(io.StringIO(csv_data), sep=";")


class B3IssuersResponse:
    """Processa o arquivo ZIP de emissores da B3."""

    def __init__(self, response: Any) -> None:
        self.response = response

    def data(self) -> pd.DataFrame:
        """Extrai os dados de emissores.

        Returns:
            pd.DataFrame: Dados processados.
        """
        return self._parse_get_emissor(self.response.content)

    def _parse_get_emissor(self, content: bytes) -> pd.DataFrame:
        with zipfile.ZipFile(io.BytesIO(content)) as zfile:
            with zfile.open("EMISSOR.TXT") as emissor_file:
                header = ["Asst", "descricao", "cnpj", "outro"]
                df = pd.read_csv(emissor_file, names=header)
                df["cnpj"] = pd.to_numeric(df["cnpj"], errors="coerce")
                return df


class CVMPublicCompaniesResponse:
    """Processa o resultado da pesquisa de companhias abertas."""

    def __init__(self, response: Any) -> None:
        self.response = response

    def data(self) -> pd.DataFrame:
        """Extrai os dados da pesquisa.

        Returns:
            pd.DataFrame: Dados das companhias.
        """
        return self._parse_get_pesquisa_cia_aberta(self.response.text)

    def _parse_get_pesquisa_cia_aberta(self, content: str) -> pd.DataFrame:
        dfs = pd.read_html(io.StringIO(content), header=0)
        if not dfs:
            return pd.DataFrame()

        df = dfs[0]
        df["CNPJ"] = pd.to_numeric(df["CNPJ"].str.replace(r"\D+", "", regex=True), errors="coerce")

        df.rename(
            columns={
                "NOME": "nome",
                "CNPJ": "cnpj",
                "CÓDIGO CVM": "cod_cvm",
                "TIPO DE PARTICIPANTE": "tipo_participante",
                "SITUAÇÃO REGISTRO": "situacao_registro",
            },
            inplace=True,
        )

        return df

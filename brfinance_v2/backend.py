"""
Módulo de interface principal para a biblioteca brFinance.
"""
from datetime import date
from typing import List, Optional, Any, Union

from brfinance_v2.connector import CVMHttpClientConnector
from brfinance_v2.http_client import CVMHttpClient
from brfinance_v2.responses import (
    CVMCodesResponse,
    SearchCategoriesResponse,
    SearchResponse,
    ReportResponse,
    ParticipantTypesResponse,
    B3InstrumentsTokenResponse,
    B3InstrumentsResponse,
    B3IssuersResponse,
    CVMPublicCompaniesResponse,
)
from brfinance_v2.cache import CacheManager


# Singleton para o conector
POOL_CONNECTOR = CVMHttpClientConnector()


class CVMBackend:
    """Interface principal para consulta de dados na CVM e B3."""

    def __init__(self) -> None:
        """Inicializa o backend com um conector de pool."""
        self._connector = POOL_CONNECTOR.get_connector()
        self.cache = CacheManager()


    def _http_client(self) -> CVMHttpClient:
        """Cria uma instância do cliente HTTP.

        Returns:
            CVMHttpClient: Instância configurada com a sessão atual.
        """
        return CVMHttpClient(session=self._connector)

    def search_document_results(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        cod_cvm: Optional[List[Union[str, int]]] = None,
        participant_type: Optional[List[int]] = None,
        category: Optional[List[str]] = None,
        last_ref_date: bool = False,
    ) -> Any:
        """Obtém resultados de busca na consulta externa da CVM.

        Args:
            start_date: Data inicial da busca.
            end_date: Data final da busca.
            cod_cvm: Lista de códigos CVM das empresas.
            participant_type: Tipos de participantes (default [1]).
            category: Categorias de documentos.
            last_ref_date: Retornar apenas último documento por data ref.

        Returns:
            Dados processados da busca.
        """
        if cod_cvm is None:
            cod_cvm = []

        if category is None:
            category = ["EST_-1", "IPE_-1_-1_-1"]

        if participant_type is None:
            participant_type = [1]

        response = self._http_client().get_search_results(
            cod_cvm=cod_cvm,
            start_date=start_date,
            end_date=end_date,
            category=",".join(category),
            participant_type=",".join([str(item) for item in participant_type]),
            last_ref_date=last_ref_date,
        )
        response_class = SearchResponse(response=response)

        return response_class.data()

    def get_report(
        self,
        numero_sequencial_documento: Union[str, int],
        codigo_tipo_instituicao: Union[str, int],
        reports_list: Optional[List[str]] = None,
        category: str = "DFs Consolidadas",
        previous_results: bool = False,
    ) -> Any:
        """Obtém relatórios financeiros detalhados.

        Args:
            numero_sequencial_documento: ID do documento.
            codigo_tipo_instituicao: ID do tipo de instituição.
            reports_list: Lista de relatórios desejados.
            category: Categoria dos relatórios (ex: "DFs Individuais", "Notas Explicativas").
            previous_results: Considerar resultados de exercícios anteriores.

        Returns:
            Relatórios processados.
        """
        response = self._http_client().get_reports(
            numero_sequencial_documento,
            codigo_tipo_instituicao,
            reports_list,
            category,
        )
        response_class = ReportResponse(
            response=response, previous_results=previous_results
        )

        return response_class.data()

    def get_cvm_codes(self) -> Any:
        """Obtém lista de códigos CVM de todas as empresas.

        Returns:
            Mapeamento código -> nome.
        """
        # Tenta obter do cache (validade: 365 dias = 8760 horas)
        cached_data = self.cache.get_data("cvm_codes", max_age_hours=8760)

        if cached_data:
            return cached_data

        response = self._http_client().get_enet_search_page()
        response_class = CVMCodesResponse(response=response)
        data = response_class.data()

        # Salva no cache
        self.cache.save_data("cvm_codes", data)

        return data


    def get_search_categories(self) -> Any:
        """Obtém categorias disponíveis na consulta da CVM.

        Returns:
            Mapeamento código -> descrição.
        """
        # Cache de 1 ano para categorias (mudam muito raramente)
        cached_data = self.cache.get_data("cvm_categories", max_age_hours=8760)

        if cached_data:
            return cached_data

        response = self._http_client().get_enet_search_page()
        response_class = SearchCategoriesResponse(response=response)
        data = response_class.data()

        self.cache.save_data("cvm_categories", data)

        return data


    def get_participant_types(self) -> Any:
        """Obtém tipos de participantes disponíveis na CVM.

        Returns:
            Mapeamento ID -> descrição.
        """
        cached_data = self.cache.get_data("participant_types", max_age_hours=8760)

        if cached_data:
            return cached_data

        response = self._http_client().get_enet_search_page()
        response_class = ParticipantTypesResponse(response=response)
        data = response_class.data()

        self.cache.save_data("participant_types", data)

        return data


    def get_b3_instruments(self, ref_date: date = date.today()) -> Any:
        """Obtém cadastro de ativos/instrumentos da B3.

        Args:
            ref_date: Data de referência para os dados.

        Returns:
            Dados de ativos.
        """
        token_response = self._http_client().get_b3_instruments_token(
            ref_date=ref_date
        )
        token = B3InstrumentsTokenResponse(response=token_response).data()

        response = self._http_client().get_b3_instruments_file(token=token)
        response_class = B3InstrumentsResponse(response=response)

        return response_class.data()

    def get_b3_issuers(self) -> Any:
        """Obtém dados de emissores da B3.

        Returns:
            Dados de emissores.
        """
        response = self._http_client().get_b3_issuers_file()
        response_class = B3IssuersResponse(response=response)

        return response_class.data()

    def get_cvm_public_companies(self) -> Any:
        """Realiza pesquisa geral de companhias abertas na CVM.

        Returns:
            Dados das companhias.
        """
        response = self._http_client().get_cvm_public_companies_page()
        response_class = CVMPublicCompaniesResponse(response=response)

        return response_class.data()

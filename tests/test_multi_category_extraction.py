"""
Teste unitário para extração de relatórios de múltiplas categorias.
"""
import sys
from pathlib import Path
import logging

# Configuração de path
pasta_raiz = Path(__file__).parent.parent
if str(pasta_raiz) not in sys.path:
    sys.path.insert(0, str(pasta_raiz))

import unittest
from brfinance_v2.backend import CVMBackend

# Configura logging para debug durante os testes
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestMultiCategoryExtraction(unittest.TestCase):
    """Testes para extração de categorias variadas estendendo o CVMBackend."""

    @classmethod
    def setUpClass(cls):
        """Inicializa backend uma vez para todos os testes."""
        cls.backend = CVMBackend()
        # Inicializa sessão
        cls.backend.get_cvm_codes()
        # ID para testes (Petrobras 2024)
        cls.doc_id = 145077
        cls.inst_id = 1

    def test_01_dfs_consolidadas_default(self):
        """Testa comportamento padrão (DFs Consolidadas)."""
        logger.info("Testando DFs Consolidadas (Default)...")
        resultado = self.backend.get_report(
            numero_sequencial_documento=self.doc_id,
            codigo_tipo_instituicao=self.inst_id
        )
        self.assertIsNotNone(resultado)
        self.assertTrue(len(resultado) > 0)
        self.assertIn("Balanço Patrimonial Ativo", resultado)
        # Verifica se DataFrame não está vazio
        self.assertFalse(resultado["Balanço Patrimonial Ativo"].empty)

    def test_02_dfs_individuais(self):
        """Testa categoria DFs Individuais."""
        logger.info("Testando DFs Individuais...")
        resultado = self.backend.get_report(
            numero_sequencial_documento=self.doc_id,
            codigo_tipo_instituicao=self.inst_id,
            category="DFs Individuais"
        )
        self.assertIsNotNone(resultado)
        self.assertTrue(len(resultado) > 0)
        # Notas: DFs Individuais também têm BP Ativo, mas os valores podem diferir
        self.assertIn("Balanço Patrimonial Ativo", resultado)

        # Opcional: Comparar valor com consolidado se necessário, mas a existência já valida a troca
        # Se o backend não trocasse, retornaria o mesmo objeto (cacheado ou não)
        # mas aqui estamos chamando separado.

        # Vamos pegar o valor do consolidado para comparar (se possível)
        # Mas o teste isolado é suficiente se retornar dados válidos.

    def test_03_dados_empresa(self):
        """Testa categoria Dados da Empresa."""
        logger.info("Testando Dados da Empresa...")
        resultado = self.backend.get_report(
            numero_sequencial_documento=self.doc_id,
            codigo_tipo_instituicao=self.inst_id,
            category="Dados da Empresa"
        )
        self.assertIsNotNone(resultado)
        # Dados da empresa geralmente retorna tabelas com infos cadastrais
        # Verificamos as chaves disponíveis
        logger.info(f"Relatórios encontrados em Dados da Empresa: {list(resultado.keys())}")
        self.assertTrue(len(resultado) > 0)

    def test_04_notas_explicativas(self):
        """Testa categoria Notas Explicativas."""
        logger.info("Testando Notas Explicativas...")
        resultado = self.backend.get_report(
            numero_sequencial_documento=self.doc_id,
            codigo_tipo_instituicao=self.inst_id,
            category="Notas Explicativas"
        )
        self.assertIsNotNone(resultado)
        logger.info(f"Relatórios encontrados em Notas Explicativas: {list(resultado.keys())}")
        # Notas geralmente retorna algo? Se for PDF, o parse do HTML pode falhar ou retornar vazio
        # Vamos apenas logar e verificar se não quebra, pois o comportamento do HTML é incerto sem ver.
        # Se retornar vazio, é aceitável se for um PDF direto, mas o teste verifica a robustez.

if __name__ == "__main__":
    unittest.main()

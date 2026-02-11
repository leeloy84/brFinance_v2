"""
Teste unitário para obtenção de relatório financeiro específico da CVM.

Este teste valida a funcionalidade de buscar um relatório utilizando o
número sequencial do documento e o código do tipo de instituição.
"""
import sys
from pathlib import Path

# Configuração de path para imports do projeto
# O bloco abaixo garante que o diretório raiz seja adicionado ao sys.path
# para permitir a importação dos módulos locais.
pasta_raiz = Path(__file__).parent.parent
if str(pasta_raiz) not in sys.path:
    sys.path.insert(0, str(pasta_raiz))

import unittest
import pandas as pd
from brfinance_v2.backend import CVMBackend



class TestObterRelatorio(unittest.TestCase):
    """Classe de teste para a funcionalidade de obtenção de relatórios."""

    def setUp(self) -> None:
        """Inicializa a instância do backend para os testes."""
        self.backend = CVMBackend()


    def test_get_report_by_ids(self) -> None:
        """
        Testa a obtenção de um relatório CVM com IDs específicos.
        IDs utilizados:
            - numero_seq_documento: 145077
            - codigo_tipo_instituicao: 1
        """
        # Parâmetros fornecidos pelo usuário
        numero_seq_documento: int = 145077
        codigo_tipo_instituicao: int = 1

        # Inicializa a sessão visitando a página principal (necessário para cookies)
        print("Inicializando sessão com a CVM...")
        self.backend.get_cvm_codes()

        print(
            f"Iniciando busca do relatório - Doc: {numero_seq_documento}, "
            f"Inst: {codigo_tipo_instituicao}"
        )

        try:
            # Chama o método do backend para obter o relatório
            resultado = self.backend.get_report(
                numero_sequencial_documento=numero_seq_documento,
                codigo_tipo_instituicao=codigo_tipo_instituicao
            )

            # Validações dos resultados obtidos
            self.assertIsNotNone(resultado, "O resultado não deve ser nulo.")

            # Novo: Valida se é instância de FinancialReportCollection (e dict)
            self.assertIsInstance(
                resultado, dict, "O resultado deve ser compatível com dicionário."
            )
            # Verifica se possui métodos da coleção (duck typing ou check de atributo)
            self.assertTrue(hasattr(resultado, 'get_report'), "O resultado deve ser um FinancialReportCollection.")

            if resultado:
                print(f"Sucesso! Foram encontrados {len(resultado)} relatórios.")

                # Teste da listagem
                lista_relatorios = resultado.list_reports()
                print(f"Relatórios disponíveis: {lista_relatorios}")
                self.assertIsInstance(lista_relatorios, list)

                for nome_relatorio, df in resultado.items():
                    self.assertIsInstance(
                        df, pd.DataFrame, f"O item {nome_relatorio} deve ser um DataFrame."
                    )
                    print(f" - Relatório: {nome_relatorio} (Linhas: {len(df)})")

                    # Verificação de Limpeza Numérica
                    if "Valor" in df.columns:
                        # Pega uma amostra não nula para testar se é numérico
                        sample_val = df["Valor"].dropna().iloc[0] if not df["Valor"].dropna().empty else 0
                        print(f"   Amostra de Valor: {sample_val} (Tipo: {type(sample_val)})")
                        # Em pandas 2.0+, numpy dtypes são comuns, mas float python puro também é aceito
                        is_numeric = isinstance(sample_val, (int, float, complex)) or pd.api.types.is_number(sample_val)
                        self.assertTrue(is_numeric, f"A coluna 'Valor' deveria ser numérica no relatório {nome_relatorio}, mas encontrou {type(sample_val)}")


                # Lógica para "download" usando busca flexível
                # Agora usamos o método get_report com busca parcial ("balanco" encontraria, mas vamos ser específicos)
                df_ativo = resultado.get_report("Balanço Patrimonial Ativo")

                if df_ativo is not None:
                    # Define diretório de downloads na raiz do projeto
                    diretorio_download = pasta_raiz / "downloads"
                    diretorio_download.mkdir(exist_ok=True)

                    nome_arquivo = f"balanco_ativo_{numero_seq_documento}.csv"
                    caminho_arquivo = diretorio_download / nome_arquivo

                    # Salva o DataFrame em CSV
                    df_ativo.to_csv(
                        caminho_arquivo,
                        index=False,
                        encoding="utf-8-sig",
                        sep=";"
                    )

                    print(f"\n[DOWNLOAD] Relatório 'Balanço Patrimonial Ativo' salvo com sucesso!")
                    print(f"Arquivo: {caminho_arquivo}")
                else:
                    print("\nAviso: O relatório 'Balanço Patrimonial Ativo' não foi encontrado.")

            else:
                print("Aviso: A busca não retornou nenhum dado para os IDs informados.")

        except Exception as e:
            # Se falhar, tenta imprimir o erro detalhado
            print(f"\nErro durante a execução: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            self.fail(f"A execução do teste falhou com o erro: {str(e)}")



    def test_save_all_reports(self) -> None:
        """Testa a funcionalidade de exportação automática de relatórios."""
        # IDs para teste
        numero_seq_documento: int = 145077
        codigo_tipo_instituicao: int = 1

        # Obtém relatórios (assumindo que o teste anterior validou que funciona)
        # Para acelerar, usar cache se disponível (backend faz isso auto)
        resultado = self.backend.get_report(
            numero_sequencial_documento=numero_seq_documento,
            codigo_tipo_instituicao=codigo_tipo_instituicao
        )

        if not resultado:
            self.skipTest("Não foi possível obter relatórios para testar o salvamento.")

        # Diretório temporário para teste de exportação
        export_dir = pasta_raiz / "downloads" / "test_export"

        # Testa exportação CSV
        print("\nTestando exportação CSV...")
        resultado.save_all(folder=str(export_dir), file_format="csv")

        # Verifica se arquivos foram criados
        csv_files = list(export_dir.glob("*.csv"))
        self.assertTrue(len(csv_files) > 0, "Deveria ter exportado arquivos .csv")
        print(f"Arquivos CSV exportados: {[f.name for f in csv_files]}")

        # Testa exportação Excel
        print("\nTestando exportação Excel...")
        resultado.save_all(folder=str(export_dir), file_format="xlsx")

        # Verifica se arquivos Excel foram criados
        xlsx_files = list(export_dir.glob("*.xlsx"))
        self.assertTrue(len(xlsx_files) > 0, "Deveria ter exportado arquivos .xlsx")
        print(f"Arquivos Excel exportados: {[f.name for f in xlsx_files]}")

        # Limpeza (opcional, ou deixar para inspeção manual)
        # import shutil
        # shutil.rmtree(export_dir) # Comentado para permitir verificação manual se necessário


if __name__ == "__main__":
    # Executa os testes se o script for chamado diretamente
    unittest.main()

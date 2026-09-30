"""Interface principal do sistema.

As três operações de negócio ficam explícitas:
1. processar relatórios PDF e persistir;
2. gerar relatório consolidado;
3. consultar a base em linguagem natural.
"""

import os

from .database import validar_dados_contrato, salvar_relatorio, conciliar_comprovantes_despesas
from .processing import carregar_arquivos, extrair_dados_comprovantes_pdf
from .report import executar_pipeline_relatorio
from .consultas import gerar_sql, preparar_e_validar_sql, executar_sql
from .database import construir_catalogo, catalogo_para_texto


def processar_relatorios(codigo_obra: str, id_contrato: int, diretorio: str = "/content"):
    """Processa um ou vários PDFs e persiste os dados no banco."""
    arquivos = [
        os.path.join(diretorio, f)
        for f in os.listdir(diretorio)
        if f.lower().startswith("n") and f.lower().endswith(".pdf")
    ]

    resultados = []
    for pdf_path in arquivos:
        dados = extrair_dados_comprovantes_pdf(pdf_path)
        if dados:
            # A persistência final deve receber o contrato e o nome do PDF.
            salvar_relatorio(dados, id_contrato, os.path.basename(pdf_path))
            resultados.append(os.path.basename(pdf_path))

    # Mantém a conciliação como etapa posterior do processamento.
    conciliar_comprovantes_despesas(limiar_similaridade_doc=80)
    return resultados


def gerar_relatorio_consolidado(nome_cliente: str, id_contrato: int, codigo_obra: str):
    """Gera o PDF consolidado para o contrato."""
    return executar_pipeline_relatorio(nome_cliente, str(id_contrato), codigo_obra)


def consultar_linguagem_natural(pergunta: str, id_contrato: int):
    """Transforma pergunta em SQL, valida e executa somente consultas permitidas."""
    catalogo = construir_catalogo()
    catalogo_texto = catalogo_para_texto(catalogo)

    sql_gerado = gerar_sql(pergunta, catalogo_texto, id_contrato)
    valido, mensagem, sql = preparar_e_validar_sql(sql_gerado.sql)

    if not valido:
        print(mensagem)
        return None

    print("SQL gerado:")
    print(sql)
    return executar_sql(sql)


def main():
    """Menu simples para execução no Google Colab."""
    print("=" * 70)
    print("SISTEMA DE GESTÃO DE RELATÓRIOS DE DESPESAS DE OBRAS")
    print("=" * 70)

    codigo_obra = input("Digite o código da obra/contrato ou 0 para sair: ").strip().upper()
    if codigo_obra == "0":
        return

    contrato = validar_dados_contrato(codigo_obra)
    if not contrato:
        return

    id_contrato = contrato[0]["id_contrato"]
    nome_cliente = contrato[0]["nome_cliente"]

    while True:
        print("\n1 - Processar relatório(s) de despesas")
        print("2 - Gerar relatório consolidado")
        print("3 - Consultar dados em linguagem natural")
        print("0 - Sair")
        opcao = input("Escolha: ").strip()

        if opcao == "1":
            processar_relatorios(codigo_obra, id_contrato)
        elif opcao == "2":
            gerar_relatorio_consolidado(nome_cliente, id_contrato, codigo_obra)
        elif opcao == "3":
            pergunta = input("Digite sua pergunta: ")
            consultar_linguagem_natural(pergunta, id_contrato)
        elif opcao == "0":
            break
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    main()

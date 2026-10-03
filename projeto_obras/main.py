########################################################################
"""Interface principal
  Sistema : 
    A partir de um código obra/contrato informado: 
    1. Permite o upload de relatórios períodicos de despesas de obras contendo quadro resumo das despesas e comprovantes 
como notas fiscais, recibos, comprovantes de transferência, orçamentos, etc. Os relatórios apresentam-se no formato PDF. Os comprovantes são anexados como imagens.
    2. Permite a geração de relatório consolidado de despesas para o contrato 
    3. Permite a realização de consulta a base de dados relacioal, usando LINGUAGEM NATURAL. 
    As três operações de negócio ficam explícitas:
    1 - Processar relatório(s) de despesas"
    2 - Gerar relatório consolidado"
    3 - Consultar dados (Use linguagem natural)

"""

import os
from pathlib import Path
import io
import json
from thefuzz import fuzz
from google.colab import files

from .database import validar_dados_contrato, validar_relatorio_processado, salvar_relatorio, conciliar_comprovantes_despesas
from .processing import carregar_arquivos, extrair_dados_comprovantes_pdf,normalizar_texto
from .report import executar_pipeline_relatorio
from .consultas import gerar_sql, preparar_e_validar_sql, executar_sql
from .database import construir_catalogo, catalogo_para_texto



def main():

  ##########################################################################################
  # FUNÇÃO PRINCIPAL - SISTEMA DE GESTÃO DE RELATÓRIOS DE DESPESAS DE OBRAS
  # OPÇÕES DISPONÍVEIS:
  # 1 - Processar relatório(s) de despesas
  # 2 - Gerar relatório consolidado"
  # 3 - Consultar dados (Use LINGUAGEM NATURAL)
  #  0 - Sair
  # Regras: O código obra/contrato deve estar previamente cadastrado.
  #         O sistema checa os dados do cliente cadastrato e os dados do cliente informado no relatório 
  #         A cada execução são processados dados de um unico contrato 
  
  ##########################################################################################

   # 1. Diretório atual do Colab
   os.chdir('/content/')
   diretorio = "."
   ctl_encerrar = False

   print("\n" + "=" * 60)
   print("       SISTEMA DE ANÁLISE DE RELATORIOS DE DESPESAS DE OBRAS")
   print("=" * 60)
   
   

   while True and not ctl_encerrar:
     #Entrada do código da Obra/Contrato
     codigo_obra = input("\n Digite o código da obra/contrato ou 0 - Sair:").strip().upper()

     if not codigo_obra:
        print("\n ❌ Nenhum código de obra foi informado.")
        continue 
     elif codigo_obra == "0":
        print("\n 🏁 Execução Encerrada")
        ctl_encerrar = True
        break
     else:
        print("\n \n Código Obra Informado: ", codigo_obra)
        contrato = validar_dados_contrato(codigo_obra)
        if contrato:
          nome_cliente = contrato[0]["nome_cliente"]
          nome_cliente = nome_cliente.upper()
          id_contrato = contrato[0]["id_contrato"]
          print(f"⚠️ Serão processados dados somente do cliente: {nome_cliente}")
          while True:
               #Entrada da opção de processamento
               print("\n Escolha uma opção:")
               print("1 - Processar relatório(s) de despesas")
               print("2 - Gerar relatório consolidado")
               print("3 - Consultar dados (Use linguagem natural)")
               print("0 - Sair")

               opcao = input("\n Digite a opção desejada: ").strip()

               # ---------------------------------------------------------
               # OPÇÃO 1 - PROCESSAR RELATÓRIO(S)
               # ---------------------------------------------------------
               if opcao == "1":

                 print("\n########################################################################")
                 print("\n➡️ Processamento dos relatórios selecionados será executado ...")
                 print("\n########################################################################")

                 # Remove relatorios já carregados anteriomente para que não sejm novamente avaliados
                 for arq in os.listdir(diretorio):
                   # Converte o nome para minúsculo para checar 'n' e 'N' ao mesmo tempo
                   if arq.lower().startswith('n') and arq.lower().endswith('.pdf'):
                     caminho_completo = os.path.join(diretorio, arq)
                     try:
                      os.remove(caminho_completo)
                     except Exception as e:
                      print(f"Erro ao remover {arq}: {e}")

                 #Carrega arquivos selecionados pelo usuário
                 arquivos_upload = files.upload()
                 arquivos_pdf = [arq
                    for arq in os.listdir(diretorio)
                       if (arq.startswith("N") or arq.startswith("n")) and arq.lower().endswith(".pdf")]

                 for arq in arquivos_pdf:
                   print(f"\n \n - {arq}")
                   if validar_relatorio_processado(id_contrato, arq):
                     print("\n🟢 Processamento em andamento: ", arq)
                     dados_dict = extrair_dados_comprovantes_pdf(arq)
                     if dados_dict is None:
                       print(f"❌ Erro: Não foi possível processar o relatório",arq, "Verifique o arquivo e a conexão com a API.")
                     else:
                       dados_dict["nome_relatorio"] = arq
                       #print(json.dumps(dados_dict, indent=2, ensure_ascii=False))
                       cliente = normalizar_texto(dados_dict["nome_cliente"])
                       cliente = cliente.upper()
                       if (fuzz.ratio(cliente, nome_cliente) < 90):
                          print(f"⚠️ O relatório ",arq, "não será processado pois nomes dos clientes são diferentes:")
                          print(cliente, " X ", nome_cliente)
                       else:
                          salvar_relatorio(dados_dict,id_contrato,arq)

                   print("\n ⚙️ Executando a Conciliação de Despesas e Comprovantes Disponíveis ...")
                   conciliar_comprovantes_despesas(50)

               # ---------------------------------------------------------
               # OPÇÃO 2 - GERAR RELATÓRIO CONSOLIDADO
               # ---------------------------------------------------------
               elif opcao == "2":

                print("\n########################################################################")
                print("\n➡️ Geração de Relatório Consolidado ...")
                print("\n########################################################################")

                """Gera o PDF consolidado para o contrato."""
                rel = executar_pipeline_relatorio(nome_cliente,id_contrato,codigo_obra)
                    
                print(f"\n Relatório: {rel}")

               elif opcao == "3":
                 # ---------------------------------------------------------
                 # OPÇÃO 3 - PERGUNTAS EM LINGUAGEM NATURAL
                 # ---------------------------------------------------------

                 catalogo = construir_catalogo()
                 catalogo_texto = catalogo_para_texto(catalogo)
                 print("/n catalogo_texto:")
                 #print(catalogo_texto)

                 print("\n########################################################################")
                 print("\n➡️ Consulta a Dados ...")
                 print("\n########################################################################")

                 pergunta = input(
                      "\n Digite sua consulta aos dados em linguagem natural:\n> "
                  ).strip()

                 if not pergunta:
                     print("❌ Nenhuma pergunta foi informada.")
                     continue

                 sql_gerado = gerar_sql(pergunta, catalogo_texto,id_contrato)
                 validacao_sql = preparar_e_validar_sql(sql_gerado.sql)
                 if sql_gerado.sql:
                  print("\n" + "=" * 80)
                  print("\n📚 SQL GERADO:")
                  print("=" * 80)
                  print("\n ",sql_gerado.sql)
                 print("\n" + "=" * 80)
                 print("\n💡 EXPLICAÇÃO:")
                 print("=" * 80)
                 print("\n ",sql_gerado.explicacao)

                 if not validacao_sql[0]:
                  print("\n \n ❌ ", validacao_sql[1],validacao_sql[0])
                 else:
                  resultado_sql = executar_sql(validacao_sql[2])
                  print(f"\n Quantidade de registros: {len(resultado_sql)}")
                  display(resultado_sql)


               elif opcao == "0":
                # ---------------------------------------------------------
                # SAIR
                # ---------------------------------------------------------
                print("\n 🏁 Execução Encerrada")
                ctl_encerrar = True
                break

                # ---------------------------------------------------------
                # OPÇÃO INVÁLIDA
                # ---------------------------------------------------------
               else:
                print("\n ❌ Opção inválida.")
                print("Escolha uma opção entre 0 e 3.")


if __name__ == "__main__":
    main()

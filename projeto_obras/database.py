"""Acesso ao PostgreSQL/Supabase e construção do catálogo."""

import psycopg2
import pandas as pd
from psycopg2.extras import RealDictCursor

from .config import DB_CONFIG
from .config import REGRAS_NEGOCIO_CONSULTA, EXEMPLOS_CONSULTA

def get_connection():
    """Abre uma conexão PostgreSQL usando a configuração local."""
    return psycopg2.connect(**DB_CONFIG)

def obter_tabelas():

  sql = """
        SELECT
            table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """
  try:

   conn = get_connection()
   # Define o autocommit como False
   conn.autocommit = False
   cursor = conn.cursor(cursor_factory=RealDictCursor)
   cursor.execute(sql)
   tabelas = cursor.fetchall()

  except Exception as e:
    conn.rollback()
    print(f"Erro durante o processo de identificação de tabelas da base: {e}")

  finally:

    cursor.close()
    conn.close()
  return tabelas

def obter_colunas():

  sql = """
        SELECT
            table_name,
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
    """
  try:

   conn = get_connection()
   # Define o autocommit como False
   conn.autocommit = False
   cursor = conn.cursor(cursor_factory=RealDictCursor)
   cursor.execute(sql)
   colunas = cursor.fetchall()
  except Exception as e:
    conn.rollback()
    print(f"Erro durante o processo de identificação de tabelas da base: {e}")

  finally:

    cursor.close()
    conn.close()
  return colunas

def obter_pks():

  sql = """
   SELECT   tc.table_name,
            kcu.column_name,
            tc.constraint_name
     FROM information_schema.table_constraints tc
     JOIN information_schema.key_column_usage kcu
       ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
      AND tc.table_name = kcu.table_name
    WHERE tc.constraint_type = 'PRIMARY KEY'
      AND tc.table_schema = 'public'
 ORDER BY tc.table_name, kcu.ordinal_position;
    """

  try:

   conn = get_connection()
   # Define o autocommit como False
   conn.autocommit = False
   cursor = conn.cursor(cursor_factory=RealDictCursor)
   cursor.execute(sql)
   pks = cursor.fetchall()
  except Exception as e:
    conn.rollback()
    print(f"Erro durante o processo de identificação de tabelas da base: {e}")

  finally:

    cursor.close()
    conn.close()
  return pks

def obter_fks():

  sql = """
        SELECT
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS tabela_referenciada,
            ccu.column_name AS coluna_referenciada,
            tc.constraint_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
          ON ccu.constraint_name = tc.constraint_name
         AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema = 'public'
        ORDER BY tc.table_name;
    """

  try:

   conn = get_connection()
   # Define o autocommit como False
   conn.autocommit = False
   cursor = conn.cursor(cursor_factory=RealDictCursor)
   cursor.execute(sql)
   fks = cursor.fetchall()
  except Exception as e:
    conn.rollback()
    print(f"Erro durante o processo de identificação de tabelas da base: {e}")

  finally:

    cursor.close()
    conn.close()
  return fks

def construir_catalogo():

    tabelas = pd.DataFrame(obter_tabelas())
    colunas = pd.DataFrame(obter_colunas())
    pks = pd.DataFrame(obter_pks())
    fks = pd.DataFrame(obter_fks())

    catalogo = {
        "banco": "Supabase PostgreSQL",
        "schema_principal": "public",
        "tabelas": {}
    }

    for _, tabela in tabelas.iterrows():

        nome_tabela = tabela["table_name"]

        catalogo["tabelas"][nome_tabela] = {
            "schema": "public",
            "colunas": {},
            "chaves_primarias": [],
            "chaves_estrangeiras": []
        }

    # ---------------------------
    # COLUNAS
    # ---------------------------

    for _, coluna in colunas.iterrows():

        tabela = coluna["table_name"]
        nome_coluna = coluna["column_name"]

        catalogo["tabelas"][tabela]["colunas"][nome_coluna] = {
            "tipo": coluna["data_type"],
            "nullable": coluna["is_nullable"],
            "default": coluna["column_default"]
        }

    # ---------------------------
    # PRIMARY KEYS
    # ---------------------------

    for _, pk in pks.iterrows():

        tabela = pk["table_name"]
        coluna = pk["column_name"]

        catalogo["tabelas"][tabela]["chaves_primarias"].append(
            coluna
        )

    # ---------------------------
    # FOREIGN KEYS
    # ---------------------------

    for _, fk in fks.iterrows():

        tabela = fk["table_name"]

        catalogo["tabelas"][tabela]["chaves_estrangeiras"].append({
            "coluna": fk["column_name"],
            "tabela_referenciada": fk["tabela_referenciada"],
            "coluna_referenciada": fk["coluna_referenciada"]
        })

    return catalogo

def catalogo_para_texto(catalogo):

    partes = []

    partes.append(
        "CATÁLOGO DO BANCO DE DADOS\n"
    )

    for tabela, info in catalogo["tabelas"].items():

        partes.append(f"\nTABELA: {tabela}")

        partes.append(
            f"SCHEMA: {info['schema']}"
        )

        if info["chaves_primarias"]:
            partes.append(
                "PRIMARY KEY: "
                + ", ".join(info["chaves_primarias"])
            )

        partes.append("COLUNAS:")

        for coluna, dados in info["colunas"].items():

            linha = (
                f"- {coluna} "
                f"(tipo={dados['tipo']}, "
                f"nullable={dados['nullable']})"
            )

            if "exemplos" in dados:
                linha += (
                    f", exemplos={dados['exemplos']}"
                )

            partes.append(linha)

        if info["chaves_estrangeiras"]:

            partes.append("RELACIONAMENTOS:")

            for fk in info["chaves_estrangeiras"]:

                partes.append(
                    f"- {fk['coluna']} → "
                    f"{fk['tabela_referenciada']}."
                    f"{fk['coluna_referenciada']}"
                )

    return "\n".join(partes)

def validar_dados_contrato(codigo_contrato: str):
    """
    Verifica se contrato cadastrado, valida o nome do cliente.
    """
    try:
        # Busca o registro na tabela 'contratos'
        response = (supabase.table("Contrato")
            .select("id_contrato","nome_cliente")
            .eq("codigo_contrato", codigo_contrato)
            .execute()
        )

        contratos = response.data

        # 1. Valida se o contrato existe
        if not contratos:
          print(f"\n ❌Código de Obra/Contrato não Cadastrado: '{codigo_contrato}'")
          return


    except Exception as e:
        print(f"\n ❌ Erro ao verificar contrato: {str(e)}")
        return
    return contratos

def validar_relatorio_processado(id_contrato, nome_relatorio: str):

    """
    Verifica se o relatório já foi processado para evitar duplicidade de despesas na base de dados.
    """

    valido = True
    erros = []

    try:
        #verifica se o relatório já foi processado para evitar duplicidade de despesas na base de dados
        response = (supabase.table("Relatorio")
            .select("id_relatorio","dta_processamento","num_relatorio")
            .eq("id_contrato", id_contrato)
            .eq("nome_relatorio", nome_relatorio)
            .execute()
        )

        relatorios =  response.data

        if relatorios:
          print(f"\n ❌ Relatório de Prestação de Contas processado anteriomente (Número: '{relatorios[0]["num_relatorio"]}' | Data: '{relatorios[0]["dta_processamento"]}')")
          return False

    except Exception as e:
       print(f"\n ❌ Erro ao verificar relatorio: {str(e)}")
       return  False

    return True

def salvar_relatorio(dados_relatorio: dict, id_contrato: int, nome_relatorio: str):
    """
    Salva dados do relatório de forma atômica no Supabase/PostgreSQL usando o padrão
    nativo do Python. Em caso de qualquer erro, é executado ROLLBACK total.
    """

    conn = None
    cursor = None

    try:
        # 2. Conecta ao banco e inicia a transação explícita
        conn = get_connection()
        conn.autocommit = False  # Desativa o commit automático
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # -------------------------------------------------------------
        # STEP 1: Insere na tabela 'Relatorio'
        # -------------------------------------------------------------
        sql_relatorio = """
            INSERT INTO "Relatorio" (
                nome_relatorio, num_relatorio, dta_envio, valor_total_materiais,
                valor_administracao_material, valor_administracao_servico,
                des_administracao_servico, total_a_pagar, id_contrato
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_relatorio;
        """
        data_envio = dados_relatorio.get('data_envio')
        if data_envio == '':
            data_envio = None
        else:
           data_envio =  converter_para_ymd(data_envio)

        valores_relatorio = (
            nome_relatorio,
            dados_relatorio.get('numero_relatorio'),
            data_envio,
            dados_relatorio.get('valor_total_materiais'),
            dados_relatorio.get('valor_administracao_material'),
            dados_relatorio.get('valor_administracao_servico'),
            dados_relatorio.get('des_administracao_servico'),
            dados_relatorio.get('total_a_pagar'),
            id_contrato
        )
        cursor.execute(sql_relatorio, valores_relatorio)
        id_relatorio = cursor.fetchone()["id_relatorio"]

        # -------------------------------------------------------------
        # STEP 2: Insere na tabela 'Despesa' (se houver)
        # -------------------------------------------------------------
        itens_despesas = dados_relatorio.get("itens_quadro_resumo", [])
        if itens_despesas:
            sql_despesa = """
                INSERT INTO "Despesa" (
                    numero_nf_recibo, dta_despesa, nome_emitente, vlr_despesa,
                    des_aplicacao, des_categoria, id_relatorio, cod_status_comprovacao
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """
            for item in itens_despesas:
                data_despesa = item.get("data")
                if data_despesa == '':
                    data_despesa = None
                else:
                    data_despesa  =  converter_para_ymd(data_despesa)

                valores_despesa = (
                    item.get("numero_nf"),
                    data_despesa,
                    item.get("emitente"),
                    item.get("valor"),
                    item.get("aplicacao_material"),
                    item.get("categoria_insumo"),
                    id_relatorio,
                    'PENDENTE'
                )
                cursor.execute(sql_despesa, valores_despesa)

        # -------------------------------------------------------------
        # STEP 3: Insere comprovantes e seus itens (se houver)
        # -------------------------------------------------------------
        comprovantes = dados_relatorio.get("lista_notas_fiscais", [])
        if comprovantes:
            sql_comprovante = """
                INSERT INTO "Comprovante Despesa" (
                    num_documento, nome_emitente, cnpj_cpf_emitente, nome_remetente,
                    cnpj_cpf_remetente, dta_emissao, valor_total, chave_acesso,
                    categoria_comprovante, id_relatorio
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id_comprovante;
            """

            sql_item_comprovante = """
                INSERT INTO "Item Comprovante Despesa" (
                    id_comprovante_despesa, codigo, descricao, unidade, quantidade, vlr_unitario, vlr_total
                ) VALUES (%s, %s, %s, %s, %s, %s,%s);
            """

            for comprovante in comprovantes:
                data_emissao = comprovante.get("data_emissao")
                if data_emissao == '':
                    data_emissao = None
                else:
                    data_emissao = converter_para_ymd(data_emissao)

                valores_comprovante = (
                    comprovante.get("numero_documento"),
                    comprovante.get("emitente_nome"),
                    comprovante.get("emitente_cnpj_cpf"),
                    comprovante.get("remetente_nome"),
                    comprovante.get("remetente_cnpj_cpf"),
                    data_emissao,
                    comprovante.get("valor_total_nota"),
                    comprovante.get("chave_acesso"),
                    comprovante.get("categoria_comprovante"),
                    id_relatorio
                )
                cursor.execute(sql_comprovante, valores_comprovante)
                id_comprovante = cursor.fetchone()["id_comprovante"]

                # Insere itens deste comprovante
                itens_comprovantes = comprovante.get("itens", [])
                for item_comp in itens_comprovantes:
                    valores_item_comp = (
                        id_comprovante,
                        item_comp.get("codigo"),
                        item_comp.get("descricao"),
                        item_comp.get("unidade"),
                        item_comp.get("quantidade"),
                        item_comp.get("valor_unitario"),
                        item_comp.get("valor_total")
                    )
                    cursor.execute(sql_item_comprovante, valores_item_comp)

        # -------------------------------------------------------------
        # STEP 4: Confirma a transação inteira se tudo correu bem
        # -------------------------------------------------------------
        conn.commit()
        print(f"✅ Sucesso! Relatório ", dados_relatorio.get('numero_relatorio')," e todas as suas dependências foram salvos.")
        return id_relatorio

    except Exception as e:
        # -------------------------------------------------------------
        # STEP 5: ROLLBACK se qualquer comando falhar no meio do caminho
        # -------------------------------------------------------------
        if conn:
            conn.rollback()
        print(f"❌ Erro na inserção. ROLLBACK executado (nada foi salvo no banco). Detalhe: {e}")
        raise e

    finally:
        # -------------------------------------------------------------
        # STEP 6: Garante o fechamento da conexão e cursor
        # -------------------------------------------------------------
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def conciliar_comprovantes_despesas(limiar_similaridade_doc):
  """Executa a conciliação baseada em similaridade de texto, valores e proximidade de datas.
  :param limiar_similaridade_doc: Nota mínima (0-100) para aceitar o nome do emitente.
  """
  conexao = get_connection()
  # Define o autocommit como False
  conexao.autocommit = False
  cursor = conexao.cursor(cursor_factory=RealDictCursor)


  try:
    # 1. Buscar comprovantes que NÃO estão associados a nenhuma despesa
    query_comprovantes = """
            SELECT c.*
            FROM public."Comprovante Despesa" c
            WHERE c.id_comprovante NOT IN (
                SELECT COALESCE(id_comprovante_despesa,0)
                FROM public."Despesa") ;
        """
    cursor.execute(query_comprovantes)
    comprovantes_nao_associados = cursor.fetchall()

    # 2. Buscar despesas com status PENDENTE
    query_despesas = """
            SELECT *
            FROM public."Despesa"
            WHERE cod_status_comprovacao = 'PENDENTE'
              AND id_comprovante_despesa IS NULL ;
        """
    cursor.execute(query_despesas)
    despesas_pendentes = cursor.fetchall()

    # 3. Cruzamento e Análise de Similaridade e Regras de Negócio
    for desp in despesas_pendentes:
      melhor_match = None
      maior_pontuacao = 0


      num_nf_desp = normalizar_texto(desp["numero_nf_recibo"])
      emitente_desp = normalizar_texto(desp["nome_emitente"])
      valor_desp = desp["vlr_despesa"]
      data_desp = desp["dta_despesa"]

      relatorio_desp = desp.get(
          "id_relatorio"
      )  # Caso exista a coluna no comprovante

      #print("Despesa:", desp)

      for i, comp in enumerate(comprovantes_nao_associados):
        #print("Comprovante  Indice:",i)
        dif_valor = 0
        similaridade_doc = 0
        similaridade_emitente = 0
        similaridade_valor = 0
        similaridade_data = 0
        diferenca_dias = 0


        num_doc_comp = normalizar_texto(comp["num_documento"])
        emitente_comp = normalizar_texto(comp["nome_emitente"])
        valor_comp = comp["valor_total"]
        data_comp = comp["dta_emissao"]


        # Critério 1: Número do documento/NF (alta exigência)
        # Se as duas informações forem números, devem ser iguais
        if num_nf_desp.isdigit() and num_doc_comp.isdigit():
         similaridade_doc = fuzz.ratio(num_doc_comp, num_nf_desp)
         if similaridade_doc != 100: continue
        else:
         similaridade_doc = limiar_similaridade_doc
        #print(" #1 Similaridade Doc:",similaridade_doc,num_nf_desp,num_doc_comp)

        # Critério 2: Validação de Valores (tolerância de até 90 centavos por arredondamentos)
        if valor_comp is not None and valor_desp is not None:
          #print(valor_comp)
          #print(valor_desp)
          dif_valor = abs(valor_comp - valor_desp)
          #print("Diferença Valor:",dif_valor)
          if dif_valor > 0.99: continue
          simililaridade_valor = (100-dif_valor)
          #print("#2 similaridade valor:",simililaridade_valor)
          #print(valor_comp)
          #print(valor_desp)

        # Critério 3: Nome do emitente (usando token_sort_ratio para ordem de palavras)
        similaridade_emitente = fuzz.ratio(emitente_comp, emitente_desp)
        #print("#3 similaridade_emitente :",similaridade_emitente,limiar_similaridade_doc)
        #print(emitente_comp)
        #print(emitente_desp)
        if similaridade_emitente < limiar_similaridade_doc: continue

        # Critério 4: Validação de
        #print("Data Comprovante",data_desp)
        #print("Data Despesa",data_comp)
        # Despesas mais próximas terão peso maior na avaliação
        # e a diferença total não pode ultrapassar o limite configurado
        #print("#4.1 Diferença Dias: ",diferenca_dias,similaridade_data)
        diferenca_dias = abs((data_desp - data_comp).days)
        match diferenca_dias:
           case d if d <= 15:
             similaridade_data = 100
           case d if d <= 30:
            similaridade_data = 80
           case d if d <= 60:
            similaridade_data = 60
           case _:
            similaridade_data = 40

        #print("#4.2 Diferença Dias: ",diferenca_dias,similaridade_data)


        # Pontuação consolidada para desempate caso haja mais de um match viável
        pontuacao_total = (simililaridade_valor * 0.9) + (similaridade_doc * 0.1) + (similaridade_emitente * 0.5) + (similaridade_data * 0.6)

        #print("Pontuação Total :",pontuacao_total, maior_pontuacao, "Indice", i)
        if pontuacao_total > maior_pontuacao:
           maior_pontuacao = pontuacao_total
           melhor_match = comp
           #print("Melhor Match encontrado Dentro:", melhor_match["id_comprovante"],desp["id_despesa"])

      if melhor_match:
        #print("Melhor Match encontrado:", melhor_match["id_comprovante"],desp["id_despesa"])
        # Comando para atualizar a tabela Despesa
        # Remove o registro de comprovante associado da lista
        del comprovantes_nao_associados[i]

        query_update = """
         UPDATE public."Despesa"
         SET  cod_status_comprovacao = 'CONCILIADO',
         id_comprovante_despesa = %s
         WHERE id_despesa = %s;"""

          # Executa a atualização cursor.execute(query_update)
        cursor.execute(query_update, (melhor_match["id_comprovante"],desp["id_despesa"]))
        conexao.commit()
  except Exception as e:
    conexao.rollback()
    print(f"Erro durante o processo de conciliação: {e}")
  finally:
    cursor.close()
    conexao.close()

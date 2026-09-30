"""Consultas em linguagem natural: Gemini -> SQL -> validação -> execução."""

import re
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from google import genai
from google.genai import types

from .config import SQL_LLM_MODEL, REGRAS_NEGOCIO_CONSULTA, EXEMPLOS_CONSULTA
from .config import CHAVE_API_GEMINI, DB_CONFIG
from .models import SQLGerado
from .database import construir_catalogo, catalogo_para_texto

def gerar_sql(pergunta, catalogo_texto, id_contrato):

    # Inicialização correta usando o novo SDK padrão 'google-genai' [1]
    client = genai.Client(api_key=CHAVE_API_GEMINI)

    prompt = f""" Você é um especialista em PostgreSQL e análise financeira
       de prestações de contas de condomínios. Sua tarefa é transformar a pergunta do usuário em SQL.

       IMPORTANTE: Caso a pergunta não seja satisfatória ou precisa, não gerar um SQL aleatório.
        Solicitar mais informações. retornar SQL = ''

     CATÁLOGO DO BANCO :  {catalogo_texto}

     REGRAS DE NEGÓCIO :  {REGRAS_NEGOCIO_CONSULTA}

     EXEMPLOS DE PERGUNTAS E RESPOSTAS: {EXEMPLOS_CONSULTA}

     PARAMETRO OBRIGATORIO: id_contrato = {id_contrato}

     PERGUNTA ALVO: {pergunta} """

    response = client.models.generate_content(

        model=SQL_LLM_MODEL,

        contents=prompt,

        config=types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
            response_schema=SQLGerado,
            max_output_tokens=2000
        )
    )

    return SQLGerado.model_validate_json(response.text)

def preparar_e_validar_sql(sql: str) -> tuple[bool, str, str]:
    """
    Prepara e valida um SQL gerado por um LLM.

    Retorna:
        sql_preparado : SQL limpo, pronto para validação/execução
        valido        : True se o SQL for permitido, False caso contrário
        mensagem      : descrição do resultado da validação
    """
    # ---------------------------------------------------------
    # 1. Verifica se o SQL foi informado
    # ---------------------------------------------------------

    sql_preparado = sql.strip()
    if not sql_preparado or not sql_preparado.strip():
        return False, "Nenhum SQL foi informado.", ""

    # --------------------------------
    # 2. Verifica se começa com SELECT
    # ---------------------------------------------------------

    if not re.match(r"^SELECT\b", sql_preparado, re.IGNORECASE):
       return (
           False,
          "SQL bloqueado: somente comandos SELECT são permitidos.",
           sql_preparado
       )

    # ---------------------------------------------------------
    # 3. Comandos proibidos
    # ---------------------------------------------------------

    comandos_proibidos = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "TRUNCATE",
        "CREATE",
        "REPLACE",
        "MERGE",
        "GRANT",
        "REVOKE",
        "EXEC",
        "EXECUTE",
        "CALL"
    ]

    padrao_proibido = (
        r"\b(" + "|".join(comandos_proibidos) + r")\b"
    )

    encontrado = re.search(
        padrao_proibido,
        sql_preparado,
        re.IGNORECASE
    )

    if encontrado:
        comando = encontrado.group(1).upper()

        return (
            False,
            f"SQL bloqueado: comando proibido encontrado ({comando}).",
            sql_preparado
        )

    # ---------------------------------------------------------
    # 4. SQL aprovado
    # ---------------------------------------------------------

    return (
        True,
        "SQL válido: somente SELECT.",
        sql_preparado
    )

def executar_sql(sql: str):
    """
    Recebe o SQL e executa no banco e mostra o resultado.

    Em caso de erro:
        - imprime o SQL gerado;
        - imprime a mensagem de erro;
        - retorna None.

    Em caso de sucesso:
        - imprime o SQL;
        - imprime o resultado;
        - retorna um DataFrame.
    """

    registros = []

    # --------------------------------------------------
    # 1. Executa o SQL no Supabase
    # --------------------------------------------------

    try:
        # Conecta ao banco e inicia a transação explícita
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False  # Desativa o commit automático
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(sql)

        print(f" \n ✅ Sucesso! Consulta realizada com sucesso.")
        # Dados retornados
        registros = cursor.fetchall()
        resultado = pd.DataFrame(registros)

    except Exception as e:
        print(f"\n ❌ Erro  ao executar SQL: {e}")
        return

    finally:

      return resultado

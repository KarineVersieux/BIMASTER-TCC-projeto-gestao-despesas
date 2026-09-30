"""Geração do relatório consolidado em PDF."""

import os
import psycopg2
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether
)
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import String, Rect

from .config import DB_CONFIG

class NumberedCanvas(canvas.Canvas):
    """
    Canvas de duas passagens. Renderiza o rodapé de forma elástica,
    sabendo o total exato de páginas antes de fechar o PDF.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#4A5568"))
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)

        # Desenha a linha horizontal do rodapé
        self.line(40, 40, 572, 40)

        # Paginação dinâmica
        texto_pagina = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(572, 25, texto_pagina)
        self.drawString(40, 25, "Relatório Despesas Obra Cassiano/Karine")
        self.restoreState()

class GeradorRelatorioCompleto:
    """Módulo responsável por renderizar a estrutura visual do PDF via ReportLab."""
    def __init__(self, caminho_saida: str):
        # 532 pontos de largura útil (612 total - 80 de margens laterais)
        self.doc = SimpleDocTemplate(
            caminho_saida, pagesize=letter,
            leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=55
        )
        self.story = []
        self.styles = getSampleStyleSheet()
        self.cor_primaria = colors.HexColor("#1A365D")
        self.cor_secundaria = colors.HexColor("#2B6CB0")

    def adicionar_cabecalho(self, titulo: str, subtitulo: str, data_emissao: str = None):
        """Adiciona título, cliente/subtítulo e data de emissão."""
        estilo_t = ParagraphStyle(
            'DocTitle', parent=self.styles['Heading1'],
            fontSize=22, leading=26,
            textColor=self.cor_primaria,
            spaceAfter=4
        )
        estilo_s = ParagraphStyle(
            'DocSubtitle', parent=self.styles['Normal'],
            fontSize=11, leading=14,
            textColor=colors.HexColor("#4A5568"),
            spaceAfter=3
        )
        estilo_data = ParagraphStyle(
            'DocDate', parent=self.styles['Normal'],
            fontSize=9, leading=12,
            textColor=colors.HexColor("#718096"),
            spaceAfter=12
        )

        self.story.append(Paragraph(titulo, estilo_t))
        self.story.append(Paragraph(subtitulo, estilo_s))

        if data_emissao:
            self.story.append(
                Paragraph(f"Data de emissão: {data_emissao}", estilo_data)
            )

        self.story.append(Spacer(1, 8))

    @staticmethod
    def formatar_moeda(valor):
        """Formata números no padrão monetário brasileiro: R$ 1.234,56."""
        try:
            numero = float(valor)
            texto = f"{numero:,.2f}"
            texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
            return f"R$ {texto}"
        except (TypeError, ValueError):
            return str(valor)

    def construir_tabela_sql(self, colunas: list, linhas_dados: list):
        dados_formatados = []

        # Estilo para as células de dados
        estilo_celula = ParagraphStyle(
            'TableCell', parent=self.styles['Normal'],
            fontSize=8,
            leading=9,
            textColor=colors.black, alignment=0
        )

        # Linha de títulos (Cabeçalho)
        linha_cabecalho = [
            Paragraph(
                f"<b>{col}</b>",
                ParagraphStyle(
                    'H', parent=self.styles['Normal'],
                    fontSize=8,
                    leading=9,
                    textColor=colors.whitesmoke, alignment=1
                )
            )
            for col in colunas
        ]
        dados_formatados.append(linha_cabecalho)

        # Converte dados do SQL para Paragraph.
        # A coluna "Valor" passa a ser exibida como moeda brasileira.
        indice_valor = next(
            (i for i, col in enumerate(colunas)
             if str(col).strip().lower() == "valor"),
            None
        )

        for linha in linhas_dados:
            nova_linha = []
            for i, celula in enumerate(linha):
                valor_exibicao = (
                    self.formatar_moeda(celula)
                    if i == indice_valor
                    else str(celula)
                )
                nova_linha.append(
                    Paragraph(valor_exibicao, estilo_celula)
                )
            dados_formatados.append(nova_linha)

        largura_disponivel = 532
        larguras = [largura_disponivel / len(colunas)] * len(colunas)

        tabela = Table(
            dados_formatados,
            colWidths=larguras,
            repeatRows=1
        )
        tabela.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.cor_secundaria),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#F7FAFC")]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        self.story.append(tabela)
        self.story.append(Spacer(1, 20))

    def construir_tabela_pizza(self, dados: list, categorias: list):
        """Tabela de duas colunas com o resumo das despesas por categoria."""
        estilo_celula = ParagraphStyle(
            'PizzaTableCell',
            parent=self.styles['Normal'],
            fontSize=9,
            leading=11
        )
        estilo_cabecalho = ParagraphStyle(
            'PizzaTableHeader',
            parent=self.styles['Normal'],
            fontSize=9,
            leading=11,
            textColor=colors.whitesmoke,
            alignment=1
        )

        dados_tabela = [[
            Paragraph('<b>Categoria</b>', estilo_cabecalho),
            Paragraph('<b>Valor</b>', estilo_cabecalho)
        ]]

        for categoria, valor in zip(categorias, dados):
            dados_tabela.append([
                Paragraph(str(categoria), estilo_celula),
                Paragraph(self.formatar_moeda(valor), estilo_celula)
            ])

        tabela = Table(
            dados_tabela,
            colWidths=[370, 162],
            repeatRows=1
        )
        tabela.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.cor_secundaria),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#F7FAFC")]),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))

        self.story.append(tabela)
        self.story.append(Spacer(1, 20))

    def construir_grafico_barras_comparativo(self, series_dados: list, categorias: list):
        desenho = Drawing(532, 200)
        grafico = VerticalBarChart()
        grafico.x = 45
        grafico.y = 25
        grafico.height = 140
        grafico.width = 460
        grafico.data = series_dados
        grafico.categoryAxis.categoryNames = categorias

        cor_metas = colors.HexColor("#006A6A")
        grafico.bars[0].fillColor = cor_metas

        grafico.categoryAxis.labels.fontName = 'Helvetica'
        grafico.categoryAxis.labels.fontSize = 8
        grafico.categoryAxis.labels.dy = -10

        valor_maximo = max(
            [max(sublista) for sublista in series_dados]
        ) if series_dados else 100

        grafico.valueAxis.valueMin = 0
        grafico.valueAxis.valueMax = valor_maximo * 1.35
        grafico.valueAxis.valueStep = valor_maximo / 4

        legenda = Legend()
        legenda.x = 360
        legenda.y = 190
        legenda.dx = 8
        legenda.dy = 8
        legenda.fontName = 'Helvetica'
        legenda.fontSize = 9
        legenda.boxAnchor = 'nw'
        legenda.columnMaximum = 1
        legenda.colorNamePairs = [(cor_metas, 'Despesas')]

        desenho.add(grafico)
        desenho.add(legenda)
        self.story.append(desenho)
        self.story.append(Spacer(1, 20))

    def construir_grafico_pizza(self, dados: list, labels_fatias: list, legendas: list):
        # Área maior para o gráfico, evitando que a pizza e a legenda fiquem comprimidas.
        desenho = Drawing(535, 235)

        pizza = Pie()
        pizza.x = 35
        pizza.y = 30
        pizza.width = 190
        pizza.height = 190
        pizza.data = dados

        # Exibe o percentual diretamente sobre cada fatia da pizza.
        total = sum(dados) or 1
        pizza.labels = [
            f"{(valor / total) * 100:.1f}%"
            for valor in dados
        ]
        pizza.simpleLabels = True

        # Posicionamento e aparência dos percentuais.
        pizza.slices.labelRadius = 1.35
        pizza.slices.fontName = "Helvetica-Bold"
        pizza.slices.fontSize = 8
        pizza.slices.fontColor = colors.black

        pizza.slices.strokeColor = colors.white
        pizza.slices.strokeWidth = 1

        paleta = [
            "#1A365D", "#2B6CB0", "#4299E1", "#38A169",
            "#68D391", "#D69E2E", "#DD6B20", "#C05621",
            "#805AD5", "#718096", "#319795", "#B83280"
        ]

        for i in range(len(pizza.data)):
            pizza.slices[i].fillColor = colors.HexColor(
                paleta[i % len(paleta)]
            )

        from reportlab.graphics.shapes import String, Rect

        x_legenda = 280
        y_legenda = 205
        espacamento = 16

        for i, valor in enumerate(dados):
            nome = (
                str(legendas[i])
                if i < len(legendas)
                else f"Categoria {i + 1}"
            )
            cor = colors.HexColor(paleta[i % len(paleta)])
            y_item = y_legenda - (i * espacamento)

            desenho.add(Rect(
                x_legenda, y_item - 6, 8, 8,
                fillColor=cor,
                strokeColor=colors.white,
                strokeWidth=0.5
            ))

            desenho.add(String(
                x_legenda + 14,
                y_item - 4,
                f"{nome} ({self.formatar_moeda(valor)})",
                fontName="Helvetica",
                fontSize=7.5,
                fillColor=colors.HexColor("#2D3748")
            ))

        desenho.add(pizza)
        self.story.append(desenho)
        self.story.append(Spacer(1, 10))

    def salvar(self):
        self.doc.build(self.story, canvasmaker=NumberedCanvas)

class GerenciadorArmazenamentoLocal:
  """Garante a integridade das pastas no servidor e cria caminhos com nomes únicos (Timestamp)."""
  def __init__(self, pasta_base: str = "relatorios_gerados"):
    self.pasta_destino = os.path.abspath(pasta_base)
    if not os.path.exists(self.pasta_destino):
        os.makedirs(self.pasta_destino)

  def gerar_caminho_unico(self, prefixo_nome: str = "relatorio") -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"{prefixo_nome}_{timestamp}.pdf"
    return os.path.join(self.pasta_destino, nome_arquivo)

def executar_pipeline_relatorio(nome_cliente: str, id_contrato: str, contrato: str):
    # Instancia gerenciador e gera nome único baseado na data e hora atual
    armazenamento = GerenciadorArmazenamentoLocal(
        pasta_base="outputs/relatorios_despesas"
    )
    caminho_pdf = armazenamento.gerar_caminho_unico(
        prefixo_nome="consolidado"
    )

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Query 1: Registros estruturados da Tabela Despesas Sem Comprovação
        query_despesas_sem_comprovacao = f"""
             select r.num_relatorio, d.dta_despesa, d.vlr_despesa,
             d.des_categoria, d.nome_emitente, d.des_aplicacao, d.numero_nf_recibo
               from public."Despesa" d, public."Relatorio" r
              where d.cod_status_comprovacao = 'PENDENTE'
                and r.id_contrato = {id_contrato}
           ORDER BY 1,2,3
        """

        cursor.execute(query_despesas_sem_comprovacao)
        registros_tabela_1 = cursor.fetchall()
        colunas_tabela_1 = [
            "Relatório", "Data", "Valor", "Categoria", "Emissor",
            "Aplicação", "Número NF/DOC"
        ]

        # Query 2: Registros estruturados da Tabela Comprovantes Não Associados
        query_comprovantes_sem_despesa = f"""
             SELECT r.num_relatorio, c.dta_emissao, c.categoria_comprovante,c.valor_total,
             c.num_documento,c.nome_emitente
            FROM public."Comprovante Despesa" c, public."Relatorio" r
            WHERE c.id_relatorio = r.id_relatorio
            AND r.id_contrato = {id_contrato}
            AND c.id_comprovante NOT IN (
                SELECT COALESCE(id_comprovante_despesa,0)
                FROM public."Despesa");
        """
        cursor.execute(query_comprovantes_sem_despesa)
        registros_tabela_2 = cursor.fetchall()
        colunas_tabela_2 = [
            "Relatório","Data", "Categoria","Valor",
            "Número NF/DOC", "Emissor"
        ]

        # Query 3: Total de Despesas Por Categoria
        query_despesas_categoria = f"""
            select d.des_categoria, sum(d.vlr_despesa)
            from public."Despesa" d, public."Relatorio" r
            where r.id_relatorio = d.id_relatorio
            and r.id_contrato = {id_contrato}
            group by d.des_categoria
            order by 1
        """
        cursor.execute(query_despesas_categoria)
        dados_pizza_brutos = cursor.fetchall()

        dados_pizza = [float(row[1]) for row in dados_pizza_brutos]
        labels_pizza = [
            f"{row[0]} ({row[1]})" for row in dados_pizza_brutos
        ]
        legendas_pizza = [str(row[0]) for row in dados_pizza_brutos]
        categorias_pizza = [str(row[0]) for row in dados_pizza_brutos]

        # Query 4: Dados temporais para o Gráfico de Barras Despesas por Mês
        query_despesas_mes = f"""
            select to_char(d.dta_despesa,'YYYY-MM') as ano_mes,
                   sum(d.vlr_despesa)
            from public."Despesa" d, public."Relatorio" r
            where r.id_relatorio = d.id_relatorio
            and r.id_contrato = {id_contrato}
            group by ano_mes
            order by 1
        """
        cursor.execute(query_despesas_mes)

        dados_barras_brutos = cursor.fetchall()
        meses_barras = [row[0] for row in dados_barras_brutos]
        serie_totais = [float(row[1]) for row in dados_barras_brutos]
        dados_barras = [serie_totais]

        cursor.close()
        conn.close()

    except Exception as e:
        print(f" \n ❌ Erro: {e}. ")
        return

    # Processamento e montagem do fluxo do PDF
    print(f"Compilando documento estruturado em: {caminho_pdf}")
    relatorio = GeradorRelatorioCompleto(caminho_pdf)

    # ==========================================================
    # PÁGINA 1 — CABEÇALHO + GRÁFICO DE PIZZA + TABELA
    # ==========================================================
    data_emissao = datetime.now().strftime("%d/%m/%Y")

    relatorio.adicionar_cabecalho(
        "Relatório de Consolidação de Despesas de Obra",
        "Contrato: " + contrato + " - " + nome_cliente,
        "Data Emissão: " + data_emissao
    )

    relatorio.story.append(
        Paragraph(
            "<b>Consolidação de Despesas por Categoria</b>",
            relatorio.styles['Heading3']
        )
    )
    relatorio.story.append(Spacer(1, 30))

    relatorio.construir_grafico_pizza(
        dados_pizza,
        labels_pizza,
        legendas_pizza
    )

    # Tabela com exatamente duas colunas: Categoria e Valor
    relatorio.construir_tabela_pizza(
        dados_pizza,
        categorias_pizza
    )

    # ==========================================================
    # PÁGINA 2 — GRÁFICO MENSAL
    # ==========================================================
    relatorio.story.append(PageBreak())

    relatorio.story.append(
        Paragraph(
            "<b>Despesas Por Mês</b>",
            relatorio.styles['Heading3']
        )
    )
    relatorio.story.append(Spacer(1, 10))
    relatorio.construir_grafico_barras_comparativo(
        dados_barras,
        meses_barras
    )

    # ==========================================================
    # PÁGINA SEGUINTE — DESPESAS PENDENTES
    # ==========================================================
    relatorio.story.append(PageBreak())
    relatorio.adicionar_cabecalho(
        "Despesas Pendentes de Comprovação",
        "Lista de Despesas"
    )
    relatorio.construir_tabela_sql(
        colunas_tabela_1,
        registros_tabela_1
    )

    # ==========================================================
    # PÁGINA SEGUINTE — COMPROVANTES NÃO VINCULADOS
    # ==========================================================
    relatorio.story.append(PageBreak())
    relatorio.adicionar_cabecalho(
        "Comprovantes Não Vinculados a Despesas",
        "Lista de Comprovantes"
    )
    relatorio.construir_tabela_sql(
        colunas_tabela_2,
        registros_tabela_2
    )

    relatorio.salvar()
    print("\n ✅ Concluído! Relatório gerado com sucesso.")

    return caminho_pdf

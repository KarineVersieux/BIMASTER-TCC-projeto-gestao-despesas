<div align="justify">
  
# Sistema de Consolidação e Consulta de Despesas de Obras

#### Aluno: Karine Versieux Magalhaes
#### Matrícula: 231.100.986 Turmas (23.2 e 24.1)

#### Orientador: Leonardo Alfredo Forero Mendoza


---

Trabalho de Conclusão de Curso [BI MASTER - BUSINESS INTELLIGENCE MASTER - SISTEMAS INTELIGENTES DE APOIO À DECISÃO EM NEGÓCIOS](https://ica.ele.puc-rio.br/cursos/mba-bi-master/).

- Código Disponível na pasta /projeto_obras

- Documentação Disponível na /pasta docs

- Exemplos de relatórios de entrada e saída disponiveis na pasta /exemplos

---

### Resumo

O projeto tem como finalidade o desenvolvimento de um sistema para apoiar a gestão de relatórios de despesas de obras de engenharia civil, automatizando a extração de informações presentes em relatórios períodicos apresentados em formato PDF, a persistência estruturada dos dados, a conciliação entre despesas e comprovantes, a geração de relatórios consolidados e a realização de consultas ao banco de dados relacional por meio de linguagem natural. Os relatórios periódicos de despesas apresentam um quadro-resumo e podem conter imagens de notas fiscais, recibos, orçamentos, comprovantes de transferência e outros documentos relacionados aos gastos.

O problema é caracterizado pela necessidade de conferir manualmente os valores dos custos, a taxa de administração, a existência dos documentos comprobatórios e a ocorrência de documentos referentes a períodos anteriores. Também é necessária uma visão consolidada das despesas por período e categoria.

**Princípio Central da Solução**

O projeto desenvolvido em Python, sem interface gráfica, combina LLMs em tarefas que exigem interpretação de documentos para extração de dados e processamento de linguagem natural para a geração de consultas SQL. Inclui também processos determinísticos para validação, persistência, conciliação e geração de relatórios.

### 1. Introdução

Empresa de engenharia civil, através de relatórios semanais no formato pdf, realiza comprovação de custos com aquisição de materiais e contratação de serviços para que o cliente faça o reembolso dos valores pagos pela empresa e também do pagamento da taxa de administração, percentual de 15%, sobre todos os custos do período. Cada relatório é composto por um quadro resumo e imagens digitalizadas de notas fiscais, recibos, orçamentos, comprovantes de transferência e outros documentos relacionados ap pagamento das despesas.

O processo de conferência manual dos custos totais, taxas de administração e validação da emissão de nota fiscal ou outro tipo de comprovante consome tempo e é suscetível a erros. Além disto, comprovantes de despesas de um período, frequentemente, são enviadas anexos ao relatório de períodos posteriores, gerando a necessidade de controle de comprovações pendentes. O cliente possui mais de um contrato com a empresa de engenharia civil. Cada obra dura em média 12 meses, sendo gerados aproximadamente 48 relatórios por obra. 
                                
O sistema possui como objetivo automatizar os processos acima citados e fornecer visão consolidada dos custos por períodos e/ou categorias. 

**Objetivos Específicos:**

  * Processar relatórios PDF contendo quadro-resumo de despesas e documentos comprobatórios.

  * Extrair informações estruturadas dos documentos.

  * Persistir os dados em banco de dados relacional.

  * Evitar o reprocessamento de relatórios já cadastrados.

  * Associar comprovantes a despesas. 

  * Gerar relatório consolidado em PDF.

  * Permitir consultas ao banco de dados por meio de linguagem natural.

### 2. Modelagem

A solução desenvolvida está organizada como uma aplicação modular Python. A função principal apresenta ao usuário três operações de negócio: processamento de relatórios, geração de relatório consolidado e consulta de dados em linguagem natural. A execução é orientada por um código de obra/contrato, informado pelo usuário, que identifica o cliente e restringe quais informações devem ser processadas e apresentadas. 

A figura apresenta a arquitetura da solução e os fluxos implementados:

<p align="center">
  <img src="docs/Arquitetura e Fluxos Solucao.png" width="850">
</p>

**Módulos Desenvolvidos:**
* main.py: Interface principal, seleção do contrato e orquestração das três opções de uso.
* config.py: Variáveis de ambiente, credenciais, modelos LLM, regras de negócio e exemplos.
* processing.py: Processamento dos PDFs, normalização de textos e datas e extração via LLM.
* models.py: Modelos Pydantic para representar dados extraídos e respostas estruturadas do LLM.
* database.py: Conexão, catálogo do banco, persistência, validações e conciliação.
* consultas.py: Geração de SQL via LLM, validação e execução no PostgreSQL.
* report.py: Construção do relatório consolidado em PDF e geração de gráficos.

As principais decisões de implementação são:

**Extração de dados de arquivos PDF: LLM Multimodal**

A solução adotada utiliza um LLM com capacidade multimodal para interpretar diretamente os arquivos PDF dos relatórios de despesas. O modelo recebe o documento completo, incluindo textos, tabelas e imagens dos comprovantes, e realiza a extração das informações relevantes para o sistema.  A escolha dessa abordagem deve-se ao fato dos relatórios não serem constituídos apenas por texto estruturado. Eles contêm quadro-resumo, tabelas e imagens de notas fiscais, recibos, comprovantes de transferência, Pix e outros documentos, exigindo interpretação conjunta de diferentes elementos do PDF. O LLM não realiza cálculos ou consistência entre os dados dos diversos relatórios. As operações determinísticas ficam sob controle da aplicação. 

Na geração de saída do modelo foi definido um esquema estruturado baseado em Pydantic o que reduz a necessidade de interpretar posteriormente uma resposta textual livre e estabelece um contrato de dados entre o modelo de linguagem e a aplicação Python. 

Os dados extraídos são armazenados em um banco de dados relacional Postgress armazenado na plataforma open-source Supabase.

**Consultas em linguagem natural — Text-to-SQL**

A solução implementada permite que o usuário consulte os dados armazenados no banco de dados utilizando linguagem natural, sem necessidade de conhecer a estrutura ou escrever diretamente comandos SQL. O processo utiliza um LLM para transformação de linguagem natural em SQL (Text-to-SQL), entretanto, a geração da consulta não ocorre de forma livre: o modelo recebe informações estruturadas sobre o banco, regras de negócio, exemplos de consultas e o identificador do contrato selecionado. O sistema constrói automaticamente um catálogo do banco de dados a partir do PostgreSQL. Em relação aos exemplos são apresentadas perguntas e respectivas consultas SQL, funcionando como referências para orientar o modelo na geração de novas consultas.

A execução produz uma estrutura SQL que passa por uma segunda camada de validação antes da execução. O objetivo de garantir que somente expressões de consultas (SELECT) são geradas, impedindo a execução de comandos não desejados como remoção de dados, alteração de estruturas de tabelas e etc.  

**Independência em relação ao modelo:**

Uma decisão arquitetural importante foi manter o modelo utilizado como parâmetro de configuração, por meio das variáveis EXTRACT_LLM_MODEL e SQL_LLM_MODEL.

**Geração de relatório consolidado:**

Para a geração automática de relatório consolidado, a partir dos dados armazenados no banco de dados, optou-se pela definição prévia de estrutura e formatação em PDF. Esta decisão permite que as informações consolidadas sejam apresentadas diretamente ao usuário em uma saída adequada para análise e conferência, reduzindo a necessidade de manipulação manual dos dados após o processamento.

### 3. Resultados

A implementação do sistema permitiu avaliar, na prática, a utilização de modelos de linguagem em duas etapas distintas do processo: a interpretação dos relatórios PDF e a geração de consultas SQL a partir de perguntas em linguagem natural. Para essas atividades, foram avaliados modelos da família Google Gemini, especificamente o Gemini 3.5 Flash-Lite, Gemini 3.5 Flash e Gemini 3.8 Flash. Os testes realizados apresentaram desempenho satisfatório nas duas categorias de tarefas, tanto na extração e estruturação das informações dos relatórios quanto na geração de consultas SQL. Considerando a qualidade dos resultados obtidos, a disponibilidade dos modelos por meio da assinatura já existente e menores custos de utilização da solução, optou-se pela utilização do Gemini 3.5 Flash-Lite. 

Foram utilizados, como dados de entrada para os testes, 26 relatórios semanais de despesas, permitindo avaliar o processamento de documentos reais dentro do escopo definido para o sistema. Em todos os relatórios processados, as informações necessárias foram extraídas e estruturadas de acordo com o formato estabelecido nos modelos de dados da aplicação, demonstrando a adequação da solução para a etapa de interpretação e estruturação dos documentos.

Para avaliar a funcionalidade de consultas em linguagem natural, foram testadas 20 consultas SQL, abrangendo situações que envolvem tanto dados provenientes de uma única tabela quanto consultas que requerem o relacionamento entre múltiplas tabelas do banco de dados. Os resultados demonstraram desempenho satisfatório na tradução dos termos utilizados nas perguntas para os elementos correspondentes da estrutura relacional, incluindo a identificação das tabelas, campos e relacionamentos necessários para a elaboração das consultas.

### 4. Conclusões

O desenvolvimento do sistema demonstrou a viabilidade da aplicação de técnicas de processamento de documentos e modelos de linguagem para apoiar a gestão de relatórios de despesas de obras. A solução desenvolvida permitiu automatizar etapas que anteriormente dependiam de análise e organização manual, desde a interpretação dos relatórios periódicos em formato PDF até a estruturação e persistência das informações em um banco de dados relacional.
A utilização de modelos de linguagem mostrou-se adequada tanto para a extração de informações dos documentos quanto para a geração de consultas SQL a partir de perguntas em linguagem natural. Na etapa de processamento dos relatórios, a capacidade multimodal dos modelos possibilitou trabalhar diretamente com documentos que combinam textos, tabelas e imagens de comprovantes. Na etapa de consultas, a utilização do catálogo estruturado do banco de dados, associado às regras de negócio e à validação das consultas geradas, permitiu estabelecer uma interface mais acessível para a obtenção de informações armazenadas no sistema.
Os testes realizados com diferentes modelos da família Google Gemini apresentaram desempenho satisfatório para as tarefas propostas. Diante dos resultados obtidos, da disponibilidade dos modelos no ambiente utilizado e da necessidade de equilibrar qualidade e custo de utilização, foi priorizada a utilização do modelo que apresentou desempenho adequado com menor custo, demonstrando que a escolha do modelo pode ser orientada pelas características específicas da aplicação, e não necessariamente pela utilização do modelo de maior capacidade.
Outro aspecto relevante foi a combinação entre componentes baseados em modelos de linguagem e mecanismos determinísticos implementados em Python. Enquanto os modelos foram empregados em atividades que envolvem interpretação de documentos e compreensão de linguagem natural, operações como validação dos dados, persistência, regras de negócio, controle do contexto da obra e validação das consultas SQL permaneceram sob responsabilidade da aplicação. Essa separação contribuiu para aumentar a previsibilidade e o controle sobre as operações realizadas pelo sistema.
A geração automática de relatórios consolidados e já formatados também contribuiu para aproximar a solução das necessidades práticas do processo de gestão. Dessa forma, os dados extraídos e armazenados deixam de constituir apenas informações disponíveis no banco de dados e passam a ser apresentados em uma saída organizada, adequada para análise, conferência e acompanhamento das despesas e respectivos comprovantes.

A arquitetura adotada mostrou-se suficiente para atender aos objetivos definidos neste trabalho, não sendo necessária, para o escopo desenvolvido, a utilização de mecanismos mais complexos, como arquiteturas multiagente ou sistemas de RAG. As etapas do processo possuem objetivos bem definidos e utilizam fontes de informação conhecidas, permitindo que uma arquitetura modular, combinada ao uso de modelos de linguagem e mecanismos tradicionais de processamento, atendesse às necessidades identificadas.

Como limitações, destaca-se que a avaliação realizada esteve concentrada no contexto e nos documentos utilizados no desenvolvimento do sistema, não constituindo um benchmark abrangente entre diferentes modelos de linguagem. Além disso, documentos com estruturas muito diferentes das utilizadas nos testes podem exigir ajustes nos prompts, nos modelos de dados ou nas regras de processamento. Como trabalhos futuros, podem ser consideradas a ampliação dos tipos de documentos processados, a realização de avaliações quantitativas mais extensas da qualidade da extração e da geração de consultas SQL, a incorporação de mecanismos de recuperação de informações para grandes volumes de documentos históricos e a evolução da solução para fluxos que demandem maior autonomia na execução de tarefas. Também poderá ser avaliada a utilização de diferentes modelos de linguagem conforme o nível de complexidade de cada operação, buscando continuamente o equilíbrio entre desempenho, custo e confiabilidade.

Assim, conclui-se que o sistema desenvolvido atingiu o propósito de estabelecer uma solução integrada para apoiar o gerenciamento das despesas de obras, combinando automação de documentos, armazenamento estruturado, conciliação de informações, geração de relatórios e consultas em linguagem natural. A principal contribuição do trabalho está na integração desses recursos em um fluxo único.

---

Matrícula: 231.100.986 Turmas (23.2 e 24.1) 

</div>

Pontifícia Universidade Católica do Rio de Janeiro

Curso de Pós Graduação *Business Intelligence Master*

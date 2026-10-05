# Sistema de Consolidação e Consulta de Despesas de Obras

#### Aluno: [Karine Versieux Magalhaes](https://github.com/link_do_github)
#### Orientador: [Nome Sobrenome](https://github.com/link_do_github).


---

Trabalho de Conclusão de Curso [BI MASTER - BUSINESS INTELLIGENCE MASTER - SISTEMAS INTELIGENTES DE APOIO À DECISÃO EM NEGÓCIOS](https://ica.ele.puc-rio.br/cursos/mba-bi-master/).

<!-- para os links a seguir, caso os arquivos estejam no mesmo repositório que este README, não há necessidade de incluir o link completo: basta incluir o nome do arquivo, com extensão, que o GitHub completa o link corretamente -->
- [Link para o código](https://github.com/link_do_repositorio). <!-- caso não aplicável, remover esta linha -->

- [Link para a monografia](https://link_da_monografia.com). <!-- caso não aplicável, remover esta linha -->

---

### Resumo

O projeto tem como finalidade o desenvolvimento de um sistema para apoiar a gestão de relatórios de despesas de obras, automatizando a extração de informações presentes em relatórios períodicos apresentados em formato PDF, a persistência estruturada dos dados, a conciliação entre despesas e comprovantes, a geração de relatórios consolidados e a realização de consultas ao banco de dados relacional por meio de linguagem natural. Os relatórios periódicos de despesas apresentam um quadro-resumo e podem conter imagens de notas fiscais, recibos, orçamentos, comprovantes de transferência e outros documentos relacionados aos gastos.

O problema é caracterizado pela necessidade de conferir manualmente os valores dos custos, a taxa de administração, a existência dos documentos comprobatórios e a ocorrência de documentos referentes a períodos anteriores. Também é necessária uma visão consolidada das despesas por período e categoria.

**Princípio Central da Solução**

O projeto desenvolvido em Python, sem interface gráfica, combina LLMs em tarefas que exigem interpretação de documentos para extração de dados e processamento de linguagem natural para a geração de consultas SQL e processos determinísticos para validação, persistência, conciliação e geração de relatórios.

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

A solução adotada utiliza um LLM com capacidade multimodal para interpretar diretamente os arquivos PDF dos relatórios de despesas. O modelo recebe o documento completo, incluindo textos, tabelas e imagens dos comprovantes, e realiza a extração das informações relevantes para o sistema.  A escolha dessa abordagem deve-se ao fato dos relatórios não serem constituídos apenas por texto estruturado. Eles contêm quadro-resumo, tabelas e imagens de notas fiscais, recibos, comprovantes de transferência, Pix e outros documentos, exigindo interpretação conjunta de diferentes elementos do PDF. O LLM não realiza cálculos ou consitência entre os diversos relatórios. As operações determinísticas ficam sob controle da aplicação. 

Na geração de saída do modelo, foi definido um esquema estruturado baseado em Pydantic o que reduz a necessidade de interpretar posteriormente uma resposta textual livre e estabelece um contrato de dados entre o modelo de linguagem e a aplicação Python. 




**Consultas em linguagem natural — Text-to-SQL**



Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin pulvinar nisl vestibulum tortor fringilla, eget imperdiet neque condimentum. Proin vitae augue in nulla vehicula porttitor sit amet quis sapien. Nam rutrum mollis ligula, et semper justo maximus accumsan. Integer scelerisque egestas arcu, ac laoreet odio aliquet at. Sed sed bibendum dolor. Vestibulum commodo sodales erat, ut placerat nulla vulputate eu. In hac habitasse platea dictumst. Cras interdum bibendum sapien a vehicula.

Proin feugiat nulla sem. Phasellus consequat tellus a ex aliquet, quis convallis turpis blandit. Quisque auctor condimentum justo vitae pulvinar. Donec in dictum purus. Vivamus vitae aliquam ligula, at suscipit ipsum. Quisque in dolor auctor tortor facilisis maximus. Donec dapibus leo sed tincidunt aliquam.

### 3. Resultados

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin pulvinar nisl vestibulum tortor fringilla, eget imperdiet neque condimentum. Proin vitae augue in nulla vehicula porttitor sit amet quis sapien. Nam rutrum mollis ligula, et semper justo maximus accumsan. Integer scelerisque egestas arcu, ac laoreet odio aliquet at. Sed sed bibendum dolor. Vestibulum commodo sodales erat, ut placerat nulla vulputate eu. In hac habitasse platea dictumst. Cras interdum bibendum sapien a vehicula.

Proin feugiat nulla sem. Phasellus consequat tellus a ex aliquet, quis convallis turpis blandit. Quisque auctor condimentum justo vitae pulvinar. Donec in dictum purus. Vivamus vitae aliquam ligula, at suscipit ipsum. Quisque in dolor auctor tortor facilisis maximus. Donec dapibus leo sed tincidunt aliquam.

### 4. Conclusões

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin pulvinar nisl vestibulum tortor fringilla, eget imperdiet neque condimentum. Proin vitae augue in nulla vehicula porttitor sit amet quis sapien. Nam rutrum mollis ligula, et semper justo maximus accumsan. Integer scelerisque egestas arcu, ac laoreet odio aliquet at. Sed sed bibendum dolor. Vestibulum commodo sodales erat, ut placerat nulla vulputate eu. In hac habitasse platea dictumst. Cras interdum bibendum sapien a vehicula.

Proin feugiat nulla sem. Phasellus consequat tellus a ex aliquet, quis convallis turpis blandit. Quisque auctor condimentum justo vitae pulvinar. Donec in dictum purus. Vivamus vitae aliquam ligula, at suscipit ipsum. Quisque in dolor auctor tortor facilisis maximus. Donec dapibus leo sed tincidunt aliquam.

---

Matrícula: 231.100.986 Turmas (23.2 e 24.1) 

Pontifícia Universidade Católica do Rio de Janeiro

Curso de Pós Graduação *Business Intelligence Master*

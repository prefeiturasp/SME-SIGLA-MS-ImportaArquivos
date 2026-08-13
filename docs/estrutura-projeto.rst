Estrutura do Projeto
=======================

Visão da árvore principal
-----------------------------

.. code-block:: text

   importacao-arquivos/
   ├── apps/
   │   ├── core/
   │   ├── importa_arquivos/
   │   └── exporta_arquivo/
   ├── config/
   ├── docs/
   ├── media/
   ├── requirements/
   ├── manage.py
   ├── Makefile
   └── pyproject.toml

Pasta ``apps/``
-------------------

``apps/core/``
~~~~~~~~~~~~~~~~~

**O que faz:** concentra recursos compartilhados entre os demais apps.

**Para que serve:** evitar duplicação dos campos comuns a todo modelo de
domínio do projeto.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Arquivo
     - Função
   * - ``models.py``
     - Define ``BaseModel``, classe abstrata com ``uuid``, ``criado_em`` e
       ``atualizado_em``, herdada por todos os modelos dos outros dois apps

**Exemplo:** todo modelo de importação ou exportação tem um identificador
público estável (``uuid``) independente da chave primária interna, o que
facilita expor esse identificador via API sem acoplar ao auto-incremento do
banco.

``apps/importa_arquivos/``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**O que faz:** recebe, valida e distribui arquivos de habilitados, vagas,
lotes de classificação e resultados de convocação (PRODAM).

**Para que serve:** ponto único de entrada de arquivos externos no pipeline
de convocação, com validação e rastreabilidade de erro centralizadas.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Camada / arquivo
     - Função
   * - ``models/``
     - ``ImportacaoArquivoHabilitado``, ``ImportacaoArquivoVagas``,
       ``ImportacaoLotes``, ``ImportacaoEscolhas``,
       ``LayoutArquivoImportacao``, ``ImportacaoErro``, ``LogRequestHttp``
   * - ``repository.py``
     - Única camada autorizada a executar queries ORM sobre esses modelos
   * - ``services/``
     - Validação de CSV/TXT (``validacao_habilitados.py``,
       ``validacao_vagas.py``, ``importacao_lotes.py``), integração com
       MS-Candidatos/MS-Concursos/MS-Escolhas/PRODAM e registro de erros
       (``erros.py``)
   * - ``api/views/``
     - ViewSets DRF, um arquivo por recurso

**Exemplo:** ``ImportacaoArquivoHabilitado`` guarda o histórico de cada
tentativa de importação de um CSV de habilitados — arquivo enviado,
quantidade de registros processados, status e concurso relacionado.

``apps/exporta_arquivo/``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**O que faz:** consulta dados já persistidos em outros microsserviços e
gera arquivos de exportação nos formatos ERGON/SIGPEC.

**Para que serve:** desacoplar os sistemas legados de folha/RH da
Prefeitura do formato de dados interno da SIGLA.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Camada / arquivo
     - Função
   * - ``models/``
     - ``CabecalhoExportacaoLote``, ``ExportacaoLote``,
       ``ExportacaoCandidatosProcesso``, ``ExportacaoVagasProcesso``,
       ``ExportacaoVagasSigpec``
   * - ``repository.py``
     - Única camada autorizada a executar queries ORM sobre esses modelos
   * - ``services/``
     - Geração do conteúdo de cada tipo de arquivo de exportação
   * - ``api/views/``
     - ViewSets DRF, um arquivo por recurso (``base.py`` concentra o
       comportamento comum de criação/listagem/download)
   * - ``management/commands/``
     - ``criar_cabecalho_exportacao_lote`` — cria/recria o cabeçalho padrão
       de exportação de lote

**Exemplo:** ``ExportacaoLote`` guarda o histórico de cada exportação de
lote gerada, incluindo o conteúdo do arquivo produzido e o status
(``SUCESSO``, ``ATENCAO`` ou ``ERRO``).

Pasta ``config/``
---------------------

Configuração do projeto Django.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Arquivo
     - Função
   * - ``settings.py``
     - Configurações de produção/desenvolvimento
   * - ``settings_test.py``
     - Configurações usadas pela suíte de testes (banco SQLite em memória)
   * - ``urls.py``
     - Roteamento raiz, healthcheck e schema OpenAPI/Swagger
   * - ``wsgi.py``
     - Ponto de entrada WSGI

Pasta ``requirements/``
---------------------------

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Arquivo
     - Propósito
   * - ``base.txt``
     - Dependências de produção: Django, DRF, PostgreSQL, sigla-sdk,
       validate-docbr, pydantic, entre outras
   * - ``local.txt``
     - Inclui ``base.txt`` e adiciona ferramentas de desenvolvimento e teste
       (pytest, ruff, black, mypy, pre-commit, sphinx)
   * - ``production.txt``
     - Inclui ``base.txt`` e adiciona o servidor WSGI (gunicorn)

Pasta ``docs/``
-------------------

Documentação Sphinx do módulo — este mesmo material, gerado em HTML via
``make docs``.

Arquivos na raiz
--------------------

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Arquivo
     - Função
   * - ``manage.py``
     - Utilitário de linha de comando do Django
   * - ``Makefile``
     - Atalhos de desenvolvimento (``test``, ``lint``, ``format``, ``docs``, etc.)
   * - ``pyproject.toml``
     - Configuração de ferramentas (ruff, black, mypy, isort)
   * - ``.pre-commit-config.yaml``
     - Hooks de lint/format/type-check executados antes de cada commit

API — endpoints principais (referência)
-------------------------------------------

Todas as rotas abaixo estão sob o prefixo ``/api/v1/``.

.. list-table:: importa_arquivos
   :header-rows: 1
   :widths: 50 50

   * - Rota
     - Recurso
   * - ``importacao-arquivo/habilitados/``
     - Importação de habilitados
   * - ``importacao-arquivo/vagas/``
     - Importação de vagas
   * - ``importacao-escolhas/``
     - Importação de escolhas (via PRODAM)
   * - ``importacao/lotes/``
     - Importação de lotes de classificação
   * - ``layouts/``
     - Layouts configuráveis de importação

.. list-table:: exporta_arquivo
   :header-rows: 1
   :widths: 50 50

   * - Rota
     - Recurso
   * - ``exportacao/lote/``
     - Exportação de lote (formato ERGON/SIGPEC)
   * - ``exportacao/candidatos-processo/``
     - Exportação de candidatos por processo
   * - ``exportacao/vagas-processo/``
     - Exportação de vagas por processo
   * - ``exportacao/vagas-sigpec/``
     - Exportação de vagas (formato SIGPEC)
   * - ``exportacao/cabecalho-lote/``
     - Cabeçalho configurável de exportação de lote

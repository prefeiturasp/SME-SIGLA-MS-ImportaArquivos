Regras de Negócio
==================

Importação de arquivos (``importa_arquivos``)
------------------------------------------------

Tipos de importação
~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Recurso
     - Origem do dado
     - O que faz
   * - Habilitados
     - Upload de CSV
     - Importa candidatos habilitados em um concurso e os envia ao MS-Candidatos
   * - Vagas
     - Upload de CSV
     - Importa vagas ofertadas por unidade escolar e as envia ao MS-Escolhas
   * - Lotes
     - Upload de TXT
     - Atualiza dados de classificação (lote SIGPEC) dos candidatos já habilitados
   * - Escolhas
     - Consulta à PRODAM
     - Busca resultado de convocação/ingresso na PRODAM e envia ao MS-Escolhas

Status do processo de importação
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Todas as importações seguem o mesmo ciclo de vida:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Status
     - Significado
   * - ``PENDENTE``
     - Registro criado, ainda não processado
   * - ``PROCESSANDO``
     - Em andamento (usado explicitamente pelo fluxo de Escolhas)
   * - ``CONCLUIDO``
     - Arquivo validado e dados enviados com sucesso ao microsserviço de destino
   * - ``ERRO``
     - Falha de validação do arquivo ou falha ao enviar os dados; detalhes
       registrados em ``ImportacaoErro``

**Regras importantes sobre status:**

- Qualquer exceção durante o processamento marca a importação como ``ERRO``
  e cria um registro em ``ImportacaoErro`` (via ``registrar_erro``), vinculado
  ao registro de importação por ``GenericForeignKey`` — o mesmo mecanismo de
  erro serve os quatro tipos de importação.
- O detalhe do erro fica disponível para download em texto simples através
  da action ``erros/download`` de cada recurso (e também como JSON, via
  ``erros``, no caso de Escolhas).

Layout configurável (``LayoutArquivoImportacao``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As importações de Habilitados e Vagas não têm o formato de coluna fixo no
código: cada uma é validada contra um layout cadastrado (campo
``estrutura``, uma lista de definições de coluna — nome, campo de destino,
obrigatoriedade, ordem, tamanho). Isso permite ajustar o formato esperado do
arquivo sem alterar código, bastando recadastrar o layout do tipo
correspondente (``HABILITADOS`` ou ``VAGAS``). Se não existir layout
cadastrado para o tipo, a importação falha imediatamente.

Validações específicas
~~~~~~~~~~~~~~~~~~~~~~~~~

- **Habilitados**: CPF validado via ``validate_docbr``; e-mail validado por
  regex; data de nascimento no formato ``mm/dd/aaaa``; e-mails duplicados
  associados a CPFs diferentes são rejeitados; o código de cargo de cada
  candidato é conferido em tempo real contra os cargos válidos do concurso
  (consulta ao MS-Concursos) — se o concurso não existir ou a consulta
  falhar, a importação inteira é rejeitada.
- **Vagas**: cabeçalho do CSV comparado de forma estrita ao layout — tanto
  colunas faltantes quanto colunas extras invalidam o arquivo.
- **Lotes**: arquivo TXT com cabeçalho fixo
  (``LOTE;EMPRESA;VAGA;IDENTIFICACAO;CHAVE_INSCRITO;NUMFUNC;NUMVINC``); cada
  linha validada individualmente, e todos os erros de linha são agregados em
  uma única mensagem antes de rejeitar o arquivo.

Exportação de arquivos (``exporta_arquivo``)
------------------------------------------------

Status de exportação de lote (``StatusExportacao``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Status
     - O que dispara
   * - ``PENDENTE`` / ``PROCESSANDO``
     - Estados intermediários do fluxo
   * - ``SUCESSO``
     - Todos os candidatos do lote têm escolha registrada; arquivo ERGON/SIGPEC
       gerado e devolvido para download
   * - ``ATENCAO``
     - Existem candidatos do lote sem escolha registrada em MS-Escolhas; o
       arquivo devolvido lista os candidatos pendentes, em vez do lote final
   * - ``ERRO``
     - Falha ao consultar MS-Candidatos/MS-Escolhas ou outra falha de serviço;
       nenhum arquivo é persistido

Formato de exportação ERGON/SIGPEC
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

O arquivo de lote segue um formato de cabeçalho fixo, configurável via
``CabecalhoExportacaoLote`` (``@TABELA=``, ``@CHAVE=``, ``@SEPARADOR=``,
``@FORMATO DATA=``, ``@COLUNAS=``), seguido de uma linha por candidato com
número do lote, código SIGPEC, chave de inscrição, data no formato
``DD/MM/AAAA`` e um indicador de situação (``S`` para escolha registrada,
``N`` para não-escolha, ``R`` para reconvocação). O comando de gestão
``criar_cabecalho_exportacao_lote`` cria o cabeçalho padrão (formato
``[c_ERGON][PMSP_ESCOLHA_VAGA_SME][1.0]``); só pode existir um cabeçalho
ativo por vez, e recriar um novo com ``--force`` desativa o anterior.

Outras exportações
~~~~~~~~~~~~~~~~~~~~~

- **Candidatos por processo**: gera um arquivo delimitado por ``|`` com os
  dados cadastrais dos candidatos habilitados de um processo/cargo,
  ordenados por classificação de escolha.
- **Vagas por processo**: gera um arquivo delimitado por ``|`` com
  código de cargo, código EOL da unidade e quantidade de vagas definitivas e
  precárias.
- **Vagas SIGPEC**: mesma origem de dados de vagas, mas formatada no padrão
  SIGPEC (``;``, com cabeçalho ``@TABELA=[C_ERGON][PMSP_VAGAS_SME][1.0]``).

Auditoria
------------

Todos os modelos de ambos os apps são registrados via ``django-auditlog``
(campo ``history`` em cada modelo), garantindo histórico completo de
criação e alteração de cada registro de importação e exportação.

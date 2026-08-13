Visão Geral
===========

O que é este módulo?
---------------------

O **Módulo de Importação e Exportação de Arquivos** (MS-IMPORTA-ARQUIVOS) é o
microsserviço da SIGLA responsável por toda a troca de arquivos em lote do
pipeline de convocação de servidores da SME: recebe arquivos CSV/TXT enviados
pelas áreas de negócio e distribui os dados para os demais microsserviços, e
gera os arquivos de exportação exigidos pelos sistemas de folha de pagamento
(**ERGON**) e de gestão de pessoas (**SIGPEC**) da Prefeitura.

Ele é dividido em dois apps Django independentes:

- **importa_arquivos** — recebe e valida arquivos, encaminhando o conteúdo
  para os microsserviços responsáveis por persistir a informação de negócio.
- **exporta_arquivo** — consulta dados já persistidos nos demais
  microsserviços e gera arquivos de exportação nos formatos esperados por
  sistemas legados/externos.

Para que serve?
----------------

O fluxo de convocação de um concurso público passa por várias etapas —
publicação do resultado, habilitação dos candidatos, oferta de vagas,
escolha de unidade escolar — e cada uma dessas etapas historicamente é
alimentada por planilhas/arquivos vindos de sistemas externos ou preenchidos
manualmente pela área de negócio. Este módulo existe para que essa entrada e
saída de arquivos aconteça de forma **validada, rastreável e auditável**, sem
que cada microsserviço de domínio precise reimplementar sua própria lógica de
parsing de CSV/TXT.

Onde ele se encaixa no ecossistema SIGLA?
-------------------------------------------

Todas as integrações são feitas via HTTP, usando o cliente compartilhado
``sigla_sdk.http.api_client.http_client`` (autenticação por API Key entre
microsserviços).

.. list-table:: Integrações externas
   :header-rows: 1
   :widths: 25 20 55

   * - Sistema
     - Direção
     - Papel neste módulo
   * - MS-Candidatos
     - Envio
     - Recebe habilitados importados e atualizações de lote de classificação
   * - MS-Concursos
     - Consulta
     - Valida se um código de cargo pertence ao concurso informado
   * - MS-Escolhas
     - Envio
     - Recebe vagas ofertadas e escolhas de unidade (inclusive as vindas da PRODAM)
   * - PRODAM
     - Consulta
     - API externa da Prefeitura com o resultado de convocação/ingresso

Exemplo prático do dia a dia
-------------------------------

**Importando um arquivo de habilitados:**

1. A área de negócio faz upload de um CSV com os candidatos habilitados de
   um concurso via ``POST /api/v1/importacao-arquivo/habilitados/``.
2. O módulo valida o cabeçalho do arquivo contra o layout configurado
   (``LayoutArquivoImportacao``), e cada linha quanto a CPF, e-mail, data de
   nascimento e código de cargo (este último confirmado em tempo real junto
   ao MS-Concursos).
3. Se tudo estiver correto, os registros são enviados ao MS-Candidatos e a
   importação é marcada como ``CONCLUIDO``. Se algo falhar, ela é marcada
   como ``ERRO`` e o motivo fica disponível para download
   (``GET .../erros/download/``).

**Exportando um lote para o ERGON/SIGPEC:**

1. A área de negócio solicita a exportação de um lote via
   ``POST /api/v1/exportacao/lote/``.
2. O módulo busca os candidatos do lote no MS-Candidatos e a escolha de cada
   um no MS-Escolhas.
3. Se todos os candidatos tiverem escolha registrada, o arquivo no formato
   ERGON/SIGPEC é gerado e devolvido para download. Se algum candidato ainda
   não tiver escolha, a exportação é sinalizada como ``ATENCAO`` e a lista de
   pendências é devolvida em vez do arquivo final.

Fluxo resumido
----------------

.. code-block:: text

   Área de negócio                MS-IMPORTA-ARQUIVOS              Outros microsserviços
   ----------------                --------------------              ----------------------
   Upload de CSV/TXT  ──────────▶  Valida por layout
                                    configurado
                                        │
                                        ▼
                                   Envia dados validados ────────▶  MS-Candidatos / MS-Escolhas
                                        │
                                        ▼
                                   status = CONCLUIDO / ERRO

   Solicita exportação ─────────▶  Busca dados                ◀──  MS-Candidatos / MS-Escolhas
                                    Gera arquivo ERGON/SIGPEC
                                        │
                                        ▼
                                   status = SUCESSO / ATENCAO / ERRO

Tecnologias utilizadas (referência rápida)
----------------------------------------------

- **Django 5.2** + **Django REST Framework** — API HTTP
- **PostgreSQL** — banco de dados relacional
- **sigla-sdk** — cliente HTTP compartilhado entre microsserviços SIGLA
- **validate-docbr** — validação de CPF
- **pydantic** — validação estruturada das linhas do arquivo de lotes
- **django-auditlog** — histórico de alterações em todos os modelos

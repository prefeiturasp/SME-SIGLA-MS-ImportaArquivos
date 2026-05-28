import csv
import io
import logging

from importa_arquivos.models import LayoutArquivoImportacao
from importa_arquivos.services.exceptions import (
    ColunaCSVInvalidaException,
    LayoutNaoConfiguradoException,
    LeituraCSVException,
)

from .erros import captura_erros_importacao

logger = logging.getLogger(__name__)


@captura_erros_importacao(param_nome_obj="importacao_obj")
def validar_csv_vagas(
    arquivo, importacao_obj=None
) -> tuple[list[dict], list[dict]]:
    """
    Valida o arquivo CSV enviado para VAGAS contra o layout configurado
    e retorna a lista de registros (linhas) como dicts, além da estrutura do
    layout.
    """
    try:
        layout = LayoutArquivoImportacao.objects.filter(tipo="VAGAS").latest(
            "criado_em"
        )
    except LayoutArquivoImportacao.DoesNotExist:
        raise LayoutNaoConfiguradoException("Layout VAGAS não configurado.")  # noqa: B904

    estrutura: list[dict] = layout.estrutura or []
    colunas_esperadas = {
        item.get("coluna") for item in estrutura if isinstance(item, dict)
    }
    try:
        file_bytes = arquivo.read()
        arquivo.seek(0)
        text = file_bytes.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text), delimiter=";")
    except Exception as exc:
        raise LeituraCSVException(  # noqa: B904
            "Erro ao ler arquivo CSV",
            detalhes=f"Não foi possível ler o arquivo CSV. Detalhes: {str(exc)}",  # noqa: E501
        )

    headers_csv = set(reader.fieldnames or [])
    if headers_csv != colunas_esperadas:
        logger.warning(f"Colunas inválidas no CSV: {headers_csv}")
        colunas_esperadas - headers_csv
        colunas_sobrando = headers_csv - colunas_esperadas
        mensagem_erro = "Colunas inválidas no arquivo CSV"
        detalhes_lista = []

        if colunas_sobrando:
            detalhes_lista.append(
                f"Colunas não esperadas: {sorted(colunas_sobrando)}"
            )
        detalhes_lista.append(
            f"Colunas esperadas para Vagas: {sorted(colunas_esperadas)}"
        )
        detalhes_lista.append(f"Encontradas: {sorted(headers_csv)}")
        detalhes = " | ".join(detalhes_lista)

        raise ColunaCSVInvalidaException(mensagem_erro, detalhes=detalhes)

    registros: list[dict] = []
    for row in reader:
        if not isinstance(row, dict):
            continue
        registros.append(row)

    return registros, estrutura

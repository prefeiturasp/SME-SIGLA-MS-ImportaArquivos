"""Módulo services/validacao_habilitados."""

from __future__ import annotations

import csv
import io
import logging
from datetime import datetime
from typing import Any

from django.conf import settings
from validate_docbr import CPF  # type: ignore[import-not-found]

from importa_arquivos.models import LayoutArquivoImportacao
from importa_arquivos.services.api_concursos import ApiConcursosService
from importa_arquivos.services.exceptions import (
    ColunaCSVInvalidaException,
    LayoutNaoConfiguradoException,
    LeituraCSVException,
)

from .erros import captura_erros_importacao

logger = logging.getLogger(__name__)


def _resolver_colunas(estrutura: list[dict]) -> dict:
    """Percorre estrutura uma única vez e retorna as colunas mapeadas por.

    Args:
        estrutura: Definição de colunas do layout de importação.

    Returns:
        Dicionário com os dados processados.
    """

    def _eh_obrigatorio(valor: Any) -> Any:
        """Eh obrigatorio.

        Args:
            valor: Valor recebido para validação ou conversão.

        Returns:
            Valor convertido ou validado.
        """
        try:
            return str(valor).strip() in ("1", "true", "True")
        except Exception:
            return False

    email_col = None
    cpf_col = None
    dn_col = None
    cargo_col = None
    obrigatorias: list[str] = []
    for item in estrutura:
        if not isinstance(item, dict):
            continue
        coluna = item.get("coluna")
        campo = str(item.get("campo_payload", "")).lower()
        if coluna and _eh_obrigatorio(item.get("obrigatorio")):
            obrigatorias.append(coluna)
        if email_col is None and (
            campo == "email"
            or (
                isinstance(coluna, str)
                and coluna.lower() in ("email", "e-mail")
            )
        ):
            email_col = coluna
        if cpf_col is None and (
            campo == "cpf"
            or (isinstance(coluna, str) and coluna.lower() == "cpf")
        ):
            cpf_col = coluna
        if dn_col is None and (
            campo == "data_nascimento"
            or (
                isinstance(coluna, str)
                and coluna.lower() in ("datanascimento",)
            )
        ):
            dn_col = coluna
        if cargo_col is None and (
            campo == "codigo_cargo" or coluna == "Codigo_do_Cargo"
        ):
            cargo_col = coluna
    return {
        "email_col": email_col,
        "cpf_col": cpf_col,
        "dn_col": dn_col,
        "cargo_col": cargo_col,
        "obrigatorias": obrigatorias,
    }


def _validar_linhas(
    colunas: dict, registros: list[dict]
) -> dict[int, list[str]]:
    """Percorre registros uma única vez aplicando todas as validações.

    Args:
        colunas: Colunas mapeadas para validação.
        registros: Registros a serem validados.

    Returns:
        Dicionário com os erros encontrados por linha.
    """
    import re

    _re_email = re.compile("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$")
    _cpf_validator = CPF()
    obrigatorias = colunas["obrigatorias"]
    email_col = colunas["email_col"]
    cpf_col = colunas["cpf_col"]
    dn_col = colunas["dn_col"]
    erros_por_linha: dict[int, list[str]] = {}
    for idx, row in enumerate(registros, start=2):
        erros: list[str] = []
        faltantes = [
            col
            for col in obrigatorias
            if row.get(col) is None or str(row.get(col)).strip() == ""
        ]
        if faltantes:
            erros.append(
                "Campos obrigatórios vazios: "
                f"{', '.join(sorted(faltantes))}"
            )
        if email_col:
            valor_email = row.get(email_col)
            if (
                valor_email is not None
                and str(valor_email).strip() != ""
                and not _re_email.match(str(valor_email).strip())
            ):
                erros.append(f"Email inválido -> '{valor_email}'")
        if cpf_col:
            valor_cpf = row.get(cpf_col)
            if valor_cpf is not None and str(valor_cpf).strip() != "":
                digits = "".join(ch for ch in str(valor_cpf) if ch.isdigit())
                if not _cpf_validator.validate(digits):
                    erros.append(f"CPF inválido -> '{valor_cpf}'")
        if dn_col:
            valor_dn = row.get(dn_col)
            if valor_dn is not None and str(valor_dn).strip() != "":
                try:
                    datetime.strptime(str(valor_dn).strip(), "%m/%d/%Y")
                except Exception:
                    erros.append(
                        f"dataNascimento inválida -> '{valor_dn}' (esperado mm/dd/yyyy)"  # noqa: E501
                    )
        if erros:
            erros_por_linha[idx] = erros
    return erros_por_linha


def _validar_email_duplicado_por_cpf(
    colunas: dict, registros: list[dict]
) -> dict[int, list[str]]:
    """Valida e-mail duplicado vinculado a CPFs distintos.

    Args:
        colunas: Colunas mapeadas para validação.
        registros: Registros a serem validados.

    Returns:
        Dicionário com os erros encontrados por linha.
    """
    email_col = colunas.get("email_col")
    cpf_col = colunas.get("cpf_col")
    if not email_col or not cpf_col:
        return {}

    def _normalizar_email(valor: object) -> str:
        """Normaliza e-mail para comparação."""
        if valor is None:
            return ""
        return str(valor).strip().lower()

    def _normalizar_cpf(valor: object) -> str:
        """Normaliza CPF para comparação."""
        if valor is None:
            return ""
        s = str(valor).strip()
        if s == "":
            return ""
        return "".join(ch for ch in s if ch.isdigit())

    expected_cpf_por_email: dict[str, str] = {}
    erros_por_linha: dict[int, list[str]] = {}
    for idx, row in enumerate(registros, start=2):
        email_norm = _normalizar_email(row.get(email_col))
        if not email_norm:
            continue
        cpf_norm = _normalizar_cpf(row.get(cpf_col))
        if email_norm not in expected_cpf_por_email:
            expected_cpf_por_email[email_norm] = cpf_norm
            continue
        expected = expected_cpf_por_email[email_norm]
        if cpf_norm != expected:
            erros_por_linha.setdefault(idx, []).append(
                f"Email duplicado. CPF {cpf_norm} com o mesmo email que o CPF {expected}"  # noqa: E501
            )
    return erros_por_linha


def _validar_codigo_cargo(
    colunas: dict, registros: list[dict], codigos_cargo_concurso: set
) -> dict[int, list[str]]:
    """Valida Codigo_do_Cargo de cada linha do arquivo.

    Args:
        colunas: Colunas mapeadas para validação.
        registros: Registros a serem validados.
        codigos_cargo_concurso: Codigos cargo do concurso.

    Returns:
        Dicionário com os erros encontrados por linha.
    """
    cargo_col = colunas.get("cargo_col")
    if not cargo_col:
        return {}
    erros_por_linha: dict[int, list[str]] = {}
    for idx, row in enumerate(registros, start=2):
        valor = row.get(cargo_col)
        if valor is None or str(valor).strip() == "":
            erros_por_linha.setdefault(idx, []).append(
                "Codigo_do_Cargo não pode estar em branco"
            )
            continue
        try:
            codigo_int = int(str(valor).strip())
        except (ValueError, TypeError):
            erros_por_linha.setdefault(idx, []).append(
                f"Codigo_do_Cargo deve ser um número inteiro válido -> '{valor}'"  # noqa: E501
            )
            continue
        if codigo_int not in codigos_cargo_concurso:
            codigos_validos = ", ".join(
                str(c) for c in sorted(codigos_cargo_concurso)
            )
            erros_por_linha.setdefault(idx, []).append(
                f"Codigo_do_Cargo '{valor}' não possui relação com o concurso selecionado. Códigos válidos: {codigos_validos}"  # noqa: E501
            )
    return erros_por_linha


@captura_erros_importacao(param_nome_obj="importacao_obj")
def validar_csv_habilitados(
    arquivo: Any, importacao_obj: Any = None
) -> tuple[list[dict], list[dict]]:
    """Valida csv habilitados.

    Args:
        arquivo: Arquivo enviado para importação.
        importacao_obj: Registro de importação em andamento.

    Returns:
        Tupla com os objetos criados ou atualizados.

    Raises:
        ColunaCSVInvalidaException: Se tiver colunas inválidas.
        LayoutNaoConfiguradoException: Se não tiver layout configurado.
        LeituraCSVException: Se não conseguir ler o arquivo CSV.
    """
    try:
        layout = LayoutArquivoImportacao.objects.filter(
            tipo="HABILITADOS"
        ).latest("criado_em")
    except LayoutArquivoImportacao.DoesNotExist:
        raise LayoutNaoConfiguradoException(
            "Layout HABILITADOS não configurado."
        ) from None
    estrutura: list[dict] = layout.estrutura or []
    colunas_esperadas = {
        item.get("coluna") for item in estrutura if isinstance(item, dict)
    }
    try:
        file_bytes = arquivo.read()
        arquivo.seek(0)
        text = file_bytes.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
    except Exception as exc:
        raise LeituraCSVException(
            "Erro ao ler arquivo de Habilitados",
            detalhes=(
                "Não foi possível ler o arquivo CSV. " f"Detalhes: {exc!s}."
            ),
        ) from exc
    headers_csv = set(reader.fieldnames or [])
    if headers_csv != colunas_esperadas:
        logger.warning(f"Colunas inválidas no CSV: {headers_csv}")
        detalhes = f"Encontradas: {sorted(headers_csv)} | Esperadas: {sorted(colunas_esperadas)}"  # type: ignore[type-var]  # noqa: E501
        raise ColunaCSVInvalidaException(
            "Arquivo de Habilitados inválido", detalhes=detalhes
        )
    registros: list[dict] = []
    for row in reader:
        if isinstance(row, dict):
            registros.append(row)
    colunas = _resolver_colunas(estrutura)
    erros_linhas = _validar_linhas(colunas, registros)
    erros_email_duplicado = _validar_email_duplicado_por_cpf(
        colunas, registros
    )
    concurso_uuid = (
        str(importacao_obj.concurso_uuid)
        if importacao_obj and getattr(importacao_obj, "concurso_uuid", None)
        else None
    )
    codigos_cargo_concurso: set = set()
    if concurso_uuid:
        service = ApiConcursosService(
            base_url=settings.CONCURSOS_API_URL,
            timeout_seconds=getattr(settings, "CONCURSOS_API_TIMEOUT", 10),
        )
        codigos_cargo_concurso = service.obter_codigos_cargo_do_concurso(
            concurso_uuid
        )
    erros_cargo = _validar_codigo_cargo(
        colunas, registros, codigos_cargo_concurso
    )
    erros_agrupados: dict[int, list[str]] = {}
    for src in (erros_linhas, erros_email_duplicado, erros_cargo):
        for linha, msgs in src.items():
            erros_agrupados.setdefault(linha, []).extend(msgs)
    if erros_agrupados:
        mensagens = [
            f'Linha {linha}: {'; '.join(msgs)}'
            for linha, msgs in sorted(erros_agrupados.items())
        ]
        detalhes = " | ".join(mensagens)
        logger.error("Erros de validação no CSV de Habilitados: %s", detalhes)
        raise ColunaCSVInvalidaException(
            "Erros de validação encontrados", detalhes=detalhes
        )
    return (registros, estrutura)

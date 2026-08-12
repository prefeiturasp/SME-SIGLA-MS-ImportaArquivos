"""Módulo utils."""

from __future__ import annotations

from typing import Any

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 10


class CustomPagination(PageNumberPagination):
    """Representa CustomPagination."""

    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = "page_size"

    def get_paginated_response(self, data: Any) -> Any:
        """Retorna resposta paginada no formato padrão SIGLA."""
        assert self.page is not None
        assert self.request is not None
        return Response(
            {
                "links": {
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                },
                "count": self.page.paginator.count,
                "page": int(self.request.GET.get("page", DEFAULT_PAGE)),
                "page_size": int(
                    self.request.GET.get("page_size", self.page_size)
                ),
                "results": data,
            }
        )

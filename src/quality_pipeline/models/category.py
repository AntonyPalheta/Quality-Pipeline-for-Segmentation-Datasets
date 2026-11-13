
"""
Este módulo define o modelo Category, responsável por representar
uma categoria pertencente a um dataset de segmentação.

A classe armazena as informações básicas de uma categoria,
independentemente do domínio ou formato original do dataset.

A conversão dos dados de formatos externos, como COCO,
será responsabilidade dos parsers.
"""

from dataclasses import dataclass


@dataclass
class Category:
    """
    Representa uma categoria existente em um dataset.

    Attributes:
        id: Identificador único da categoria dentro do dataset.
        name: Nome da categoria.
        supercategory: Grupo mais abrangente ao qual a categoria
                       pertence. É opcional.
    """

    id: int
    name: str
    supercategory: str | None = None


"""
Este módulo define o modelo Dataset, responsável por representar
um conjunto completo de dados de segmentação.

A classe reúne imagens, categorias e anotações em uma estrutura
interna padronizada, independentemente do formato de origem.

Também permite armazenar metadados gerais associados ao dataset.

Os parsers serão responsáveis por interpretar os formatos externos,
como COCO e Ultralytics YOLO, e construir instâncias deste modelo.
"""

from dataclasses import dataclass, field

from .annotation import Annotation
from .category import Category
from .image import Image


@dataclass
class Dataset:
    """
    Representa um conjunto de dados de segmentação.

    Attributes:
        images: Lista de imagens pertencentes ao dataset.
        categories: Lista de categorias existentes no dataset.
        annotations: Lista de anotações associadas às imagens
                     e categorias.
        metadata: Dicionário com informações gerais do dataset,
                  quando disponíveis.
    """

    images: list[Image] = field(default_factory=list)
    categories: list[Category] = field(default_factory=list)
    annotations: list[Annotation] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)

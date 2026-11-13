
"""
Este módulo define a interface pública do pacote models.

Sua responsabilidade é disponibilizar os modelos e tipos de dados
para que possam ser importados diretamente pelo pacote models,
sem precisar indicar o arquivo individual de cada implementação.
"""

from .annotation import Annotation
from .bounding_box import BoundingBox
from .category import Category
from .image import Image
from .segmentation import (
    MaskSegmentation,
    PolygonSegmentation,
    Segmentation,
)


__all__ = [
    "Annotation",
    "BoundingBox",
    "Category",
    "Image",
    "MaskSegmentation",
    "PolygonSegmentation",
    "Segmentation",
]

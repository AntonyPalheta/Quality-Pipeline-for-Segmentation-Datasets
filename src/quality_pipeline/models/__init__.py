
"""
Este módulo define a interface pública do pacote models.

Sua responsabilidade é disponibilizar os modelos de dados
para que possam ser importados diretamente pelo pacote models,
sem precisar indicar o arquivo individual de cada classe.
"""

from .category import Category
from .image import Image


__all__ = [
    "Category",
    "Image",
]

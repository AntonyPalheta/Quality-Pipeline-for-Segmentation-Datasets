
"""
Este módulo define as representações internas de segmentação
utilizadas pelo Quality Pipeline.

São suportadas duas representações:

- PolygonSegmentation: representa a segmentação por meio de
  um ou mais polígonos com coordenadas em pixels.
- MaskSegmentation: representa uma máscara binária utilizando
  uma codificação RLE interna e independente do formato de origem.

O tipo Segmentation reúne essas representações e será utilizado
por outros modelos, como Annotation.
"""

from dataclasses import dataclass
from typing import TypeAlias


@dataclass
class PolygonSegmentation:
    """
    Representa uma segmentação composta por um ou mais polígonos.

    Cada polígono é uma lista de pontos (x, y), cujas coordenadas
    são expressas em pixels, relativas à imagem original.

    Attributes:
        polygons: Lista de polígonos. Cada polígono contém uma
                  sequência de pontos com coordenadas x e y.
    """

    polygons: list[list[tuple[float, float]]]


@dataclass
class MaskSegmentation:
    """
    Representa uma segmentação por meio de uma máscara binária.

    A máscara é armazenada utilizando uma codificação RLE interna,
    independente das codificações específicas dos formatos externos.

    Os valores representam sequências alternadas de pixels de fundo
    e de primeiro plano, começando sempre pelo fundo.

    A sequência percorre a máscara em ordem de linhas (row-major).

    Attributes:
        width: Largura da máscara em pixels.
        height: Altura da máscara em pixels.
        runs: Quantidades de pixels em sequências alternadas de
              fundo e primeiro plano. A soma deve corresponder
              ao total de pixels da máscara.
    """

    width: int
    height: int
    runs: tuple[int, ...]


# Representa os tipos de segmentação aceitos pelo modelo interno.
Segmentation: TypeAlias = PolygonSegmentation | MaskSegmentation


"""
Este módulo define o modelo BoundingBox, responsável por representar
uma caixa delimitadora associada a um objeto em uma imagem.

A representação interna utiliza coordenadas em pixels, com origem
no canto superior esquerdo da imagem.

Os parsers serão responsáveis por converter as representações
específicas de cada formato, como COCO e YOLO, para esse padrão.
"""

from dataclasses import dataclass


@dataclass
class BoundingBox:
    """
    Representa uma caixa delimitadora em uma imagem.

    As coordenadas são expressas em pixels e utilizam o canto
    superior esquerdo como ponto de origem.

    Attributes:
        x: Coordenada horizontal do canto superior esquerdo.
        y: Coordenada vertical do canto superior esquerdo.
        width: Largura da caixa delimitadora em pixels.
        height: Altura da caixa delimitadora em pixels.
    """

    x: float
    y: float
    width: float
    height: float

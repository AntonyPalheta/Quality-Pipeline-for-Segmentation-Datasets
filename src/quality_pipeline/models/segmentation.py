
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



@dataclass(frozen=True)
class MaskSegmentation:
    """
    Representa uma segmentação por meio de uma máscara binária.

    A máscara é armazenada utilizando uma codificação RLE interna,
    independente das codificações específicas dos formatos externos.

    A sequência percorre a máscara em ordem de linhas (row-major),
    começando sempre pela contagem de pixels de fundo.

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

    def __post_init__(self) -> None:
        """
        Verifica a integridade estrutural da representação RLE.

        Garante que as dimensões sejam positivas, que as contagens
        sejam inteiros não negativos e que a quantidade total de
        pixels representada corresponda às dimensões da máscara.

        A primeira contagem pode ser zero quando a máscara começa
        diretamente com pixels de primeiro plano. As contagens
        seguintes devem ser positivas para manter a representação
        em segmentos alternados sem sequências vazias.
        
        Raises:
            TypeError: Quando dimensões ou contagens possuem tipos
                       incompatíveis com a representação.
            ValueError: Quando dimensões ou sequências RLE são inválidas.
        """
        if (
            isinstance(self.width, bool)
            or not isinstance(self.width, int)
        ):
            raise TypeError("A largura da máscara deve ser um inteiro.")

        if (
            isinstance(self.height, bool)
            or not isinstance(self.height, int)
        ):
            raise TypeError("A altura da máscara deve ser um inteiro.")

        if self.width <= 0:
            raise ValueError("A largura da máscara deve ser positiva.")

        if self.height <= 0:
            raise ValueError("A altura da máscara deve ser positiva.")

        if not isinstance(self.runs, tuple):
            raise TypeError("A sequência RLE deve ser uma tupla.")

        if not self.runs:
            raise ValueError("A sequência RLE não pode estar vazia.")

        for index, run_length in enumerate(self.runs):
            if (
                isinstance(run_length, bool)
                or not isinstance(run_length, int)
            ):
                raise TypeError(
                    "Todas as contagens RLE devem ser inteiros."
                )

            if run_length < 0:
                raise ValueError(
                    "As contagens RLE não podem ser negativas."
                )

            if index > 0 and run_length == 0:
                raise ValueError(
                    "Somente a primeira contagem RLE pode ser zero."
                )

        expected_pixels = self.width * self.height
        represented_pixels = sum(self.runs)

        if represented_pixels != expected_pixels:
            raise ValueError(
                "A soma das contagens RLE deve corresponder "
                "à quantidade total de pixels da máscara. "
                f"Esperado: {expected_pixels}; "
                f"recebido: {represented_pixels}."
            )


# Representa os tipos de segmentação aceitos pelo modelo interno.
Segmentation: TypeAlias = PolygonSegmentation | MaskSegmentation

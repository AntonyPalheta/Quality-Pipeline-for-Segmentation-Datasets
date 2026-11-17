
"""
Este módulo contém os testes automatizados das representações
internas de segmentação.

Os testes verificam se PolygonSegmentation e MaskSegmentation
armazenam corretamente suas respectivas representações geométricas
e se ambas pertencem ao tipo Segmentation.
"""

import pytest
from quality_pipeline.models import (
    MaskSegmentation,
    PolygonSegmentation,
    Segmentation,
)

def test_polygon_segmentation_stores_multiple_polygons():
    """
    Verifica se PolygonSegmentation armazena corretamente
    uma segmentação composta por múltiplos polígonos.
    """
    polygons = [
        [
            (10.0, 20.0),
            (50.0, 20.0),
            (40.0, 60.0),
        ],
        [
            (80.0, 90.0),
            (100.0, 90.0),
            (90.0, 110.0),
        ],
    ]

    segmentation = PolygonSegmentation(polygons=polygons)

    assert segmentation.polygons == polygons
    assert isinstance(segmentation, Segmentation)


def test_mask_segmentation_stores_rle_representation():
    """
    Verifica se MaskSegmentation armazena corretamente
    as dimensões e a sequência RLE da máscara.
    """
    # Máscara binária 2x3:
    #
    # 0 1 1
    # 0 0 1
    #
    # Em ordem de linhas, a sequência é:
    # 0 1 1 0 0 1
    #
    # RLE: 1 pixel de fundo, 2 de objeto,
    # 2 de fundo e 1 de objeto.

    segmentation = MaskSegmentation(
        width=3,
        height=2,
        runs=(1, 2, 2, 1),
    )

    assert segmentation.width == 3
    assert segmentation.height == 2
    assert segmentation.runs == (1, 2, 2, 1)

    assert sum(segmentation.runs) == (
        segmentation.width * segmentation.height
    )

    assert isinstance(segmentation, Segmentation)


@pytest.mark.parametrize(
    ("width", "height"),
    [
        (0, 2),
        (-1, 2),
        (3, 0),
        (3, -2),
    ],
)
def test_mask_segmentation_rejects_non_positive_dimensions(
    width,
    height,
):
    """
    Verifica se a máscara rejeita dimensões iguais a zero
    ou valores negativos.
    """
    with pytest.raises(ValueError):
        MaskSegmentation(
            width=width,
            height=height,
            runs=(6,),
        )


@pytest.mark.parametrize(
    ("width", "height"),
    [
        (3.0, 2),
        (True, 2),
        (3, 2.0),
    ],
)
def test_mask_segmentation_rejects_non_integer_dimensions(
    width,
    height,
):
    """
    Verifica se as dimensões rejeitam valores que não sejam inteiros.
    """
    with pytest.raises(TypeError):
        MaskSegmentation(
            width=width,
            height=height,
            runs=(6,),
        )


@pytest.mark.parametrize(
    "runs",
    [
        (),
        (1, -1, 6),
        (1, 0, 5),
        (1, 2, 2),
    ],
)
def test_mask_segmentation_rejects_invalid_runs(runs):
    """
    Verifica se a máscara rejeita sequências RLE vazias,
    negativas, com segmentos vazios intermediários ou
    com quantidade total de pixels incorreta.
    """
    with pytest.raises(ValueError):
        MaskSegmentation(
            width=3,
            height=2,
            runs=runs,
        )


@pytest.mark.parametrize(
    "runs",
    [
        [1, 5],
        (1, 2.5, 2, 0.5),
        (True, 5),
    ],
)
def test_mask_segmentation_rejects_non_integer_runs(runs):
    """
    Verifica se a sequência RLE exige uma tupla de inteiros,
    sem aceitar valores booleanos como contagens.
    """
    with pytest.raises(TypeError):
        MaskSegmentation(
            width=3,
            height=2,
            runs=runs,
        )


def test_mask_segmentation_accepts_initial_zero_run():
    """
    Verifica se uma máscara que começa diretamente com pixels
    de primeiro plano aceita zero na primeira contagem RLE.
    """
    segmentation = MaskSegmentation(
        width=3,
        height=2,
        runs=(0, 6),
    )

    assert segmentation.runs == (0, 6)


def test_mask_segmentation_is_immutable():
    """
    Verifica se os atributos da máscara não podem ser alterados
    após a criação do objeto.
    """
    segmentation = MaskSegmentation(
        width=3,
        height=2,
        runs=(6,),
    )

    with pytest.raises(AttributeError):
        segmentation.width = 5

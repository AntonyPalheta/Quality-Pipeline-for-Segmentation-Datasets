
"""
Este módulo contém os testes automatizados das representações
internas de segmentação.

Os testes verificam se PolygonSegmentation e MaskSegmentation
armazenam corretamente suas respectivas representações geométricas
e se ambas pertencem ao tipo Segmentation.
"""

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

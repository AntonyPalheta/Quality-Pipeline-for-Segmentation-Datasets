
"""
Este módulo contém os testes automatizados do modelo BoundingBox.

Os testes verificam se a classe armazena corretamente as coordenadas
e dimensões da caixa delimitadora, incluindo valores decimais.
"""

from quality_pipeline.models import BoundingBox


def test_bounding_box_stores_attributes():
    """
    Verifica se BoundingBox armazena corretamente as coordenadas
    do canto superior esquerdo e as dimensões da caixa.
    """
    bounding_box = BoundingBox(
        x=125.0,
        y=84.0,
        width=210.0,
        height=160.0,
    )

    assert bounding_box.x == 125.0
    assert bounding_box.y == 84.0
    assert bounding_box.width == 210.0
    assert bounding_box.height == 160.0


def test_bounding_box_accepts_decimal_values():
    """
    Verifica se BoundingBox preserva valores decimais,
    evitando perda de precisão nas coordenadas e dimensões.
    """
    bounding_box = BoundingBox(
        x=125.75,
        y=84.25,
        width=210.50,
        height=160.75,
    )

    assert bounding_box.x == 125.75
    assert bounding_box.y == 84.25
    assert bounding_box.width == 210.50
    assert bounding_box.height == 160.75

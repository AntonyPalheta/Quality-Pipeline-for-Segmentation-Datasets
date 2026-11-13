
"""
Este módulo contém os testes automatizados do modelo Annotation.

Os testes verificam o armazenamento dos dados de uma anotação,
o comportamento dos atributos opcionais e a independência
dos dicionários de metadados entre diferentes instâncias.
"""

from quality_pipeline.models import (
    Annotation,
    BoundingBox,
    PolygonSegmentation,
)


def test_annotation_stores_all_attributes():
    """
    Verifica se Annotation armazena corretamente todos os atributos,
    incluindo referências, segmentação, bounding box e metadados.
    """
    segmentation = PolygonSegmentation(
        polygons=[
            [
                (10.0, 20.0),
                (50.0, 20.0),
                (40.0, 60.0),
            ]
        ]
    )

    bounding_box = BoundingBox(
        x=10.0,
        y=20.0,
        width=40.0,
        height=40.0,
    )

    attributes = {
        "occluded": False,
        "source": "manual",
    }

    annotation = Annotation(
        id=1,
        image_id=10,
        category_id=2,
        segmentation=segmentation,
        bbox=bounding_box,
        area=800.0,
        is_crowd=False,
        attributes=attributes,
    )

    assert annotation.id == 1
    assert annotation.image_id == 10
    assert annotation.category_id == 2
    assert annotation.segmentation is segmentation
    assert annotation.bbox is bounding_box
    assert annotation.area == 800.0
    assert annotation.is_crowd is False
    assert annotation.attributes == attributes


def test_annotation_optional_attributes_default_to_none():
    """
    Verifica se os atributos opcionais recebem seus valores padrão
    quando não são informados durante a criação da anotação.
    """
    annotation = Annotation(
        id=2,
        image_id=10,
        category_id=3,
    )

    assert annotation.segmentation is None
    assert annotation.bbox is None
    assert annotation.area is None
    assert annotation.is_crowd is None
    assert annotation.attributes == {}


def test_annotation_attributes_are_independent_between_instances():
    """
    Verifica se diferentes instâncias de Annotation possuem
    dicionários attributes independentes.

    Isso evita que alterações nos metadados de uma anotação
    afetem acidentalmente outra anotação.
    """
    first_annotation = Annotation(
        id=1,
        image_id=10,
        category_id=2,
    )

    second_annotation = Annotation(
        id=2,
        image_id=10,
        category_id=2,
    )

    first_annotation.attributes["occluded"] = True

    assert first_annotation.attributes == {"occluded": True}
    assert second_annotation.attributes == {}

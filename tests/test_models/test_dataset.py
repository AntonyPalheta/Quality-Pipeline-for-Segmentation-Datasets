
"""
Este módulo contém os testes automatizados do modelo Dataset.

Os testes verificam o armazenamento das imagens, categorias,
anotações e metadados, além da independência das coleções
e dos dicionários entre diferentes instâncias de Dataset.
"""

from quality_pipeline.models import (
    Annotation,
    Category,
    Dataset,
    Image,
)


def test_dataset_stores_all_attributes():
    """
    Verifica se Dataset armazena corretamente imagens,
    categorias, anotações e metadados.
    """
    image = Image(
        id=1,
        file_name="images/apple.jpg",
        width=1920,
        height=1080,
    )

    category = Category(
        id=1,
        name="apple",
        supercategory="fruit",
    )

    annotation = Annotation(
        id=1,
        image_id=1,
        category_id=1,
        area=800.0,
    )

    metadata = {
        "source": "CVAT",
        "description": "Fruit segmentation dataset",
    }

    dataset = Dataset(
        images=[image],
        categories=[category],
        annotations=[annotation],
        metadata=metadata,
    )

    assert dataset.images == [image]
    assert dataset.categories == [category]
    assert dataset.annotations == [annotation]
    assert dataset.metadata == metadata


def test_dataset_collections_default_to_empty():
    """
    Verifica se as coleções e os metadados começam vazios
    quando não são informados durante a criação do Dataset.
    """
    dataset = Dataset()

    assert dataset.images == []
    assert dataset.categories == []
    assert dataset.annotations == []
    assert dataset.metadata == {}


def test_dataset_collections_are_independent_between_instances():
    """
    Verifica se diferentes instâncias de Dataset possuem
    listas e dicionários independentes.

    Alterações em uma instância não devem afetar outra.
    """
    first_dataset = Dataset()
    second_dataset = Dataset()

    image = Image(
        id=1,
        file_name="images/apple.jpg",
        width=1920,
        height=1080,
    )

    first_dataset.images.append(image)
    first_dataset.metadata["source"] = "CVAT"

    assert len(first_dataset.images) == 1
    assert first_dataset.metadata == {"source": "CVAT"}

    assert second_dataset.images == []
    assert second_dataset.categories == []
    assert second_dataset.annotations == []
    assert second_dataset.metadata == {}

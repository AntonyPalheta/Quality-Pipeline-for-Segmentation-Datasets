
"""
Este módulo contém os testes automatizados do modelo Category.

Os testes verificam se a classe armazena corretamente os dados
de uma categoria e se o atributo supercategory pode ser omitido.
"""

from quality_pipeline.models import Category


def test_category_stores_attributes():
    """
    Verifica se Category armazena corretamente os atributos
    recebidos durante a criação do objeto.
    """
    category = Category(
        id=1,
        name="apple",
        supercategory="fruit"
    )

    assert category.id == 1
    assert category.name == "apple"
    assert category.supercategory == "fruit"


def test_category_supercategory_defaults_to_none():
    """
    Verifica se supercategory recebe None quando não é informado.
    """
    category = Category(
        id=2,
        name="tomato"
    )

    assert category.supercategory is None

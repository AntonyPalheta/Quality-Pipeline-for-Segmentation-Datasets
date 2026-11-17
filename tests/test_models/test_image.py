
"""
Este módulo contém os testes automatizados do modelo Image.

Os testes verificam se a classe armazena corretamente os dados
de uma imagem e se o caminho local resolvido (resolved_path)
pode ser informado ou permanecer None.
"""

from pathlib import Path

from quality_pipeline.models import Image


def test_image_stores_attributes():
    """
    Verifica se Image armazena corretamente seus atributos,
    incluindo o caminho local da imagem.
    """
    resolved_path = Path("data/raw/coco_sample/images/apple.jpg")

    image = Image(
        id=1,
        file_name="pre-annotation/batch-20261113/images/apple.jpg",
        width=1920,
        height=1080,
        resolved_path=resolved_path
    )

    assert image.id == 1
    assert image.file_name == "pre-annotation/batch-20261113/images/apple.jpg"
    assert image.width == 1920
    assert image.height == 1080
    assert image.resolved_path == resolved_path


def test_image_resolved_path_defaults_to_none():
    """
    Verifica se resolved_path recebe None quando não é informado.
    """
    image = Image(
        id=2,
        file_name="apple.jpg",
        width=640,
        height=480
    )

    assert image.resolved_path is None

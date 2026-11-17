
"""
Este módulo contém os testes automatizados das conversões
de segmentações RLE do formato COCO.

Os testes verificam a interpretação de RLE comprimido e
não comprimido, a conversão da ordem column-major para
row-major e o tratamento de estruturas inválidas.
"""

import pytest

from quality_pipeline.models import MaskSegmentation
from quality_pipeline.parsers.coco_rle import (
    CocoRLEError,
    decode_coco_rle,
)


def test_decode_uncompressed_coco_rle():
    """
    Verifica a conversão de RLE não comprimido do COCO
    para a representação interna row-major.

    O exemplo representa uma máscara de 3 colunas por 2 linhas.
    """
    coco_rle = {
        "size": [2, 3],
        "counts": [2, 1, 1, 2],
    }

    segmentation = decode_coco_rle(coco_rle)

    assert isinstance(segmentation, MaskSegmentation)
    assert segmentation.width == 3
    assert segmentation.height == 2

    # RLE COCO: column-major.
    # RLE interno: row-major.
    assert segmentation.runs == (1, 2, 2, 1)


def test_decode_compressed_coco_rle():
    """
    Verifica a decodificação de RLE comprimido do COCO.

    O exemplo utiliza uma sequência que contém codificação
    diferencial com valor negativo.
    """
    coco_rle = {
        "size": [2, 3],
        "counts": "032N",
    }

    segmentation = decode_coco_rle(coco_rle)

    assert isinstance(segmentation, MaskSegmentation)
    assert segmentation.width == 3
    assert segmentation.height == 2
    assert segmentation.runs == (0, 2, 1, 1, 1, 1)


def test_decode_all_background_mask():
    """
    Verifica a conversão de uma máscara composta apenas por fundo.
    """
    coco_rle = {
        "size": [2, 3],
        "counts": [6],
    }

    segmentation = decode_coco_rle(coco_rle)

    assert segmentation.runs == (6,)


def test_decode_all_foreground_mask():
    """
    Verifica a conversão de uma máscara composta apenas por objeto.

    O RLE utiliza uma primeira contagem igual a zero para indicar
    que a máscara começa diretamente com pixels de primeiro plano.
    """
    coco_rle = {
        "size": [2, 3],
        "counts": [0, 6],
    }

    segmentation = decode_coco_rle(coco_rle)

    assert segmentation.runs == (0, 6)


@pytest.mark.parametrize(
    "size",
    [
        [],
        [2],
        [0, 3],
        [-1, 3],
        [2, 0],
        [2.0, 3],
        [True, 3],
    ],
)
def test_decode_rejects_invalid_mask_dimensions(size):
    """
    Verifica se dimensões inválidas ou com tipos incompatíveis
    são rejeitadas.
    """
    coco_rle = {
        "size": size,
        "counts": [6],
    }

    with pytest.raises(CocoRLEError):
        decode_coco_rle(coco_rle)


@pytest.mark.parametrize(
    "counts",
    [
        [],
        [1, -1, 6],
        [1, 0, 5],
        [1, 2],
        [1, 2.5, 2, 0.5],
        [True, 5],
    ],
)
def test_decode_rejects_invalid_uncompressed_counts(counts):
    """
    Verifica se contagens RLE não comprimidas inválidas
    são rejeitadas.
    """
    coco_rle = {
        "size": [2, 3],
        "counts": counts,
    }

    with pytest.raises(CocoRLEError):
        decode_coco_rle(coco_rle)


@pytest.mark.parametrize(
    "counts",
    [
        "",
        "P",
        "p",
        " ",
    ],
)
def test_decode_rejects_invalid_compressed_counts(counts):
    """
    Verifica se strings RLE comprimidas inválidas ou incompletas
    são rejeitadas.
    """
    coco_rle = {
        "size": [2, 3],
        "counts": counts,
    }

    with pytest.raises(CocoRLEError):
        decode_coco_rle(coco_rle)


def test_decode_rejects_non_object_rle():
    """
    Verifica se a função rejeita uma estrutura RLE que não
    seja representada por um objeto.
    """
    with pytest.raises(CocoRLEError):
        decode_coco_rle([])


def test_decode_rejects_missing_counts():
    """
    Verifica se a ausência do campo counts é identificada.
    """
    coco_rle = {
        "size": [2, 3],
    }

    with pytest.raises(CocoRLEError):
        decode_coco_rle(coco_rle)

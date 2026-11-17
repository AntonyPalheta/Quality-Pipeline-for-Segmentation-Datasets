
"""
Este módulo contém os testes automatizados do CocoParser.

Os testes verificam a leitura do JSON COCO, a conversão de imagens,
categorias e anotações, a resolução de caminhos e o tratamento
de estruturas inválidas.

Os datasets utilizados são sintéticos e criados durante a execução
dos testes, evitando dependência de arquivos externos.
"""

import json
from pathlib import Path
from typing import Any

import pytest

from quality_pipeline.models import (
    Annotation,
    BoundingBox,
    Dataset,
    MaskSegmentation,
    PolygonSegmentation,
)
from quality_pipeline.parsers import (
    CocoParser,
    CocoParserError,
)


def _write_coco_json(
    directory: Path,
    payload: object,
) -> Path:
    """
    Cria um arquivo JSON temporário com o conteúdo informado.

    Args:
        directory: Diretório temporário onde o JSON será criado.
        payload: Estrutura que será serializada como JSON.

    Returns:
        Caminho do arquivo JSON criado.
    """
    annotation_file = directory / "annotations.json"

    annotation_file.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    return annotation_file


def _minimal_coco_payload() -> dict[str, Any]:
    """
    Cria uma estrutura COCO mínima para reutilização nos testes.

    O exemplo contém uma imagem, duas categorias e nenhuma anotação.

    Returns:
        Dicionário representando um dataset COCO simplificado.
    """
    return {
        "info": {
            "description": "Synthetic COCO dataset",
        },
        "licenses": [],
        "images": [
            {
                "id": 1,
                "file_name": "batch-example/images/image_001.jpg",
                "width": 640,
                "height": 480,
            }
        ],
        "categories": [
            {
                "id": 3,
                "name": "apple",
                "supercategory": "fruit",
            },
            {
                "id": 8,
                "name": "banana",
            },
        ],
        "annotations": [],
    }


def _payload_with_annotation(
    annotation: dict[str, Any],
) -> dict[str, Any]:
    """
    Cria um dataset COCO mínimo contendo uma anotação.

    Args:
        annotation: Registro de anotação que será incluído no dataset.

    Returns:
        Dicionário representando o dataset COCO.
    """
    payload = _minimal_coco_payload()
    payload["annotations"] = [annotation]

    return payload


def test_coco_parser_loads_images_and_categories(tmp_path):
    """
    Verifica se o parser converte corretamente imagens e categorias
    para uma instância do modelo interno Dataset.
    """
    annotation_file = _write_coco_json(
        tmp_path,
        _minimal_coco_payload(),
    )

    images_root = tmp_path / "images"

    parser = CocoParser(
        annotation_file=annotation_file,
        images_root=images_root,
    )

    dataset = parser.parse()

    assert isinstance(dataset, Dataset)

    assert len(dataset.images) == 1
    assert len(dataset.categories) == 2
    assert len(dataset.annotations) == 0

    assert dataset.images[0].id == 1
    assert dataset.images[0].width == 640
    assert dataset.images[0].height == 480

    assert dataset.categories[0].id == 3
    assert dataset.categories[0].name == "apple"
    assert dataset.categories[0].supercategory == "fruit"

    assert dataset.categories[1].id == 8
    assert dataset.categories[1].name == "banana"
    assert dataset.categories[1].supercategory is None

    assert dataset.metadata["source_format"] == "COCO"


def test_coco_parser_resolves_image_path_from_configured_root(tmp_path):
    """
    Verifica se o parser combina corretamente o diretório raiz
    configurado com o caminho relativo original da imagem.
    """
    annotation_file = _write_coco_json(
        tmp_path,
        _minimal_coco_payload(),
    )

    images_root = tmp_path / "dataset" / "images"

    parser = CocoParser(
        annotation_file=annotation_file,
        images_root=images_root,
    )

    dataset = parser.parse()

    image = dataset.images[0]

    expected_path = (
        images_root / image.file_name
    ).resolve()

    assert image.file_name == "batch-example/images/image_001.jpg"
    assert image.resolved_path == expected_path


def test_coco_parser_allows_missing_images_root(tmp_path):
    """
    Verifica se o parser funciona sem um diretório raiz de imagens.
    """
    annotation_file = _write_coco_json(
        tmp_path,
        _minimal_coco_payload(),
    )

    parser = CocoParser(
        annotation_file=annotation_file,
    )

    dataset = parser.parse()

    assert dataset.images[0].file_name == (
        "batch-example/images/image_001.jpg"
    )
    assert dataset.images[0].resolved_path is None


def test_coco_parser_raises_error_when_annotation_file_does_not_exist(
    tmp_path,
):
    """
    Verifica se o parser informa corretamente quando o arquivo
    annotations.json não existe.
    """
    annotation_file = tmp_path / "missing.json"

    parser = CocoParser(annotation_file=annotation_file)

    with pytest.raises(FileNotFoundError):
        parser.parse()


def test_coco_parser_rejects_invalid_json(tmp_path):
    """
    Verifica se o parser identifica um arquivo que não contém
    um JSON válido.
    """
    annotation_file = tmp_path / "annotations.json"

    annotation_file.write_text(
        '{"images": ',
        encoding="utf-8",
    )

    parser = CocoParser(annotation_file=annotation_file)

    with pytest.raises(CocoParserError):
        parser.parse()


def test_coco_parser_rejects_non_object_json_root(tmp_path):
    """
    Verifica se o parser rejeita estruturas JSON cuja raiz
    não seja um objeto.
    """
    annotation_file = _write_coco_json(
        tmp_path,
        [],
    )

    parser = CocoParser(annotation_file=annotation_file)

    with pytest.raises(CocoParserError):
        parser.parse()


def test_coco_parser_converts_polygon_annotation(tmp_path):
    """
    Verifica a conversão de uma anotação COCO completa,
    incluindo polígono, bounding box, área e atributos.
    """
    payload = _payload_with_annotation(
        {
            "id": 101,
            "image_id": 1,
            "category_id": 3,
            "segmentation": [
                [
                    10.0, 20.0,
                    50.0, 20.0,
                    40.0, 60.0,
                ]
            ],
            "bbox": [10.0, 20.0, 40.0, 40.0],
            "area": 800.0,
            "iscrowd": 0,
            "attributes": {
                "occluded": False,
            },
        }
    )

    annotation_file = _write_coco_json(tmp_path, payload)

    parser = CocoParser(annotation_file=annotation_file)
    dataset = parser.parse()

    assert len(dataset.annotations) == 1

    annotation = dataset.annotations[0]

    assert isinstance(annotation, Annotation)
    assert annotation.id == 101
    assert annotation.image_id == 1
    assert annotation.category_id == 3

    assert isinstance(annotation.segmentation, PolygonSegmentation)

    assert annotation.segmentation.polygons == [
        [
            (10.0, 20.0),
            (50.0, 20.0),
            (40.0, 60.0),
        ]
    ]

    assert isinstance(annotation.bbox, BoundingBox)
    assert annotation.bbox.x == 10.0
    assert annotation.bbox.y == 20.0
    assert annotation.bbox.width == 40.0
    assert annotation.bbox.height == 40.0

    assert annotation.area == 800.0
    assert annotation.is_crowd is False
    assert annotation.attributes == {"occluded": False}


def test_coco_parser_converts_multiple_polygons(tmp_path):
    """
    Verifica se o parser preserva múltiplos polígonos
    pertencentes à mesma anotação.
    """
    payload = _payload_with_annotation(
        {
            "id": 102,
            "image_id": 1,
            "category_id": 3,
            "segmentation": [
                [
                    10.0, 20.0,
                    50.0, 20.0,
                    40.0, 60.0,
                ],
                [
                    80.0, 90.0,
                    100.0, 90.0,
                    90.0, 110.0,
                ],
            ],
        }
    )

    annotation_file = _write_coco_json(tmp_path, payload)

    parser = CocoParser(annotation_file=annotation_file)
    dataset = parser.parse()

    annotation = dataset.annotations[0]

    assert isinstance(annotation.segmentation, PolygonSegmentation)
    assert len(annotation.segmentation.polygons) == 2

    assert annotation.segmentation.polygons[0] == [
        (10.0, 20.0),
        (50.0, 20.0),
        (40.0, 60.0),
    ]

    assert annotation.segmentation.polygons[1] == [
        (80.0, 90.0),
        (100.0, 90.0),
        (90.0, 110.0),
    ]


def test_coco_parser_rejects_non_object_image_record(tmp_path):
    """
    Verifica se registros de imagem que não são objetos JSON
    são rejeitados pelo parser.
    """
    payload = _minimal_coco_payload()
    payload["images"] = [None]

    annotation_file = _write_coco_json(tmp_path, payload)

    parser = CocoParser(annotation_file=annotation_file)

    with pytest.raises(CocoParserError):
        parser.parse()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("width", 0),
        ("width", True),
        ("height", -1),
        ("height", 480.0),
    ],
)
def test_coco_parser_rejects_invalid_image_dimensions(
    tmp_path,
    field,
    value,
):
    """
    Verifica se dimensões inválidas ou com tipos incompatíveis
    são rejeitadas pelo parser.
    """
    payload = _minimal_coco_payload()
    payload["images"][0][field] = value

    annotation_file = _write_coco_json(tmp_path, payload)

    parser = CocoParser(annotation_file=annotation_file)

    with pytest.raises(CocoParserError):
        parser.parse()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", ""),
        ("name", None),
        ("supercategory", 123),
    ],
)
def test_coco_parser_rejects_invalid_category_fields(
    tmp_path,
    field,
    value,
):
    """
    Verifica se nomes e supercategorias inválidos
    são rejeitados durante a conversão.
    """
    payload = _minimal_coco_payload()
    payload["categories"][0][field] = value

    annotation_file = _write_coco_json(tmp_path, payload)

    parser = CocoParser(annotation_file=annotation_file)

    with pytest.raises(CocoParserError):
        parser.parse()


def test_coco_parser_rejects_invalid_annotation_identifier(tmp_path):
    """
    Verifica se identificadores booleanos são rejeitados
    como IDs de anotação.
    """
    payload = _payload_with_annotation(
        {
            "id": True,
            "image_id": 1,
            "category_id": 3,
        }
    )

    annotation_file = _write_coco_json(tmp_path, payload)

    parser = CocoParser(annotation_file=annotation_file)

    with pytest.raises(CocoParserError):
        parser.parse()


@pytest.mark.parametrize(
    "segmentation",
    [
        [[0, 0, 10, 10]],
        [[0, 0, 10, 10, 5]],
        [[0, 0, float("nan"), 10, 5, 5]],
    ],
)
def test_coco_parser_rejects_unsupported_or_invalid_segmentations(
    tmp_path,
    segmentation,
):
    """
    Verifica se o parser rejeita RLE ainda não suportado
    e estruturas poligonais malformadas.
    """
    payload = _payload_with_annotation(
        {
            "id": 103,
            "image_id": 1,
            "category_id": 3,
            "segmentation": segmentation,
        }
    )

    annotation_file = _write_coco_json(tmp_path, payload)

    parser = CocoParser(annotation_file=annotation_file)

    with pytest.raises(CocoParserError):
        parser.parse()


@pytest.mark.parametrize(
    "bbox",
    [
        [10, 20, 30],
        [10, 20, -30, 40],
        [10, 20, "invalid", 40],
    ],
)
def test_coco_parser_rejects_invalid_bounding_boxes(
    tmp_path,
    bbox,
):
    """
    Verifica se bounding boxes com estrutura ou valores inválidos
    são rejeitadas pelo parser.
    """
    payload = _payload_with_annotation(
        {
            "id": 104,
            "image_id": 1,
            "category_id": 3,
            "bbox": bbox,
        }
    )

    annotation_file = _write_coco_json(tmp_path, payload)

    parser = CocoParser(annotation_file=annotation_file)

    with pytest.raises(CocoParserError):
        parser.parse()


def test_coco_parser_rejects_negative_annotation_area(tmp_path):
    """
    Verifica se o parser rejeita áreas negativas.
    """
    payload = _payload_with_annotation(
        {
            "id": 105,
            "image_id": 1,
            "category_id": 3,
            "area": -10.0,
        }
    )

    annotation_file = _write_coco_json(tmp_path, payload)

    parser = CocoParser(annotation_file=annotation_file)

    with pytest.raises(CocoParserError):
        parser.parse()


def test_coco_parser_rejects_invalid_iscrowd(tmp_path):
    """
    Verifica se o parser rejeita valores de iscrowd diferentes
    de 0, 1 ou booleanos.
    """
    payload = _payload_with_annotation(
        {
            "id": 106,
            "image_id": 1,
            "category_id": 3,
            "iscrowd": 2,
        }
    )

    annotation_file = _write_coco_json(tmp_path, payload)

    parser = CocoParser(annotation_file=annotation_file)

    with pytest.raises(CocoParserError):
        parser.parse()


def test_coco_parser_rejects_non_object_attributes(tmp_path):
    """
    Verifica se attributes deve ser representado por um objeto JSON.
    """
    payload = _payload_with_annotation(
        {
            "id": 107,
            "image_id": 1,
            "category_id": 3,
            "attributes": ["occluded"],
        }
    )

    annotation_file = _write_coco_json(tmp_path, payload)

    parser = CocoParser(annotation_file=annotation_file)

    with pytest.raises(CocoParserError):
        parser.parse()


def test_coco_parser_rejects_image_path_outside_configured_root(tmp_path):
    """
    Verifica se o parser impede caminhos que tentem escapar
    do diretório raiz configurado para as imagens.
    """
    payload = _minimal_coco_payload()

    payload["images"][0]["file_name"] = "../outside/image.jpg"

    annotation_file = _write_coco_json(tmp_path, payload)

    parser = CocoParser(
        annotation_file=annotation_file,
        images_root=tmp_path / "images",
    )

    with pytest.raises(CocoParserError):
        parser.parse()


def test_coco_parser_converts_uncompressed_rle(tmp_path):
    """
    Verifica se o CocoParser converte RLE não comprimido do COCO
    para o modelo interno MaskSegmentation.
    """
    payload = _minimal_coco_payload()

    payload["images"][0]["width"] = 3
    payload["images"][0]["height"] = 2

    payload["annotations"] = [
        {
            "id": 201,
            "image_id": 1,
            "category_id": 3,
            "segmentation": {
                "size": [2, 3],
                "counts": [2, 1, 1, 2],
            },
            "iscrowd": 1,
        }
    ]

    annotation_file = _write_coco_json(tmp_path, payload)

    parser = CocoParser(annotation_file=annotation_file)
    dataset = parser.parse()

    annotation = dataset.annotations[0]

    assert isinstance(annotation.segmentation, MaskSegmentation)
    assert annotation.segmentation.width == 3
    assert annotation.segmentation.height == 2
    assert annotation.segmentation.runs == (1, 2, 2, 1)
    assert annotation.is_crowd is True


def test_coco_parser_converts_compressed_rle(tmp_path):
    """
    Verifica se o CocoParser converte RLE comprimido do COCO
    para o modelo interno MaskSegmentation.
    """
    payload = _minimal_coco_payload()

    payload["images"][0]["width"] = 3
    payload["images"][0]["height"] = 2

    payload["annotations"] = [
        {
            "id": 202,
            "image_id": 1,
            "category_id": 3,
            "segmentation": {
                "size": [2, 3],
                "counts": "032N",
            },
        }
    ]

    annotation_file = _write_coco_json(tmp_path, payload)

    parser = CocoParser(annotation_file=annotation_file)
    dataset = parser.parse()

    annotation = dataset.annotations[0]

    assert isinstance(annotation.segmentation, MaskSegmentation)
    assert annotation.segmentation.runs == (0, 2, 1, 1, 1, 1)


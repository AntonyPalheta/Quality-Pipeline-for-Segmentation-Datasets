
"""
Este módulo define o modelo Annotation, responsável por representar
uma anotação de objeto pertencente a uma imagem de um dataset.

A classe relaciona uma imagem, uma categoria e uma representação
geométrica de segmentação, podendo também armazenar uma bounding box
e metadados adicionais.

O modelo é independente do formato de origem dos dados. Os parsers
serão responsáveis por converter as informações de formatos externos,
como COCO e Ultralytics YOLO, para esta representação interna.
"""

from dataclasses import dataclass, field

from .bounding_box import BoundingBox
from .segmentation import Segmentation


@dataclass
class Annotation:
    """
    Representa uma instância de objeto anotada em uma imagem.

    Attributes:
        id: Identificador único da anotação dentro do dataset.
        image_id: Identificador da imagem à qual a anotação pertence.
        category_id: Identificador da categoria associada à anotação.
        segmentation: Representação geométrica da segmentação.
                      Pode ser None quando a informação estiver ausente.
        bbox: Caixa delimitadora do objeto, quando disponível.
        area: Área ocupada pela anotação, quando disponível.
        is_crowd: Indica se a anotação representa um agrupamento
                  de objetos. Pode ser None quando essa informação
                  não existir no formato de origem.
        attributes: Metadados adicionais associados à anotação,
                    preservados em formato de dicionário.
    """

    id: int
    image_id: int
    category_id: int
    segmentation: Segmentation | None = None
    bbox: BoundingBox | None = None
    area: float | None = None
    is_crowd: bool | None = None
    attributes: dict[str, object] = field(default_factory=dict)

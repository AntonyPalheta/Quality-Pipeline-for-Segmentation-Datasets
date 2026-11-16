
"""
Este módulo implementa o parser responsável por interpretar
datasets de segmentação exportados no formato COCO.

Sua responsabilidade é:

- Carregar e interpretar o arquivo annotations.json.
- Converter imagens para o modelo Image.
- Converter categorias para o modelo Category.
- Converter anotações para o modelo Annotation.
- Converter segmentações poligonais para PolygonSegmentation.
- Converter segmentações RLE para MaskSegmentation.
- Converter bounding boxes para BoundingBox.
- Preservar os atributos adicionais das anotações.
- Resolver caminhos locais das imagens utilizando uma raiz configurável.

São suportadas segmentações poligonais, RLE comprimido
e RLE não comprimido.
"""

import json
import math
from pathlib import Path
from typing import Any

from ..models import (
    Annotation,
    BoundingBox,
    Category,
    Dataset,
    Image,
    PolygonSegmentation,
    Segmentation,
)

from .coco_rle import CocoRLEError, decode_coco_rle

class CocoParserError(ValueError):
    """
    Representa erros encontrados durante a interpretação
    de um dataset no formato COCO.

    É utilizada quando o arquivo JSON ou seus registros
    não possuem uma estrutura compatível com o formato esperado.
    """


class CocoParser:
    """
Interpreta datasets COCO e converte seus dados para
os modelos internos do Quality Pipeline.

São suportadas imagens, categorias, anotações com
segmentações poligonais ou RLE e bounding boxes.

Attributes:
    annotation_file: Caminho do arquivo annotations.json.
    images_root: Diretório raiz utilizado para resolver
                 os caminhos relativos das imagens.
"""

    def __init__(
        self,
        annotation_file: str | Path,
        images_root: str | Path | None = None,
    ) -> None:
        """
        Inicializa o parser com os caminhos do dataset.

        Args:
            annotation_file: Caminho do arquivo annotations.json.
            images_root: Diretório raiz das imagens. É opcional.
        """
        self.annotation_file = Path(annotation_file)

        self.images_root = (
            Path(images_root)
            if images_root is not None
            else None
        )

    def parse(self) -> Dataset:
        """
        Carrega o JSON COCO e converte imagens, categorias
        e anotações para os modelos internos do projeto.

        Returns:
            Dataset contendo imagens, categorias, anotações
            e metadados do arquivo COCO.

        Raises:
            FileNotFoundError: Quando o arquivo JSON não existe.
            CocoParserError: Quando a estrutura do arquivo é inválida
                             ou contém registros incompatíveis.
        """
        data = self._load_json()

        images_data = self._get_required_list(data, "images")
        categories_data = self._get_required_list(data, "categories")
        annotations_data = self._get_required_list(data, "annotations")

        images = [
            self._parse_image(item)
            for item in images_data
        ]

        categories = [
            self._parse_category(item)
            for item in categories_data
        ]

        annotations = [
            self._parse_annotation(item)
            for item in annotations_data
        ]

        metadata = {
            "source_format": "COCO",
            "info": data.get("info"),
            "licenses": data.get("licenses", []),
        }

        return Dataset(
            images=images,
            categories=categories,
            annotations=annotations,
            metadata=metadata,
        )

    def _load_json(self) -> dict[str, Any]:
        """
        Abre e interpreta o arquivo JSON do dataset.

        Returns:
            Conteúdo do JSON representado como dicionário.

        Raises:
            FileNotFoundError: Quando o arquivo não existe.
            CocoParserError: Quando o JSON é inválido ou sua raiz
                             não representa um objeto.
        """
        if not self.annotation_file.is_file():
            raise FileNotFoundError(
                f"Arquivo COCO não encontrado: {self.annotation_file}"
            )

        try:
            with self.annotation_file.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

        except json.JSONDecodeError as error:
            raise CocoParserError(
                f"JSON COCO inválido: {error}"
            ) from error

        if not isinstance(data, dict):
            raise CocoParserError(
                "A estrutura principal do JSON COCO deve ser um objeto."
            )

        return data

    @staticmethod
    def _get_required_list(
        data: dict[str, Any],
        field_name: str,
    ) -> list[Any]:
        """
        Recupera uma coleção obrigatória do JSON COCO.

        Args:
            data: Conteúdo principal do JSON.
            field_name: Nome do campo que será recuperado.

        Returns:
            Lista de registros do campo solicitado.

        Raises:
            CocoParserError: Quando o campo não existe ou não é uma lista.
        """
        value = data.get(field_name)

        if not isinstance(value, list):
            raise CocoParserError(
                f"O campo '{field_name}' deve existir e ser uma lista."
            )

        return value

    def _parse_image(self, data: Any) -> Image:
        """
        Converte um registro de imagem COCO para o modelo Image.

        O caminho original é preservado em file_name.
        Quando images_root é informado, resolved_path recebe
        o caminho local correspondente.

        Args:
            data: Registro de imagem encontrado no JSON COCO.

        Returns:
            Instância do modelo Image.

        Raises:
            CocoParserError: Quando os dados da imagem são inválidos.
        """
        self._validate_record(data, "imagem")

        image_id = self._require_integer(data, "id", "imagem")
        file_name = data.get("file_name")

        if not isinstance(file_name, str) or not file_name.strip():
            raise CocoParserError(
                "O campo 'file_name' da imagem deve ser uma string válida."
            )

        width = self._require_integer(data, "width", "imagem")
        height = self._require_integer(data, "height", "imagem")

        if width <= 0 or height <= 0:
            raise CocoParserError(
                "As dimensões da imagem devem ser positivas."
            )

        resolved_path = self._resolve_image_path(file_name)

        return Image(
            id=image_id,
            file_name=file_name,
            width=width,
            height=height,
            resolved_path=resolved_path,
        )

    def _parse_category(self, data: Any) -> Category:
        """
        Converte um registro de categoria COCO para o modelo Category.

        O campo supercategory é opcional e será preservado quando
        estiver disponível.

        Args:
            data: Registro de categoria encontrado no JSON COCO.

        Returns:
            Instância do modelo Category.

        Raises:
            CocoParserError: Quando os dados da categoria são inválidos.
        """
        self._validate_record(data, "categoria")

        category_id = self._require_integer(data, "id", "categoria")
        name = data.get("name")
        supercategory = data.get("supercategory")

        if not isinstance(name, str) or not name.strip():
            raise CocoParserError(
                "O campo 'name' da categoria deve ser uma string válida."
            )

        if (
            supercategory is not None
            and not isinstance(supercategory, str)
        ):
            raise CocoParserError(
                "O campo 'supercategory' deve ser uma string ou None."
            )

        return Category(
            id=category_id,
            name=name,
            supercategory=supercategory,
        )

    def _parse_annotation(self, data: Any) -> Annotation:
        """
        Converte uma anotação COCO para o modelo interno Annotation.

        Interpreta identificadores, segmentação, bounding box,
        área, informação de agrupamento e atributos adicionais.

        Args:
            data: Registro de anotação encontrado no JSON COCO.

        Returns:
            Instância do modelo Annotation.

        Raises:
            CocoParserError: Quando os dados da anotação são inválidos.
        """
        self._validate_record(data, "anotação")

        annotation_id = self._require_integer(data, "id", "anotação")
        image_id = self._require_integer(data, "image_id", "anotação")
        category_id = self._require_integer(data, "category_id", "anotação")

        segmentation = self._parse_segmentation(
            data.get("segmentation")
        )

        bbox = self._parse_bbox(data.get("bbox"))

        area_value = data.get("area")

        area = (
            None
            if area_value is None
            else self._require_number(
                area_value,
                "area",
                "anotação",
            )
        )

        if area is not None and area < 0:
            raise CocoParserError(
                "O campo 'area' não pode ser negativo."
            )

        iscrowd_value = data.get("iscrowd")

        if iscrowd_value is None:
            is_crowd = None
        elif isinstance(iscrowd_value, bool):
            is_crowd = iscrowd_value
        elif (
            isinstance(iscrowd_value, int)
            and iscrowd_value in (0, 1)
        ):
            is_crowd = bool(iscrowd_value)
        else:
            raise CocoParserError(
                "O campo 'iscrowd' deve ser 0, 1 ou estar ausente."
            )

        attributes = data.get("attributes")

        if attributes is None:
            attributes = {}

        if not isinstance(attributes, dict):
            raise CocoParserError(
                "O campo 'attributes' deve ser um objeto JSON."
            )

        return Annotation(
            id=annotation_id,
            image_id=image_id,
            category_id=category_id,
            segmentation=segmentation,
            bbox=bbox,
            area=area,
            is_crowd=is_crowd,
            attributes=attributes,
        )

    
    @staticmethod
    def _parse_segmentation(
        data: Any,
    ) -> Segmentation | None:
        """
        Converte uma segmentação COCO para a representação interna.

        Suporta:
        - Polígonos.
        - RLE comprimido.
        - RLE não comprimido.

        As coordenadas dos polígonos são preservadas em pixels.
        As máscaras RLE são convertidas para a representação interna
        row-major.

        Args:
            data: Campo segmentation de uma anotação COCO.

        Returns:
            PolygonSegmentation, MaskSegmentation ou None.

        Raises:
            CocoParserError: Quando a estrutura da segmentação é inválida.
        """
        if data is None or data == []:
            return None

        if isinstance(data, dict):
            try:
                return decode_coco_rle(data)

            except CocoRLEError as error:
                raise CocoParserError(
                    f"Segmentação RLE COCO inválida: {error}"
                ) from error

        if not isinstance(data, list):
            raise CocoParserError(
                "O campo 'segmentation' possui uma estrutura inválida."
            )

        polygons = []

        for polygon_index, coordinates in enumerate(data):
            if not isinstance(coordinates, list):
                raise CocoParserError(
                    f"Polígono {polygon_index} deve ser uma lista."
                )

            if len(coordinates) < 6 or len(coordinates) % 2 != 0:
                raise CocoParserError(
                    f"Polígono {polygon_index} deve possuir pelo menos "
                    "três pontos e uma quantidade par de coordenadas."
                )

            points = []

            for index in range(0, len(coordinates), 2):
                x = CocoParser._require_number(
                    coordinates[index],
                    "coordenada X",
                    "polígono",
                )

                y = CocoParser._require_number(
                    coordinates[index + 1],
                    "coordenada Y",
                    "polígono",
                )

                points.append((x, y))

            polygons.append(points)

        return PolygonSegmentation(polygons=polygons)

    @staticmethod
    def _parse_bbox(data: Any) -> BoundingBox | None:
        """
        Converte uma bounding box COCO para o modelo BoundingBox.

        O formato COCO utiliza [x, y, width, height], com coordenadas
        expressas em pixels a partir do canto superior esquerdo.

        Args:
            data: Campo bbox da anotação COCO.

        Returns:
            BoundingBox ou None quando a informação está ausente.

        Raises:
            CocoParserError: Quando a estrutura da bounding box é inválida.
        """
        if data is None:
            return None

        if not isinstance(data, list) or len(data) != 4:
            raise CocoParserError(
                "O campo 'bbox' deve ser uma lista com quatro valores."
            )

        x, y, width, height = (
            CocoParser._require_number(
                value,
                "bbox",
                "anotação",
            )
            for value in data
        )

        if width < 0 or height < 0:
            raise CocoParserError(
                "A largura e a altura da bounding box não podem ser negativas."
            )

        return BoundingBox(
            x=x,
            y=y,
            width=width,
            height=height,
        )

    def _resolve_image_path(self, file_name: str) -> Path | None:
        """
        Resolve o caminho local de uma imagem utilizando images_root.

        O caminho relativo original não é alterado.

        Também impede que um caminho relativo escape do diretório
        raiz configurado, por exemplo, utilizando '..'.

        Args:
            file_name: Caminho relativo encontrado no JSON COCO.

        Returns:
            Caminho local completo ou None quando images_root
            não foi informado.

        Raises:
            CocoParserError: Quando o caminho é absoluto ou escapa
                             do diretório raiz configurado.
        """
        if self.images_root is None:
            return None

        relative_path = Path(file_name)

        if relative_path.is_absolute() or relative_path.drive:
            raise CocoParserError(
                f"O caminho da imagem deve ser relativo: {file_name}"
            )

        root = self.images_root.resolve()
        resolved_path = (root / relative_path).resolve()

        if not resolved_path.is_relative_to(root):
            raise CocoParserError(
                f"O caminho da imagem escapa do diretório raiz: {file_name}"
            )

        return resolved_path

    @staticmethod
    def _validate_record(data: Any, record_type: str) -> None:
        """
        Verifica se um registro do JSON é representado por um objeto.

        Args:
            data: Registro que será verificado.
            record_type: Tipo de registro utilizado na mensagem de erro.

        Raises:
            CocoParserError: Quando o registro não é um objeto JSON.
        """
        if not isinstance(data, dict):
            raise CocoParserError(
                f"O registro de {record_type} deve ser um objeto JSON."
            )

    @staticmethod
    def _require_integer(
        data: dict[str, Any],
        field_name: str,
        record_type: str,
    ) -> int:
        """
        Recupera um campo inteiro obrigatório de um registro COCO.

        Valores booleanos são rejeitados, pois Python considera bool
        uma subclasse de int.

        Args:
            data: Registro que contém o campo.
            field_name: Nome do campo obrigatório.
            record_type: Tipo de registro utilizado na mensagem de erro.

        Returns:
            Valor inteiro do campo.

        Raises:
            CocoParserError: Quando o campo não é um inteiro válido.
        """
        value = data.get(field_name)

        if (
            isinstance(value, bool)
            or not isinstance(value, int)
        ):
            raise CocoParserError(
                f"O campo '{field_name}' do registro de {record_type} "
                "deve ser um inteiro."
            )

        return value

    @staticmethod
    def _require_number(
        value: Any,
        field_name: str,
        record_type: str,
    ) -> float:
        """
        Verifica se um valor é numérico e finito.

        Valores booleanos são rejeitados, pois Python considera bool
        uma subclasse de int.

        Args:
            value: Valor que será verificado.
            field_name: Nome do campo para a mensagem de erro.
            record_type: Tipo de registro analisado.

        Returns:
            Valor convertido para float.

        Raises:
            CocoParserError: Quando o valor não é numérico ou finito.
        """
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
        ):
            raise CocoParserError(
                f"O campo '{field_name}' do registro de {record_type} "
                "deve conter um número finito."
            )

        try:
            numeric_value = float(value)
        except (OverflowError, ValueError) as error:
            raise CocoParserError(
                f"O campo '{field_name}' do registro de {record_type} "
                "deve conter um número finito."
            ) from error

        if not math.isfinite(numeric_value):
            raise CocoParserError(
                f"O campo '{field_name}' do registro de {record_type} "
                "deve conter um número finito."
            )

        return numeric_value


"""
Este módulo implementa o auditor responsável por verificar
a integridade estrutural de datasets de segmentação.

Sua responsabilidade é identificar:

- IDs duplicados de imagens, categorias e anotações.
- Anotações que referenciam imagens inexistentes.
- Anotações que referenciam categorias inexistentes.
- Arquivos de imagem ausentes no sistema de arquivos.
- Máscaras RLE com dimensões incompatíveis com suas imagens.

O auditor recebe um Dataset já interpretado pelos parsers
e retorna os problemas encontrados utilizando AuditReport.

Nenhum dado do dataset é modificado durante a auditoria.
"""

from collections import Counter, defaultdict
from pathlib import Path

from quality_pipeline.models import (
    Annotation,
    Category,
    Dataset,
    Image,
    MaskSegmentation,
)

from .results import AuditIssue, AuditReport, AuditSeverity


class DatasetIntegrityAuditor:
    """
    Verifica a integridade estrutural de um Dataset.

    O auditor analisa as relações entre imagens, categorias
    e anotações, além de verificar arquivos e dimensões de
    máscaras RLE.

    Cada problema encontrado é convertido em AuditIssue
    e adicionado ao AuditReport retornado pela auditoria.
    """

    def audit(self, dataset: Dataset) -> AuditReport:
        """
        Executa todas as verificações de integridade estrutural.

        A auditoria verifica IDs duplicados, referências entre
        anotações, disponibilidade de arquivos e dimensões RLE.

        Args:
            dataset: Dataset interno que será auditado.

        Returns:
            Relatório contendo todos os problemas encontrados.

        Raises:
            TypeError: Quando o dataset ou suas coleções possuem
                       estruturas incompatíveis com os modelos.
        """
        self._validate_dataset(dataset)

        report = AuditReport()

        images_by_id = defaultdict(list)

        for image in dataset.images:
            images_by_id[image.id].append(image)

        category_ids = {
            category.id
            for category in dataset.categories
        }

        self._check_duplicate_ids(
            identifiers=[image.id for image in dataset.images],
            entity_type="Image",
            report=report,
        )

        self._check_duplicate_ids(
            identifiers=[category.id for category in dataset.categories],
            entity_type="Category",
            report=report,
        )

        self._check_duplicate_ids(
            identifiers=[annotation.id for annotation in dataset.annotations],
            entity_type="Annotation",
            report=report,
        )

        self._check_image_files(
            images=dataset.images,
            report=report,
        )

        self._check_annotation_references(
            annotations=dataset.annotations,
            images_by_id=images_by_id,
            category_ids=category_ids,
            report=report,
        )

        return report

    def _validate_dataset(self, dataset: Dataset) -> None:
        """
        Verifica se o objeto recebido possui as coleções esperadas.

        Essa validação protege o auditor contra objetos que não
        respeitem a estrutura dos modelos internos.

        Args:
            dataset: Objeto que será validado.

        Raises:
            TypeError: Quando o objeto ou algum elemento das coleções
                       não corresponde ao modelo esperado.
        """
        if not isinstance(dataset, Dataset):
            raise TypeError("O objeto recebido deve ser um Dataset.")

        collections = (
            ("images", dataset.images, Image),
            ("categories", dataset.categories, Category),
            ("annotations", dataset.annotations, Annotation),
        )

        for collection_name, collection, expected_type in collections:
            if not isinstance(collection, list):
                raise TypeError(
                    f"dataset.{collection_name} deve ser uma lista."
                )

            if not all(
                isinstance(item, expected_type)
                for item in collection
            ):
                raise TypeError(
                    f"Todos os elementos de dataset.{collection_name} "
                    f"devem ser instâncias de {expected_type.__name__}."
                )

        for image in dataset.images:
            if (
                image.resolved_path is not None
                and not isinstance(image.resolved_path, Path)
            ):
                raise TypeError(
                    "O resolved_path de Image deve ser Path ou None."
                )

    def _check_duplicate_ids(
        self,
        identifiers: list[int],
        entity_type: str,
        report: AuditReport,
    ) -> None:
        """
        Identifica IDs repetidos dentro de uma coleção.

        Cada identificador duplicado gera somente um AuditIssue,
        independentemente da quantidade de ocorrências.

        Args:
            identifiers: Lista de identificadores de uma coleção.
            entity_type: Nome do tipo de elemento analisado.
            report: Relatório que receberá os problemas encontrados.
        """
        counts = Counter(identifiers)

        code_by_entity = {
            "Image": "DUPLICATE_IMAGE_ID",
            "Category": "DUPLICATE_CATEGORY_ID",
            "Annotation": "DUPLICATE_ANNOTATION_ID",
        }

        code = code_by_entity[entity_type]

        for identifier, occurrences in counts.items():
            if occurrences <= 1:
                continue

            report.add_issue(
                AuditIssue(
                    code=code,
                    severity=AuditSeverity.ERROR,
                    message=(
                        f"O identificador {identifier} aparece "
                        f"{occurrences} vezes na coleção {entity_type}."
                    ),
                    entity_type=entity_type,
                    entity_id=identifier,
                    details={
                        "identifier": identifier,
                        "occurrences": occurrences,
                    },
                )
            )

    def _check_image_files(
        self,
        images: list[Image],
        report: AuditReport,
    ) -> None:
        """
        Verifica se os arquivos de imagem resolvidos existem.

        Imagens cujo resolved_path é None são ignoradas, pois
        não há um caminho local disponível para verificar.

        Args:
            images: Imagens pertencentes ao dataset.
            report: Relatório que receberá os problemas encontrados.
        """
        for image in images:
            if image.resolved_path is None:
                continue

            if image.resolved_path.is_file():
                continue

            report.add_issue(
                AuditIssue(
                    code="IMAGE_FILE_NOT_FOUND",
                    severity=AuditSeverity.ERROR,
                    message=(
                        f"O arquivo da imagem {image.id} "
                        "não foi encontrado no caminho resolvido."
                    ),
                    entity_type="Image",
                    entity_id=image.id,
                    details={
                        "file_name": image.file_name,
                        "resolved_path": str(image.resolved_path),
                    },
                )
            )

    def _check_annotation_references(
        self,
        annotations: list[Annotation],
        images_by_id: dict[int, list[Image]],
        category_ids: set[int],
        report: AuditReport,
    ) -> None:
        """
        Verifica as referências de imagens e categorias das anotações.

        Também verifica se as dimensões das máscaras RLE correspondem
        às dimensões da imagem associada.

        A comparação RLE só é executada quando existe exatamente
        uma imagem com o identificador referenciado. Isso evita
        resultados incorretos quando há IDs de imagens duplicados.

        Args:
            annotations: Anotações pertencentes ao dataset.
            images_by_id: Índice de imagens organizado por identificador.
            category_ids: Conjunto de IDs de categorias existentes.
            report: Relatório que receberá os problemas encontrados.
        """
        for annotation in annotations:
            matching_images = images_by_id.get(annotation.image_id, [])

            if not matching_images:
                report.add_issue(
                    AuditIssue(
                        code="ANNOTATION_IMAGE_NOT_FOUND",
                        severity=AuditSeverity.ERROR,
                        message=(
                            f"A anotação {annotation.id} referencia "
                            f"a imagem inexistente {annotation.image_id}."
                        ),
                        entity_type="Annotation",
                        entity_id=annotation.id,
                        details={
                            "annotation_id": annotation.id,
                            "image_id": annotation.image_id,
                        },
                    )
                )

            if annotation.category_id not in category_ids:
                report.add_issue(
                    AuditIssue(
                        code="ANNOTATION_CATEGORY_NOT_FOUND",
                        severity=AuditSeverity.ERROR,
                        message=(
                            f"A anotação {annotation.id} referencia "
                            f"a categoria inexistente {annotation.category_id}."
                        ),
                        entity_type="Annotation",
                        entity_id=annotation.id,
                        details={
                            "annotation_id": annotation.id,
                            "category_id": annotation.category_id,
                        },
                    )
                )

            self._check_mask_dimensions(
                annotation=annotation,
                matching_images=matching_images,
                report=report,
            )

    def _check_mask_dimensions(
        self,
        annotation: Annotation,
        matching_images: list[Image],
        report: AuditReport,
    ) -> None:
        """
        Compara as dimensões de uma máscara RLE com as da imagem.

        A verificação somente é possível quando a segmentação
        é uma MaskSegmentation e existe exatamente uma imagem
        correspondente ao image_id da anotação.

        Args:
            annotation: Anotação cuja máscara será analisada.
            matching_images: Imagens que correspondem ao image_id.
            report: Relatório que receberá os problemas encontrados.
        """
        segmentation = annotation.segmentation

        if not isinstance(segmentation, MaskSegmentation):
            return

        if len(matching_images) != 1:
            return

        image = matching_images[0]

        if (
            segmentation.width == image.width
            and segmentation.height == image.height
        ):
            return

        report.add_issue(
            AuditIssue(
                code="MASK_DIMENSIONS_MISMATCH",
                severity=AuditSeverity.ERROR,
                message=(
                    f"A máscara RLE da anotação {annotation.id} "
                    "possui dimensões diferentes da imagem associada."
                ),
                entity_type="Annotation",
                entity_id=annotation.id,
                details={
                    "annotation_id": annotation.id,
                    "image_id": image.id,
                    "mask_width": segmentation.width,
                    "mask_height": segmentation.height,
                    "image_width": image.width,
                    "image_height": image.height,
                },
            )
        )

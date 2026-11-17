
"""
Este módulo contém os testes automatizados do
DatasetIntegrityAuditor.

Os testes verificam a identificação de IDs duplicados,
referências inválidas, arquivos ausentes e inconsistências
entre as dimensões das máscaras RLE e das imagens.
"""

import pytest

from quality_pipeline.auditors import (
    AuditSeverity,
    DatasetIntegrityAuditor,
)
from quality_pipeline.models import (
    Annotation,
    Category,
    Dataset,
    Image,
    MaskSegmentation,
)


def test_audit_valid_empty_dataset():
    """
    Verifica se um dataset vazio pode ser auditado sem problemas.
    """
    auditor = DatasetIntegrityAuditor()

    report = auditor.audit(Dataset())

    assert report.total_issues == 0
    assert report.has_errors is False


def test_audit_reports_duplicate_image_ids():
    """
    Verifica se identificadores duplicados de imagens são encontrados.
    """
    dataset = Dataset(
        images=[
            Image(id=1, file_name="image_a.jpg", width=100, height=100),
            Image(id=1, file_name="image_b.jpg", width=100, height=100),
        ]
    )

    report = DatasetIntegrityAuditor().audit(dataset)

    issues = [
        issue
        for issue in report.issues
        if issue.code == "DUPLICATE_IMAGE_ID"
    ]

    assert len(issues) == 1
    assert issues[0].severity == AuditSeverity.ERROR
    assert issues[0].entity_id == 1
    assert issues[0].details["occurrences"] == 2


def test_audit_reports_duplicate_category_ids():
    """
    Verifica se identificadores duplicados de categorias são encontrados.
    """
    dataset = Dataset(
        categories=[
            Category(id=1, name="apple"),
            Category(id=1, name="pear"),
        ]
    )

    report = DatasetIntegrityAuditor().audit(dataset)

    assert any(
        issue.code == "DUPLICATE_CATEGORY_ID"
        for issue in report.issues
    )


def test_audit_reports_duplicate_annotation_ids():
    """
    Verifica se identificadores duplicados de anotações são encontrados.
    """
    dataset = Dataset(
        annotations=[
            Annotation(id=1, image_id=10, category_id=20),
            Annotation(id=1, image_id=10, category_id=20),
        ]
    )

    report = DatasetIntegrityAuditor().audit(dataset)

    assert any(
        issue.code == "DUPLICATE_ANNOTATION_ID"
        for issue in report.issues
    )


def test_audit_reports_missing_image_reference():
    """
    Verifica se uma anotação que referencia uma imagem inexistente
    gera um problema de integridade.
    """
    dataset = Dataset(
        categories=[Category(id=1, name="apple")],
        annotations=[
            Annotation(id=100, image_id=999, category_id=1),
        ],
    )

    report = DatasetIntegrityAuditor().audit(dataset)

    issues = [
        issue
        for issue in report.issues
        if issue.code == "ANNOTATION_IMAGE_NOT_FOUND"
    ]

    assert len(issues) == 1
    assert issues[0].entity_id == 100
    assert issues[0].details["image_id"] == 999


def test_audit_reports_missing_category_reference():
    """
    Verifica se uma anotação que referencia uma categoria inexistente
    gera um problema de integridade.
    """
    dataset = Dataset(
        images=[
            Image(id=10, file_name="image.jpg", width=100, height=100),
        ],
        annotations=[
            Annotation(id=100, image_id=10, category_id=999),
        ],
    )

    report = DatasetIntegrityAuditor().audit(dataset)

    issues = [
        issue
        for issue in report.issues
        if issue.code == "ANNOTATION_CATEGORY_NOT_FOUND"
    ]

    assert len(issues) == 1
    assert issues[0].entity_id == 100
    assert issues[0].details["category_id"] == 999


def test_audit_reports_missing_image_file(tmp_path):
    """
    Verifica se um caminho resolvido que não aponta para
    um arquivo existente gera um problema.
    """
    missing_path = tmp_path / "missing.jpg"

    dataset = Dataset(
        images=[
            Image(
                id=1,
                file_name="missing.jpg",
                width=100,
                height=100,
                resolved_path=missing_path,
            )
        ]
    )

    report = DatasetIntegrityAuditor().audit(dataset)

    issues = [
        issue
        for issue in report.issues
        if issue.code == "IMAGE_FILE_NOT_FOUND"
    ]

    assert len(issues) == 1
    assert issues[0].entity_id == 1


def test_audit_accepts_existing_image_file(tmp_path):
    """
    Verifica se um arquivo existente não gera problema de ausência.
    """
    image_path = tmp_path / "image.jpg"
    image_path.write_bytes(b"example image content")

    dataset = Dataset(
        images=[
            Image(
                id=1,
                file_name="image.jpg",
                width=100,
                height=100,
                resolved_path=image_path,
            )
        ]
    )

    report = DatasetIntegrityAuditor().audit(dataset)

    assert not any(
        issue.code == "IMAGE_FILE_NOT_FOUND"
        for issue in report.issues
    )


def test_audit_skips_unresolved_image_paths():
    """
    Verifica se caminhos não resolvidos são ignorados
    em vez de serem classificados como arquivos ausentes.
    """
    dataset = Dataset(
        images=[
            Image(
                id=1,
                file_name="image.jpg",
                width=100,
                height=100,
                resolved_path=None,
            )
        ]
    )

    report = DatasetIntegrityAuditor().audit(dataset)

    assert not any(
        issue.code == "IMAGE_FILE_NOT_FOUND"
        for issue in report.issues
    )


def test_audit_reports_mask_dimensions_mismatch():
    """
    Verifica se uma máscara RLE com dimensões diferentes
    das dimensões da imagem é identificada.
    """
    dataset = Dataset(
        images=[
            Image(id=1, file_name="image.jpg", width=10, height=8),
        ],
        categories=[
            Category(id=1, name="apple"),
        ],
        annotations=[
            Annotation(
                id=100,
                image_id=1,
                category_id=1,
                segmentation=MaskSegmentation(
                    width=5,
                    height=8,
                    runs=(40,),
                ),
            )
        ],
    )

    report = DatasetIntegrityAuditor().audit(dataset)

    issues = [
        issue
        for issue in report.issues
        if issue.code == "MASK_DIMENSIONS_MISMATCH"
    ]

    assert len(issues) == 1
    assert issues[0].entity_id == 100
    assert issues[0].details["mask_width"] == 5
    assert issues[0].details["image_width"] == 10


def test_audit_accepts_matching_mask_dimensions():
    """
    Verifica se uma máscara com dimensões iguais às da imagem
    não gera um problema.
    """
    dataset = Dataset(
        images=[
            Image(id=1, file_name="image.jpg", width=10, height=8),
        ],
        categories=[
            Category(id=1, name="apple"),
        ],
        annotations=[
            Annotation(
                id=100,
                image_id=1,
                category_id=1,
                segmentation=MaskSegmentation(
                    width=10,
                    height=8,
                    runs=(80,),
                ),
            )
        ],
    )

    report = DatasetIntegrityAuditor().audit(dataset)

    assert not any(
        issue.code == "MASK_DIMENSIONS_MISMATCH"
        for issue in report.issues
    )


def test_audit_does_not_compare_mask_with_missing_image():
    """
    Verifica se uma máscara não gera uma inconsistência dimensional
    adicional quando sua imagem de referência não existe.
    """
    dataset = Dataset(
        categories=[
            Category(id=1, name="apple"),
        ],
        annotations=[
            Annotation(
                id=100,
                image_id=999,
                category_id=1,
                segmentation=MaskSegmentation(
                    width=5,
                    height=5,
                    runs=(25,),
                ),
            )
        ],
    )

    report = DatasetIntegrityAuditor().audit(dataset)

    codes = {issue.code for issue in report.issues}

    assert "ANNOTATION_IMAGE_NOT_FOUND" in codes
    assert "MASK_DIMENSIONS_MISMATCH" not in codes


def test_audit_does_not_compare_mask_with_ambiguous_image_id():
    """
    Verifica se a comparação dimensional é ignorada quando
    existem imagens duplicadas com o mesmo identificador.
    """
    dataset = Dataset(
        images=[
            Image(id=1, file_name="image_a.jpg", width=10, height=8),
            Image(id=1, file_name="image_b.jpg", width=20, height=8),
        ],
        categories=[
            Category(id=1, name="apple"),
        ],
        annotations=[
            Annotation(
                id=100,
                image_id=1,
                category_id=1,
                segmentation=MaskSegmentation(
                    width=15,
                    height=8,
                    runs=(120,),
                ),
            )
        ],
    )

    report = DatasetIntegrityAuditor().audit(dataset)

    codes = {issue.code for issue in report.issues}

    assert "DUPLICATE_IMAGE_ID" in codes
    assert "MASK_DIMENSIONS_MISMATCH" not in codes


def test_audit_does_not_flag_images_without_annotations():
    """
    Verifica se imagens sem anotações continuam sendo aceitas.

    Essas imagens podem representar exemplos negativos legítimos.
    """
    dataset = Dataset(
        images=[
            Image(id=1, file_name="negative.jpg", width=100, height=100),
        ],
        categories=[
            Category(id=1, name="apple"),
        ],
    )

    report = DatasetIntegrityAuditor().audit(dataset)

    assert report.total_issues == 0


def test_audit_allows_same_id_across_different_collections():
    """
    Verifica se identificadores iguais em coleções distintas
    não são classificados como duplicados.
    """
    dataset = Dataset(
        images=[
            Image(id=1, file_name="image.jpg", width=100, height=100),
        ],
        categories=[
            Category(id=1, name="apple"),
        ],
        annotations=[
            Annotation(id=1, image_id=1, category_id=1),
        ],
    )

    report = DatasetIntegrityAuditor().audit(dataset)

    duplicate_issues = [
        issue
        for issue in report.issues
        if issue.code.startswith("DUPLICATE_")
    ]

    assert duplicate_issues == []


def test_audit_rejects_invalid_dataset_type():
    """
    Verifica se o auditor rejeita objetos que não sejam Dataset.
    """
    auditor = DatasetIntegrityAuditor()

    with pytest.raises(TypeError):
        auditor.audit([])


"""
Este script demonstra o funcionamento do DatasetIntegrityAuditor
utilizando um dataset artificial com problemas estruturais conhecidos.

A demonstração cria intencionalmente:

- IDs duplicados de imagens, categorias e anotações.
- Referências a imagens e categorias inexistentes.
- Um caminho de imagem que não existe.
- Uma máscara RLE com dimensões incompatíveis com sua imagem.

O objetivo é demonstrar que o auditor identifica cada inconsistência
e consolida os resultados em um AuditReport.

Execução a partir da raiz do projeto:

    python examples/demo_dataset_integrity.py
"""

from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

from quality_pipeline.auditors import DatasetIntegrityAuditor
from quality_pipeline.models import (
    Annotation,
    Category,
    Dataset,
    Image,
    MaskSegmentation,
)


def main() -> None:
    """
    Executa a demonstração do auditor de integridade estrutural.

    Um diretório temporário é utilizado para representar arquivos
    existentes e ausentes sem modificar os dados reais do projeto.

    Raises:
        RuntimeError: Quando alguma inconsistência esperada não
                      for identificada pelo auditor.
    """
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)

        # Cria um arquivo temporário para representar uma imagem existente.
        existing_file = root / "existing.jpg"
        existing_file.write_bytes(b"example")

        # Define um caminho que propositalmente não existe.
        missing_file = root / "missing.jpg"

        # Cria um dataset com problemas estruturais conhecidos.
        dataset = Dataset(
            images=[
                Image(
                    id=1,
                    file_name="image_a.jpg",
                    width=10,
                    height=10,
                    resolved_path=existing_file,
                ),
                Image(
                    id=1,
                    file_name="image_b.jpg",
                    width=10,
                    height=10,
                    resolved_path=existing_file,
                ),
                Image(
                    id=2,
                    file_name="missing.jpg",
                    width=10,
                    height=10,
                    resolved_path=missing_file,
                ),
                Image(
                    id=3,
                    file_name="mask.jpg",
                    width=10,
                    height=8,
                ),
            ],
            categories=[
                Category(id=10, name="apple"),
                Category(id=10, name="pear"),
                Category(id=20, name="orange"),
            ],
            annotations=[
                Annotation(
                    id=100,
                    image_id=3,
                    category_id=20,
                    segmentation=MaskSegmentation(
                        width=5,
                        height=8,
                        runs=(40,),
                    ),
                ),
                Annotation(
                    id=100,
                    image_id=3,
                    category_id=20,
                ),
                Annotation(
                    id=101,
                    image_id=999,
                    category_id=888,
                ),
            ],
        )

        # Executa a auditoria.
        auditor = DatasetIntegrityAuditor()
        report = auditor.audit(dataset)

        # Exibe o resumo do relatório.
        print("\n========== AUDITORIA DE TESTE ==========")
        print(f"Total de problemas: {report.total_issues}")
        print(f"Errors: {report.error_count}")
        print(f"Warnings: {report.warning_count}")
        print(f"Info: {report.info_count}")

        print("\nProblemas identificados:")

        for issue in report.issues:
            print(
                f"[{issue.severity.value}] "
                f"{issue.code} | "
                f"{issue.entity_type} {issue.entity_id}: "
                f"{issue.message}"
            )

        print("\nQuantidade por regra:")

        issue_counts = Counter(
            issue.code for issue in report.issues
        )

        for code, count in sorted(issue_counts.items()):
            print(f"- {code}: {count}")

        # Define quais problemas obrigatoriamente devem ser encontrados.
        expected_codes = {
            "DUPLICATE_IMAGE_ID",
            "DUPLICATE_CATEGORY_ID",
            "DUPLICATE_ANNOTATION_ID",
            "ANNOTATION_IMAGE_NOT_FOUND",
            "ANNOTATION_CATEGORY_NOT_FOUND",
            "IMAGE_FILE_NOT_FOUND",
            "MASK_DIMENSIONS_MISMATCH",
        }

        detected_codes = set(issue_counts)

        # Confere se todas as regras foram acionadas exatamente uma vez.
        if detected_codes != expected_codes:
            missing_codes = expected_codes - detected_codes
            unexpected_codes = detected_codes - expected_codes

            raise RuntimeError(
                "Resultado inesperado da auditoria. "
                f"Problemas não encontrados: {missing_codes}. "
                f"Problemas inesperados: {unexpected_codes}."
            )

        if any(count != 1 for count in issue_counts.values()):
            raise RuntimeError(
                "A quantidade de problemas por regra é diferente "
                "da quantidade esperada."
            )

        if report.total_issues != 7 or report.error_count != 7:
            raise RuntimeError(
                "A quantidade ou severidade dos problemas está incorreta."
            )

        print("\nSUCESSO: todas as inconsistências esperadas foram identificadas.")
        print("========================================")


if __name__ == "__main__":
    main()

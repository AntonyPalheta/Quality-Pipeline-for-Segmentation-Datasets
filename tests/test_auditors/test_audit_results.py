
"""
Este módulo contém os testes automatizados das estruturas
utilizadas para representar os resultados das auditorias.

Os testes verificam a classificação de severidade, a validação
de problemas individuais e o agrupamento dos resultados.
"""

import pytest

from quality_pipeline.auditors.results import (
    AuditIssue,
    AuditReport,
    AuditSeverity,
)


def test_audit_severity_values():
    """
    Verifica se os níveis de severidade disponíveis estão definidos.
    """
    assert AuditSeverity.INFO.value == "INFO"
    assert AuditSeverity.WARNING.value == "WARNING"
    assert AuditSeverity.ERROR.value == "ERROR"


def test_create_audit_issue():
    """
    Verifica a criação de um problema de auditoria válido.
    """
    issue = AuditIssue(
        code="DUPLICATE_IMAGE_ID",
        severity=AuditSeverity.ERROR,
        message="O identificador da imagem está duplicado.",
        entity_type="Image",
        entity_id=15,
        details={"image_id": 15},
    )

    assert issue.code == "DUPLICATE_IMAGE_ID"
    assert issue.severity == AuditSeverity.ERROR
    assert issue.message == "O identificador da imagem está duplicado."
    assert issue.entity_type == "Image"
    assert issue.entity_id == 15
    assert issue.details == {"image_id": 15}


def test_audit_issue_rejects_empty_code():
    """
    Verifica se o problema rejeita um código vazio.
    """
    with pytest.raises(ValueError):
        AuditIssue(
            code="",
            severity=AuditSeverity.ERROR,
            message="Problema de teste.",
        )


def test_audit_issue_rejects_empty_message():
    """
    Verifica se o problema rejeita uma mensagem vazia.
    """
    with pytest.raises(ValueError):
        AuditIssue(
            code="TEST_ERROR",
            severity=AuditSeverity.ERROR,
            message=" ",
        )


def test_audit_issue_rejects_invalid_severity():
    """
    Verifica se a severidade precisa utilizar AuditSeverity.
    """
    with pytest.raises(TypeError):
        AuditIssue(
            code="TEST_ERROR",
            severity="ERROR",
            message="Problema de teste.",
        )


def test_audit_issue_rejects_boolean_entity_id():
    """
    Verifica se valores booleanos não são aceitos como identificadores.
    """
    with pytest.raises(TypeError):
        AuditIssue(
            code="TEST_ERROR",
            severity=AuditSeverity.ERROR,
            message="Problema de teste.",
            entity_id=True,
        )


def test_audit_issue_copies_details():
    """
    Verifica se o dicionário de detalhes não compartilha
    a referência original recebida pelo problema.
    """
    details = {"image_id": 15}

    issue = AuditIssue(
        code="TEST_ERROR",
        severity=AuditSeverity.ERROR,
        message="Problema de teste.",
        details=details,
    )

    details["image_id"] = 99

    assert issue.details["image_id"] == 15


def test_create_empty_audit_report():
    """
    Verifica o comportamento de um relatório sem problemas.
    """
    report = AuditReport()

    assert report.total_issues == 0
    assert report.error_count == 0
    assert report.warning_count == 0
    assert report.info_count == 0
    assert report.has_errors is False


def test_audit_report_counts_severities():
    """
    Verifica se o relatório contabiliza corretamente
    os problemas de cada nível de severidade.
    """
    report = AuditReport(
        issues=[
            AuditIssue(
                code="ERROR_1",
                severity=AuditSeverity.ERROR,
                message="Primeiro erro.",
            ),
            AuditIssue(
                code="WARNING_1",
                severity=AuditSeverity.WARNING,
                message="Primeiro alerta.",
            ),
            AuditIssue(
                code="ERROR_2",
                severity=AuditSeverity.ERROR,
                message="Segundo erro.",
            ),
            AuditIssue(
                code="INFO_1",
                severity=AuditSeverity.INFO,
                message="Informação.",
            ),
        ]
    )

    assert report.total_issues == 4
    assert report.error_count == 2
    assert report.warning_count == 1
    assert report.info_count == 1
    assert report.has_errors is True


def test_audit_report_add_issue():
    """
    Verifica se um problema pode ser adicionado ao relatório.
    """
    report = AuditReport()

    issue = AuditIssue(
        code="TEST_ERROR",
        severity=AuditSeverity.ERROR,
        message="Problema de teste.",
    )

    report.add_issue(issue)

    assert report.total_issues == 1
    assert report.issues[0] == issue


def test_audit_report_rejects_invalid_issue():
    """
    Verifica se o relatório rejeita elementos que não sejam AuditIssue.
    """
    report = AuditReport()

    with pytest.raises(TypeError):
        report.add_issue("Problema inválido")


def test_audit_report_extend():
    """
    Verifica se vários problemas podem ser adicionados ao relatório.
    """
    report = AuditReport()

    issues = [
        AuditIssue(
            code="ERROR_1",
            severity=AuditSeverity.ERROR,
            message="Primeiro erro.",
        ),
        AuditIssue(
            code="WARNING_1",
            severity=AuditSeverity.WARNING,
            message="Primeiro alerta.",
        ),
    ]

    report.extend(issues)

    assert report.total_issues == 2
    assert report.error_count == 1
    assert report.warning_count == 1


def test_audit_report_extend_rejects_invalid_items():
    """
    Verifica se uma coleção inválida é rejeitada sem modificar
    os problemas que já estão no relatório.
    """
    report = AuditReport(
        issues=[
            AuditIssue(
                code="EXISTING_ERROR",
                severity=AuditSeverity.ERROR,
                message="Erro já registrado.",
            )
        ]
    )

    with pytest.raises(TypeError):
        report.extend(
            [
                AuditIssue(
                    code="NEW_ERROR",
                    severity=AuditSeverity.ERROR,
                    message="Novo erro.",
                ),
                "Problema inválido",
            ]
        )

    assert report.total_issues == 1

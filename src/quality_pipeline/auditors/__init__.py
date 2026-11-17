
"""
Este pacote reúne os componentes responsáveis pelas auditorias
de qualidade dos datasets de segmentação.
"""

from .dataset_integrity_auditor import DatasetIntegrityAuditor
from .results import AuditIssue, AuditReport, AuditSeverity

__all__ = [
    "AuditIssue",
    "AuditReport",
    "AuditSeverity",
    "DatasetIntegrityAuditor",
]

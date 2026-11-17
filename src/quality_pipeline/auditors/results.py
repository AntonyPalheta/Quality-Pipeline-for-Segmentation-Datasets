
"""
Este módulo define as estruturas padronizadas utilizadas para
representar e agrupar os resultados das auditorias do projeto.

Sua responsabilidade é:

- Definir os níveis de severidade dos problemas encontrados.
- Representar individualmente cada problema de auditoria.
- Reunir os problemas em um relatório.
- Disponibilizar contadores para consultar os resultados.

Todos os auditores deverão utilizar essas estruturas para
retornar resultados consistentes, independentemente do tipo
de verificação executada.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum


class AuditSeverity(str, Enum):
    """
    Define os níveis de severidade dos resultados de auditoria.

    INFO:
        Informação relevante que não representa necessariamente
        um problema.

    WARNING:
        Situação potencialmente problemática que merece revisão.

    ERROR:
        Violação objetiva de uma regra de integridade ou qualidade.
    """

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class AuditIssue:
    """
    Representa um problema ou uma observação identificada
    durante uma auditoria.

    Attributes:
        code: Identificador padronizado do problema.
        severity: Nível de severidade do problema.
        message: Descrição compreensível do que foi encontrado.
        entity_type: Tipo de elemento afetado, como Image ou Annotation.
        entity_id: Identificador do elemento afetado, quando disponível.
        details: Informações adicionais relacionadas ao problema.
    """

    code: str
    severity: AuditSeverity
    message: str
    entity_type: str | None = None
    entity_id: int | str | None = None
    details: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        Valida os campos do problema para garantir que todo
        AuditIssue possua informações mínimas e consistentes.

        Raises:
            ValueError: Quando campos textuais obrigatórios estão vazios.
            TypeError: Quando algum campo possui um tipo incompatível.
        """
        if not isinstance(self.code, str) or not self.code.strip():
            raise ValueError("O código do problema não pode ser vazio.")

        if not isinstance(self.severity, AuditSeverity):
            raise TypeError("severity deve ser uma instância de AuditSeverity.")

        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError("A mensagem do problema não pode ser vazia.")

        if self.entity_type is not None:
            if not isinstance(self.entity_type, str) or not self.entity_type.strip():
                raise ValueError("entity_type deve ser uma string não vazia.")

        if self.entity_id is not None:
            if isinstance(self.entity_id, bool) or not isinstance(
                self.entity_id, (int, str)
            ):
                raise TypeError("entity_id deve ser um inteiro, uma string ou None.")

        if not isinstance(self.details, dict):
            raise TypeError("details deve ser um dicionário.")

        if not all(isinstance(key, str) for key in self.details):
            raise TypeError("Todas as chaves de details devem ser strings.")

        # Cria uma cópia para não manter uma referência externa ao dicionário.
        object.__setattr__(self, "details", dict(self.details))


@dataclass(slots=True)
class AuditReport:
    """
    Reúne os problemas identificados durante uma ou mais auditorias.

    O relatório permite adicionar resultados de diferentes auditores
    e consultar a quantidade de problemas por nível de severidade.

    Attributes:
        issues: Lista dos problemas identificados.
    """

    issues: list[AuditIssue] = field(default_factory=list)

    def __post_init__(self) -> None:
        """
        Valida os elementos recebidos na criação do relatório.

        Raises:
            TypeError: Se a coleção ou algum elemento for inválido.
        """
        if not isinstance(self.issues, list):
            raise TypeError("issues deve ser uma lista.")

        if not all(isinstance(issue, AuditIssue) for issue in self.issues):
            raise TypeError("Todos os elementos de issues devem ser AuditIssue.")

        # Cria uma nova lista para evitar compartilhar a coleção recebida.
        self.issues = list(self.issues)

    def add_issue(self, issue: AuditIssue) -> None:
        """
        Adiciona um problema individual ao relatório.

        Args:
            issue: Problema de auditoria que será adicionado.

        Raises:
            TypeError: Se o objeto informado não for AuditIssue.
        """
        if not isinstance(issue, AuditIssue):
            raise TypeError("O problema adicionado deve ser AuditIssue.")

        self.issues.append(issue)

    def extend(self, issues: Iterable[AuditIssue]) -> None:
        """
        Adiciona vários problemas ao relatório.

        A coleção é validada antes de modificar o relatório, evitando
        adicionar apenas parte dos resultados quando houver um item inválido.

        Args:
            issues: Coleção de problemas que será adicionada.

        Raises:
            TypeError: Se algum elemento não for AuditIssue.
        """
        new_issues = list(issues)

        if not all(isinstance(issue, AuditIssue) for issue in new_issues):
            raise TypeError("Todos os elementos adicionados devem ser AuditIssue.")

        self.issues.extend(new_issues)

    @property
    def total_issues(self) -> int:
        """
        Retorna a quantidade total de problemas encontrados.

        Returns:
            Número total de problemas presentes no relatório.
        """
        return len(self.issues)

    @property
    def error_count(self) -> int:
        """
        Retorna a quantidade de problemas classificados como ERROR.

        Returns:
            Número de erros encontrados.
        """
        return sum(
            issue.severity == AuditSeverity.ERROR for issue in self.issues
        )

    @property
    def warning_count(self) -> int:
        """
        Retorna a quantidade de problemas classificados como WARNING.

        Returns:
            Número de alertas encontrados.
        """
        return sum(
            issue.severity == AuditSeverity.WARNING for issue in self.issues
        )

    @property
    def info_count(self) -> int:
        """
        Retorna a quantidade de problemas classificados como INFO.

        Returns:
            Número de informações registradas.
        """
        return sum(
            issue.severity == AuditSeverity.INFO for issue in self.issues
        )

    @property
    def has_errors(self) -> bool:
        """
        Informa se o relatório possui pelo menos um erro.

        Returns:
            True se existir algum ERROR; caso contrário, False.
        """
        return self.error_count > 0

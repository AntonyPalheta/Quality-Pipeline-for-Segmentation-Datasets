
"""
Este módulo define o modelo Image, responsável por representar
uma imagem pertencente a um dataset de segmentação.

A classe armazena os identificadores, as dimensões e os caminhos
associados à imagem.

O caminho original do dataset é preservado separadamente do
caminho local resolvido, permitindo trabalhar com diferentes
estruturas de diretórios e formatos de anotação.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Image:
    """
    Representa uma imagem existente em um dataset.

    Attributes:
        id: Identificador único da imagem dentro do modelo interno
            do dataset.
        file_name: Caminho ou nome original da imagem, conforme
                   identificado na estrutura do dataset.
        width: Largura da imagem em pixels.
        height: Altura da imagem em pixels.
        resolved_path: Caminho local completo da imagem, quando
                       disponível. Pode ser None caso ainda não
                       tenha sido resolvido pelo parser.
    """

    id: int
    file_name: str
    width: int
    height: int
    resolved_path: Path | None = None

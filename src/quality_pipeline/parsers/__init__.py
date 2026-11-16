
"""
Este módulo define a interface pública do pacote parsers.

Sua responsabilidade é disponibilizar os parsers implementados
para que possam ser importados diretamente pelo pacote parsers.
"""

from .coco_parser import CocoParser, CocoParserError


__all__ = [
    "CocoParser",
    "CocoParserError",
]


"""
Este módulo implementa as conversões de segmentações RLE
provenientes do formato COCO.

Sua responsabilidade é:

- Interpretar RLE não comprimido.
- Decodificar RLE comprimido.
- Validar as dimensões e contagens recebidas.
- Reconstruir a máscara na ordem column-major utilizada pelo COCO.
- Converter a representação para RLE row-major.
- Retornar uma instância do modelo MaskSegmentation.

O módulo mantém a lógica de conversão RLE separada do CocoParser,
facilitando os testes e a manutenção do algoritmo.
"""

from typing import Any

from ..models import MaskSegmentation


class CocoRLEError(ValueError):
    """
    Representa erros encontrados durante a interpretação
    de uma segmentação RLE proveniente do formato COCO.
    """


def decode_coco_rle(rle: Any) -> MaskSegmentation:
    """
    Decodifica uma representação RLE do COCO para MaskSegmentation.

    O COCO utiliza uma representação column-major, enquanto
    o modelo interno utiliza row-major.

    Por isso, além de decodificar as contagens, esta função
    reconstrói a máscara e converte sua ordem de armazenamento.

    Args:
        rle: Dicionário contendo os campos size e counts.

    Returns:
        Instância de MaskSegmentation com RLE interno row-major.

    Raises:
        CocoRLEError: Quando a estrutura, dimensões ou contagens
                      da representação RLE são inválidas.
    """
    if not isinstance(rle, dict):
        raise CocoRLEError(
            "A representação RLE deve ser um objeto."
        )

    size = rle.get("size")
    counts = rle.get("counts")

    if not isinstance(size, (list, tuple)) or len(size) != 2:
        raise CocoRLEError(
            "O campo 'size' deve conter altura e largura."
        )

    height, width = size

    _validate_dimension(height, "altura")
    _validate_dimension(width, "largura")

    total_pixels = height * width

    if isinstance(counts, (list, tuple)):
        decoded_counts = counts

    elif isinstance(counts, (str, bytes)):
        decoded_counts = _decode_compressed_counts(counts)

    else:
        raise CocoRLEError(
            "O campo 'counts' deve ser uma lista, string ou bytes."
        )

    validated_counts = _validate_run_counts(
        decoded_counts,
        total_pixels,
    )

    internal_runs = _convert_column_major_to_row_major(
        validated_counts,
        height,
        width,
    )

    return MaskSegmentation(
        width=width,
        height=height,
        runs=internal_runs,
    )


def _validate_dimension(value: Any, field_name: str) -> None:
    """
    Verifica se uma dimensão da máscara é um inteiro positivo.

    Valores booleanos são rejeitados, pois bool é uma subclasse de int.

    Args:
        value: Dimensão que será validada.
        field_name: Nome da dimensão, utilizado na mensagem de erro.

    Raises:
        CocoRLEError: Quando a dimensão não é um inteiro positivo.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise CocoRLEError(
            f"A {field_name} da máscara deve ser um inteiro."
        )

    if value <= 0:
        raise CocoRLEError(
            f"A {field_name} da máscara deve ser positiva."
        )


def _decode_compressed_counts(counts: str | bytes) -> tuple[int, ...]:
    """
    Decodifica as contagens RLE comprimidas utilizadas pelo COCO.

    A codificação utiliza grupos de cinco bits de dados por caractere,
    com bits adicionais para indicar continuação e sinal.

    A partir da quarta contagem, o COCO utiliza uma codificação
    diferencial: o valor armazenado deve ser somado à contagem
    situada duas posições antes.

    Args:
        counts: String ou sequência de bytes do RLE comprimido.

    Returns:
        Tupla contendo as contagens decodificadas.

    Raises:
        CocoRLEError: Quando a string contém caracteres inválidos,
                      sequências incompletas ou contagens negativas.
    """
    if isinstance(counts, bytes):
        try:
            encoded = counts.decode("ascii")
        except UnicodeDecodeError as error:
            raise CocoRLEError(
                "O RLE comprimido deve utilizar caracteres ASCII."
            ) from error
    else:
        encoded = counts

    if not encoded:
        raise CocoRLEError(
            "A sequência RLE comprimida não pode estar vazia."
        )

    decoded_counts = []
    position = 0

    while position < len(encoded):
        value = 0
        shift = 0
        chunk_count = 0

        while True:
            if position >= len(encoded):
                raise CocoRLEError(
                    "A sequência RLE comprimida está incompleta."
                )

            character_value = ord(encoded[position]) - 48

            if not 0 <= character_value <= 63:
                raise CocoRLEError(
                    "O RLE comprimido contém um caractere inválido."
                )

            position += 1

            # Os cinco bits inferiores representam os dados.
            value |= (character_value & 0x1F) << shift

            # O sexto bit indica se existe outro grupo.
            more = bool(character_value & 0x20)

            shift += 5
            chunk_count += 1

            if not more:
                # Aplica a extensão de sinal quando necessário.
                if character_value & 0x10:
                    value |= -1 << shift

                break

            # As contagens COCO utilizam inteiros sem sinal de 32 bits.
            # Sete grupos de cinco bits são suficientes para representá-los.
            if chunk_count >= 7:
                raise CocoRLEError(
                    "O RLE comprimido possui uma sequência excessivamente longa."
                )

        # A partir da quarta contagem, aplica a codificação diferencial.
        if len(decoded_counts) > 2:
            value += decoded_counts[-2]

        if value < 0:
            raise CocoRLEError(
                "O RLE comprimido produziu uma contagem negativa."
            )

        decoded_counts.append(value)

    return tuple(decoded_counts)


def _validate_run_counts(
    counts: Any,
    total_pixels: int,
) -> tuple[int, ...]:
    """
    Valida uma sequência de contagens RLE.

    Verifica:
    - A existência de pelo menos uma contagem.
    - Tipos inteiros, sem aceitar booleanos.
    - Ausência de contagens negativas.
    - Ausência de segmentos vazios após a primeira contagem.
    - Correspondência entre a soma das contagens e o total de pixels.

    Args:
        counts: Sequência de contagens RLE.
        total_pixels: Quantidade total de pixels da máscara.

    Returns:
        Tupla de contagens validadas.

    Raises:
        CocoRLEError: Quando a sequência é inválida.
    """
    if not isinstance(counts, (list, tuple)) or not counts:
        raise CocoRLEError(
            "A sequência RLE deve conter pelo menos uma contagem."
        )

    validated_counts = []
    represented_pixels = 0

    for index, run_length in enumerate(counts):
        if (
            isinstance(run_length, bool)
            or not isinstance(run_length, int)
        ):
            raise CocoRLEError(
                "Todas as contagens RLE devem ser inteiros."
            )

        if run_length < 0:
            raise CocoRLEError(
                "As contagens RLE não podem ser negativas."
            )

        if index > 0 and run_length == 0:
            raise CocoRLEError(
                "Somente a primeira contagem RLE pode ser zero."
            )

        represented_pixels += run_length

        if represented_pixels > total_pixels:
            raise CocoRLEError(
                "A soma das contagens RLE excede o total de pixels da máscara."
            )

        validated_counts.append(run_length)

    if represented_pixels != total_pixels:
        raise CocoRLEError(
            "A soma das contagens RLE deve corresponder "
            "à quantidade total de pixels da máscara. "
            f"Esperado: {total_pixels}; "
            f"recebido: {represented_pixels}."
        )

    return tuple(validated_counts)


def _convert_column_major_to_row_major(
    counts: tuple[int, ...],
    height: int,
    width: int,
) -> tuple[int, ...]:
    """
    Converte uma sequência RLE column-major para row-major.

    Primeiro reconstrói a máscara binária na ordem utilizada pelo COCO.
    Depois reorganiza os pixels para a ordem utilizada pelo modelo interno.

    A máscara é armazenada temporariamente em bytearray, evitando
    o custo de memória de uma lista Python contendo um inteiro por pixel.

    Args:
        counts: Contagens RLE COCO previamente validadas.
        height: Altura da máscara.
        width: Largura da máscara.

    Returns:
        Tupla de contagens RLE na ordem row-major.

    Raises:
        CocoRLEError: Quando não é possível materializar a máscara
                      devido a limitações de memória.
    """
    total_pixels = height * width

    try:
        # Reconstrói a máscara na ordem column-major do COCO.
        column_major_mask = bytearray(total_pixels)

        position = 0
        is_foreground = False

        for run_length in counts:
            next_position = position + run_length

            if is_foreground and run_length > 0:
                column_major_mask[position:next_position] = (
                    b"\x01" * run_length
                )

            position = next_position
            is_foreground = not is_foreground

        # Transpõe a disposição dos pixels para row-major.
        row_major_mask = bytearray(total_pixels)

        for row in range(height):
            row_start = row * width
            row_end = row_start + width

            row_major_mask[row_start:row_end] = (
                column_major_mask[row::height]
            )

    except (MemoryError, OverflowError) as error:
        raise CocoRLEError(
            "Não foi possível reconstruir a máscara devido "
            "ao seu tamanho ou à memória disponível."
        ) from error

    # Codifica a máscara row-major em sequências alternadas.
    row_major_runs = []

    position = 0
    current_value = 0

    while position < total_pixels:
        next_value = 1 - current_value

        next_position = row_major_mask.find(
            bytes((next_value,)),
            position,
        )

        if next_position == -1:
            next_position = total_pixels

        row_major_runs.append(next_position - position)

        position = next_position
        current_value = next_value

    return tuple(row_major_runs)

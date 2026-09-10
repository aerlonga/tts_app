from __future__ import annotations

import re

# Regras de pronúncia aplicadas ao texto antes de enviar para o TTS.
# O modelo não aceita SSML, então a correção é feita reescrevendo o texto
# com a grafia fonética esperada em português.

LETTER_NAMES_PT = {
    "A": "á",
    "B": "bê",
    "C": "cê",
    "D": "dê",
    "E": "é",
    "F": "éfe",
    "G": "gê",
    "H": "agá",
    "I": "i",
    "J": "jota",
    "K": "cá",
    "L": "éle",
    "M": "eme",
    "N": "ene",
    "O": "ó",
    "P": "pê",
    "Q": "quê",
    "R": "erre",
    "S": "esse",
    "T": "tê",
    "U": "u",
    "V": "vê",
    "W": "dáblio",
    "X": "xis",
    "Y": "ípsilon",
    "Z": "zê",
}

# Siglas que devem ser soletradas letra a letra (match sensível a maiúsculas).
SPELLED_ACRONYMS = ("GO", "BR", "DF", "MG", "SP", "CPF", "CNPJ")

# Siglas que devem ser lidas como palavra (nunca soletradas).
WORD_ACRONYMS = ("GOINFRA",)

_HIGHWAY_RE = re.compile(
    r"\b(" + "|".join(SPELLED_ACRONYMS) + r")\s*[-–]?\s*(\d{2,4})\b"
)
_EMAIL_RE = re.compile(r"\b([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")


LANGUAGE_CODES = {
    "pt": "pt-BR",
    "en": "en-US",
    "es": "es-US",
    "fr": "fr-FR",
    "de": "de-DE",
    "it": "it-IT",
}


def resolve_language_code(language: str) -> str:
    """'pt' -> 'pt-BR'. Códigos completos ('pt-PT') passam direto."""
    if "-" in language:
        return language
    return LANGUAGE_CODES.get(language.lower(), "pt-BR")


def spell_out(token: str) -> str:
    """'GO' -> 'gê-ó'."""
    return "-".join(LETTER_NAMES_PT.get(char.upper(), char) for char in token)


def _spell_digits(digits: str) -> str:
    names = {
        "0": "zero",
        "1": "um",
        "2": "dois",
        "3": "três",
        "4": "quatro",
        "5": "cinco",
        "6": "seis",
        "7": "sete",
        "8": "oito",
        "9": "nove",
    }
    return " ".join(names.get(char, char) for char in digits)


def _speak_label(label: str) -> str:
    """Rótulo de domínio: siglas curtas são soletradas, palavras ficam como estão."""
    return spell_out(label) if len(label) <= 2 else label


def _speak_email(match: re.Match[str]) -> str:
    local = " ponto ".join(_speak_label(part) for part in match.group(1).split("."))
    domain = " ponto ".join(_speak_label(part) for part in match.group(2).split("."))
    return f"{local} arroba {domain}"


def _protect_word_acronyms(text: str) -> tuple[str, dict[str, str]]:
    placeholders: dict[str, str] = {}
    for index, acronym in enumerate(WORD_ACRONYMS):
        token = f"\x00{index}\x00"
        pattern = re.compile(rf"\b{re.escape(acronym)}\b", re.IGNORECASE)
        if pattern.search(text):
            placeholders[token] = acronym.capitalize()
            text = pattern.sub(token, text)
    return text, placeholders


def apply_pronunciation(text: str, *, language: str = "pt") -> str:
    """Reescreve trechos que o TTS costuma pronunciar errado.

    - Siglas de rodovia/estado são soletradas: GO -> gê-ó, GO-060 -> gê-ó zero seis zero.
    - Siglas que são lidas como palavra (GOINFRA) ficam intactas.
    - E-mails viram 'usuario arroba dominio ponto br'.
    """
    if not language.lower().startswith("pt"):
        return text

    text = _EMAIL_RE.sub(_speak_email, text)

    text, placeholders = _protect_word_acronyms(text)

    text = _HIGHWAY_RE.sub(
        lambda match: f"{spell_out(match.group(1))} {_spell_digits(match.group(2))}",
        text,
    )

    for acronym in SPELLED_ACRONYMS:
        text = re.sub(
            rf"\b{re.escape(acronym)}\b",
            spell_out(acronym),
            text,
        )

    for token, value in placeholders.items():
        text = text.replace(token, value)

    return text

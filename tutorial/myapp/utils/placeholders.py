import re

DROPDOWN_RE = re.compile(r'\{([^{}]+)\}\[([^\]]+)\]')
INPUT_RE = re.compile(r'\{([^{}\[\]]+)\}(?!\[)')
PLACEHOLDER_RE = re.compile(r'\{([^{}]+)\}')


def find_dropdowns(sql: str):
    """All dropdowns {name}[SQL] as list of (name, dropdown_sql)."""
    return DROPDOWN_RE.findall(sql)


def find_inputs(sql: str):
    """Names of the free input placeholders {name} (no duplicates, order kept, no dropdowns)."""
    dropdown_names = {name for name, _ in find_dropdowns(sql)}
    names = list(dict.fromkeys(INPUT_RE.findall(sql)))
    return [name for name in names if name not in dropdown_names]


def strip_dropdown_sql(sql: str) -> str:
    """Removes the [SQL] directly behind a {name}; other brackets (e.g. GLOB '[a-z]*') stay."""
    return re.sub(r'(\{[^{}]+\})\[[^\]]+\]', r'\1', sql)


def open_quote(text: str) -> str:
    """The quote character ' or " of the string literal that is still open at the end of text ('' if none)."""
    quote = ''
    for char in text:
        if quote == '':
            if char in ('"', "'"):
                quote = char
        elif char == quote:
            quote = ''  # a doubled quote closes and reopens the literal
    return quote


def substitute_placeholders(sql: str, values: dict) -> str:
    """Replaces {name} by values[name] in one pass; unknown placeholders stay.

    Inside a '...' or "..." literal the quote character in the value is doubled.
    """
    def replace(match):
        name = match.group(1)
        if name not in values:
            return match.group(0)
        value = str(values[name])
        quote = open_quote(sql[:match.start()])
        if quote:
            value = value.replace(quote, quote * 2)
        return value

    return PLACEHOLDER_RE.sub(replace, sql)

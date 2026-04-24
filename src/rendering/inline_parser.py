import re
from typing import List, Tuple

InlineToken = Tuple[str, str]

_CODE_TAG_RE = re.compile(r"<code>(.*?)</code>", re.DOTALL)


def split_inline(text: str) -> List[InlineToken]:
    if not text:
        return []

    parts = _CODE_TAG_RE.split(text)

    out: List[InlineToken] = []

    # split → [text, code, text, code...]
    for i, part in enumerate(parts):
        if not part:
            continue

        # code capture group positions
        if i % 2 == 1:
            out.append(("inline_code", part))
        else:
            out.append(("text", part))

    return out


"""The Markdown readers against the page: each reads a section as CommonMark renders it.

A deterministic corpus: every combination of a prefix, a heading form, a body and a line
ending, for `## Dependencies` and `## For the cut`, read by `conduct.py` and by
`brief_check.py` and by an oracle that renders the document and reads its HTML.
Why: 0103-fewer-rounds design D6.
"""

import importlib.util
import itertools
import re
import runpy
from collections.abc import Iterator
from html.parser import HTMLParser
from pathlib import Path
from types import ModuleType
from typing import Any

from markdown_it import MarkdownIt

_REPO = Path(__file__).resolve().parent.parent
_CONDUCT = _REPO / "skills" / "mf-ship" / "scripts" / "conduct.py"
_BRIEF = _REPO / "skills" / "mf-plan" / "scripts" / "brief_check.py"
_TABLE = (
    "| item | package | constraint | why |\n|---|---|---|---|\n"
    "| x | left-pad | 1.3.0 | a pad |\n"
)
_NOTED = _TABLE.replace("| x |", "#- note\n| x |")
_PREFIXES = (
    "",
    "```x`\n",
    "```\nplain\n```\n",
    "~~~\n{h}\n~~~\n",
    "<h2>{t}</h2>\n",
    "{glyph}\n",
    "    {h}\n",
    "> {h}\n",
    "#- note\n",
)
_FORMS = ("{h}", " {h}", "{h} ##", "{t}\n---", "##\t{t}")
_BODIES = ("None.\n", _TABLE, _NOTED, f"{_TABLE}```\n")
_ENDINGS = ("\n", "\r\n", "\r")
_LONE = re.compile(r"\r(?!\n)")


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("brief_check", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


brief_check = _load(_BRIEF)
conduct = runpy.run_path(str(_CONDUCT))


class _Page(HTMLParser):
    """A rendered page's `h1` and `h2` texts, and the table rows under each."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.sections: list[tuple[str | None, list[list[str]]]] = []
        self._buffer: str | None = None
        self._row: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("h1", "h2"):
            self.sections.append((None, []))
            self._buffer = ""
        elif tag in ("td", "th"):
            self._buffer = ""
        elif tag == "tr":
            self._row = []

    def handle_data(self, data: str) -> None:
        if self._buffer is not None:
            self._buffer += data

    def handle_endtag(self, tag: str) -> None:
        if tag in ("h1", "h2") and self._buffer is not None:
            self.sections[-1] = (self._buffer if tag == "h2" else None, [])
            self._buffer = None
        elif tag in ("td", "th"):
            self._row.append((self._buffer or "").strip())
            self._buffer = None
        elif tag == "tr" and self.sections:
            self.sections[-1][1].append(self._row)


def _page(document: str) -> _Page:
    page = _Page()
    page.feed(MarkdownIt("commonmark").enable("table").render(document))
    page.close()
    return page


def _documents() -> Iterator[tuple[str, str]]:
    """Yield each heading under test and a document of one combination."""
    for heading in ("## Dependencies", "## For the cut"):
        title = heading.removeprefix("## ")
        glyph = re.sub("[eo]", lambda m: {"e": "е", "o": "о"}[m[0]], heading, count=1)
        shape: dict[str, Any] = {"h": heading, "t": title, "glyph": glyph}
        for prefix, form, body, ending in itertools.product(
            _PREFIXES, _FORMS, _BODIES, _ENDINGS
        ):
            text = prefix.format(**shape) + form.format(**shape) + "\n" + body
            yield heading, text.replace("\n", ending)


def _disagrees(heading: str, document: str) -> list[str]:
    """Return how the two scripts' readings differ from the page's."""
    found: list[str] = []
    title = heading.removeprefix("## ")
    page = _page(document)
    reading = [rows for text, rows in page.sections if text == title]
    expected = (reading[0] if len(reading) == 1 else None) if reading else []
    rows = conduct["_rows"](document, heading)
    if conduct["_headed"](document, heading) and rows is not None and rows != expected:
        found.append(f"conduct reads {rows!r}, the page {expected!r}")
    halted = brief_check.headings(document) or _LONE.search(document)
    if not halted:
        fold = {brief_check.fold(h): h for h in brief_check.HEADINGS}
        keys = sorted(
            key for key, _ in brief_check.headed(document) if key in fold.values()
        )
        texts = sorted(
            fold[brief_check.fold(t)]
            for t, _ in page.sections
            if t and brief_check.fold(t) in fold
        )
        if keys != texts:
            found.append(f"brief_check keys {keys!r}, the page {texts!r}")
    return found


def test_the_markdown_readers_agree_with_the_rendered_page() -> None:
    documents = list(_documents())
    disagree = [
        (heading, document, why)
        for heading, document in documents
        if (why := _disagrees(heading, document))
    ]
    assert disagree == []
    # The corpus reads past the halts: some documents are read, not refused.
    read = [
        document
        for heading, document in documents
        if conduct["_headed"](document, heading) and conduct["_rows"](document, heading)
    ]
    assert read

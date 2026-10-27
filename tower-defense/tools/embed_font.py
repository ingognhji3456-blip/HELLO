#!/usr/bin/env python3
"""Embed a subset of the Galmuri11 pixel font into ../index.html.

The game page carries its own font so Korean text looks the same offline and on
every device. Only the characters that appear in index.html are kept, so after
adding new Korean text run this again or the new letters fall back to the
system font.

Usage:
    pip install fonttools brotli
    python3 tools/embed_font.py path/to/Galmuri11.ttf

Galmuri11.ttf comes from https://github.com/quiple/galmuri (also the npm
package "galmuri", file dist/Galmuri11.ttf). Galmuri is (c) Lee Minseo and is
licensed under the SIL Open Font License 1.1; the embedded subset is renamed
to "TDPixel" in the page.
"""
import base64
import io
import pathlib
import re
import sys

from fontTools import subset
from fontTools.ttLib import TTFont

PAGE = pathlib.Path(__file__).resolve().parent.parent / "index.html"
BLOCK = re.compile(r'(<style id="font-face">)(.*?)(</style>)', re.S)


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    html = PAGE.read_text(encoding="utf-8")
    if not BLOCK.search(html):
        sys.exit('index.html has no <style id="font-face"> block')
    text = BLOCK.sub(r"\1\3", html)
    chars = {c for c in text if ord(c) >= 0x80} | {chr(c) for c in range(0x20, 0x7F)}

    font = TTFont(sys.argv[1])
    cmap = font.getBestCmap()
    missing = sorted(c for c in chars if ord(c) not in cmap)
    if missing:
        print("not in the font (system fallback):", " ".join(missing))

    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["*"]
    opts.name_IDs = ["*"]
    opts.notdef_outline = True
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=[ord(c) for c in chars])
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    data = base64.b64encode(buf.getvalue()).decode("ascii")

    css = (
        "/* Galmuri11 subset (c) Lee Minseo, SIL Open Font License 1.1; regenerate with tools/embed_font.py */\n"
        '@font-face { font-family: "TDPixel"; src: url(data:font/woff2;base64,'
        + data
        + ') format("woff2"); font-display: block; }\n'
    )
    PAGE.write_text(BLOCK.sub(lambda m: m.group(1) + css + m.group(3), html), encoding="utf-8")
    print(f"embedded {len(chars)} characters, {len(buf.getvalue())} bytes of woff2")


if __name__ == "__main__":
    main()

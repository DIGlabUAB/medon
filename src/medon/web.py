"""Build a single file web form. The page runs offline and sends nothing anywhere."""
from __future__ import annotations

import json
from importlib import resources

from .engine import load_all
from .render import CSS as REPORT_CSS, DISCLAIMER, FWCOL, THEME_JS


def _read(*parts):
    return resources.files("medon").joinpath("data", "web", *parts).read_text(encoding="utf-8")


def _js(obj):
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def build_page(org=None):
    data = load_all()
    data["disclaimer"] = DISCLAIMER
    data["report"] = {"css": REPORT_CSS, "fwcol": FWCOL, "theme_js": THEME_JS}
    page = _read("template.html")
    data_js = f"window.MEDON_DATA={_js(data)};window.MEDON_ORG={_js(org or {})};"
    return (page.replace("/*DATA*/", data_js)
                .replace("/*ENGINE*/", _read("engine.js"))
                .replace("/*APP*/", _read("app.js")))

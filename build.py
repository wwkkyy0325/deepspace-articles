#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the static site from the bilingual Markdown sources.

Usage:
    pip install -r requirements.txt
    python build.py

Outputs:
    index.html
    en/<slug>.html
    zh/<slug>.html

The Markdown files remain the source of truth; edit them and re-run this script.
"""

from __future__ import annotations

import html
import pathlib
import re

import markdown

ROOT = pathlib.Path(__file__).resolve().parent
EN = ROOT / "en"
ZH = ROOT / "zh"

ARTICLES = {
    "from-expansion-to-convergence": {
        "en": EN / "from-expansion-to-convergence.md",
        "title_en": "From Expansion to Convergence",
        "desc_en": "How a general-purpose agent runtime evolved from capability expansion to system convergence: thin UI, thick capability; single source of truth; five-layer compression; evidence-based verification.",
        "title_zh": "从展开到收束",
        "desc_zh": "一个通用 Agent 运行时如何从能力展开走向系统收束：薄界面厚能力、单一事实源、五层压缩、基于证据的验证。",
    },
    "development-as-a-verifiable-system": {
        "en": EN / "development-as-a-verifiable-system.md",
        "title_en": "Development as a Verifiable System",
        "desc_en": "A cross-project engineering method: four loops, six costs, five principles, small commits, short-branch validation, and reusable templates.",
        "title_zh": "把开发做成一个可验证的系统",
        "desc_zh": "一套跨项目的工程方法：四个闭环、六种成本、五条原则、小步提交、短分支验证，以及可直接复用的模板。",
    },
}

# Identify the Chinese sources by their opening H1, so the script does not
# depend on Chinese filenames or the shell's locale.
zh_sources = list(ZH.glob("*.md"))
for slug, item in ARTICLES.items():
    if slug == "from-expansion-to-convergence":
        item["zh"] = next(p for p in zh_sources if p.read_text(encoding="utf-8").startswith("# 从展开到收束"))
    else:
        item["zh"] = next(p for p in zh_sources if p.read_text(encoding="utf-8").startswith("# 把开发做成一个可验证的系统"))

NAV = """  <header class="site-header">
    <a class="brand" href="{home}">DeepSpace Articles</a>
    <nav>
      <a href="{index}">All articles</a>
      <a href="https://github.com/wwkkyy0325">GitHub</a>
    </nav>
  </header>"""

PAGE = """<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} — DeepSpace Articles</title>
  <meta name="description" content="{desc}">
  <link rel="stylesheet" href="../styles.css">
</head>
<body>
{nav}
  <main class="article">
    <h1>{title}</h1>
    <div class="article-meta">
      <span>2026-10</span>
      <a href="{other}">{other_label}</a>
      <a href="https://github.com/wwkkyy0325">GitHub</a>
    </div>
{body}
  </main>
  <footer>Written by wwkkyy0325. Architecture, agent runtimes, Rust. One developer, many projects.</footer>
</body>
</html>
"""


def strip_first_h1(text: str) -> tuple[str, str]:
    match = re.search(r"^# (.+)$", text, re.MULTILINE)
    if not match:
        return "Untitled", text
    title = match.group(1).strip()
    body = text[: match.start()] + text[match.end():]
    return title, body.lstrip()


def render(src: pathlib.Path, slug: str, lang: str) -> str:
    title, body_md = strip_first_h1(src.read_text(encoding="utf-8"))
    body = markdown.markdown(
        body_md,
        extensions=["tables", "fenced_code", "toc", "sane_lists"],
        output_format="html5",
    )
    other_lang = "zh" if lang == "en" else "en"
    other_label = "中文" if lang == "en" else "English"
    page = PAGE.format(
        lang="en" if lang == "en" else "zh-CN",
        title=html.escape(title),
        desc=html.escape(ARTICLES[slug]["desc_en" if lang == "en" else "desc_zh"]),
        nav=NAV.format(home="../index.html", index="../index.html"),
        other=f"../{other_lang}/{slug}.html",
        other_label=other_label,
        body=body,
    )
    out = ROOT / lang / f"{slug}.html"
    out.write_text(page, encoding="utf-8")
    print("wrote", out.relative_to(ROOT))
    return title


def main() -> None:
    titles: dict[tuple[str, str], str] = {}
    for slug, item in ARTICLES.items():
        titles[(slug, "en")] = render(item["en"], slug, "en")
        titles[(slug, "zh")] = render(item["zh"], slug, "zh")

    cards = []
    for slug, item in ARTICLES.items():
        cards.append(f"""    <section class="card">
      <h2>{html.escape(titles[(slug, 'en')])}</h2>
      <p>{html.escape(item['desc_en'])}</p>
      <div class="links">
        <a href="en/{slug}.html">Read in English</a>
        <a href="zh/{slug}.html">中文</a>
      </div>
    </section>""")

    index = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DeepSpace Articles</title>
  <meta name="description" content="Two long-form essays on agent runtimes, context engineering, and engineering method.">
  <link rel="stylesheet" href="styles.css">
</head>
<body>
{NAV.format(home='index.html', index='index.html')}
  <main class="index-hero">
    <h1>DeepSpace Articles</h1>
    <p>Two long-form essays from building a general-purpose agent runtime: architecture and convergence, and a cross-project engineering method. Available in English and Chinese.</p>
  </main>
  <div class="cards">
{chr(10).join(cards)}
  </div>
  <section class="about">
    <h2>About</h2>
    <p>Written by <a href="https://github.com/wwkkyy0325">wwkkyy0325</a>. I build agent runtimes, developer tools, and systems software, mostly in Rust. These essays record what worked, what failed, and how the decisions were made.</p>
  </section>
  <footer>© 2026 wwkkyy0325. Articles are provided for reading and discussion.</footer>
</body>
</html>
"""
    (ROOT / "index.html").write_text(index, encoding="utf-8")
    print("wrote index.html")


if __name__ == "__main__":
    main()

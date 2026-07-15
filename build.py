#!/usr/bin/env python3
"""
数据分析面试速通课 · 静态站点构建器

数据源：
- chapters.json: 核心课程与复习元数据
- modules.json: 课程模块
- stories.json: 案例故事目录与关联
- content/*.html: 课程正文
- story-src/*.html: 原始沉浸式故事

输出：
- index.html / articles/*.html
- home.html
- stories/index.html / stories/*.html
"""
from __future__ import annotations

import html
import json
import os
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent

SITE_ICON = '<link rel="icon" href="data:,">'


def load_json(name: str):
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def write_output(path: Path, content: str) -> None:
    """Write deterministic generated HTML without trailing whitespace."""
    normalized = "\n".join(line.rstrip() for line in content.splitlines()) + "\n"
    path.write_text(normalized, encoding="utf-8")


def chapter_href(ch: dict, from_article: bool = False) -> str:
    if ch.get("is_root"):
        return "../index.html" if from_article else "index.html"
    return f"{ch['slug']}.html" if from_article else f"articles/{ch['slug']}.html"


def story_href(story: dict, from_article: bool = False) -> str:
    prefix = "../stories/" if from_article else "stories/"
    return prefix + story["output"]


def list_items(items, class_name="review-list") -> str:
    return f'<ul class="{class_name}">' + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def build_review(ch: dict) -> str:
    framework = "".join(
        f'<div class="framework-node"><span>{idx:02d}</span><strong>{esc(item)}</strong></div>'
        for idx, item in enumerate(ch.get("framework", []), 1)
    )
    return f'''
<section class="review-sheet" aria-label="速览复习">
  <div class="review-kicker">QUICK REVIEW · {esc(ch.get('duration', 10))} 分钟课程的 2 分钟回顾</div>
  <h2>先记住这条主线</h2>
  <div class="framework-track">{framework}</div>
  <div class="review-grid">
    <article class="review-card review-card-answer">
      <div class="review-label">90 秒回答核心</div>
      <p>{esc(ch.get('interview_answer', ''))}</p>
    </article>
    <article class="review-card">
      <div class="review-label">本章学习目标</div>
      {list_items(ch.get('objectives', []))}
    </article>
    <article class="review-card review-card-warning">
      <div class="review-label">常见失分点</div>
      {list_items(ch.get('pitfalls', []))}
    </article>
  </div>
  <div class="review-actions">
    <button class="mode-link" type="button" data-mode-target="learn">返回沉浸学习</button>
    <a class="mode-link secondary" href="{'home.html' if ch.get('is_root') else '../home.html'}">查看完整课程地图</a>
  </div>
</section>'''


def build_related_stories(ch: dict, stories_by_id: dict, from_article: bool) -> str:
    related = [stories_by_id[sid] for sid in ch.get("related_stories", []) if sid in stories_by_id]
    if not related:
        return ""
    cards = []
    for story in related:
        tags = "".join(f"<span>{esc(tag)}</span>" for tag in story["tags"][:2])
        cards.append(f'''
<a class="related-story-card" href="{story_href(story, from_article)}">
  <div class="related-story-num">CASE {esc(story['num'])}</div>
  <h3>{esc(story['title'])}</h3>
  <p>{esc(story['subtitle'])}</p>
  <div class="related-story-meta">{tags}<em>{esc(story['duration'])} 分钟</em></div>
</a>''')
    return f'''
<section class="related-stories reveal">
  <div class="section-eyebrow">TRANSFER PRACTICE</div>
  <div class="related-heading">
    <div><h2>把方法迁移到另一个业务问题</h2><p>课程负责建立框架，案例负责检验你能否独立使用。</p></div>
    <a href="{'../stories/index.html' if from_article else 'stories/index.html'}">查看全部案例 →</a>
  </div>
  <div class="related-story-grid">{''.join(cards)}</div>
</section>'''


def build_chapter_page(ch: dict, idx: int, chapters: list[dict], modules_by_id: dict, stories_by_id: dict) -> str:
    is_root = ch.get("is_root", False)
    from_article = not is_root
    asset_path = "../assets/" if from_article else "assets/"
    home_link = "../home.html" if from_article else "home.html"
    stories_link = "../stories/index.html" if from_article else "stories/index.html"
    module = modules_by_id[ch["module"]]
    content = (BASE / "content" / f"{ch['slug']}.html").read_text(encoding="utf-8")

    objectives = "".join(f"<li>{esc(item)}</li>" for item in ch.get("objectives", []))
    learning_intro = f'''
<section class="lesson-brief reveal">
  <div class="lesson-brief-main">
    <div class="section-eyebrow">MISSION BRIEF</div>
    <h2>完成这一章，你应该能够</h2>
    <ul>{objectives}</ul>
  </div>
  <div class="lesson-brief-side">
    <span>{esc(ch.get('duration', 10))} MIN</span>
    <strong>{esc({'guide':'学习指南','case':'业务实战','concept':'方法理解','interview':'面试训练','career':'职业迁移'}.get(ch.get('content_type'), '课程'))}</strong>
  </div>
</section>'''

    related_html = build_related_stories(ch, stories_by_id, from_article)
    review_html = build_review(ch)

    nav_parts = []
    if idx > 0:
        prev = chapters[idx - 1]
        nav_parts.append(f'<a class="course-nav-link prev" href="{chapter_href(prev, from_article)}"><span>上一章</span><strong>← {esc(prev["short_title"])}</strong></a>')
    if idx < len(chapters) - 1:
        nxt = chapters[idx + 1]
        nav_parts.append(f'<a class="course-nav-link next" href="{chapter_href(nxt, from_article)}"><span>下一章</span><strong>{esc(nxt["short_title"])} →</strong></a>')
    else:
        nav_parts.append(f'<a class="course-nav-link next" href="{stories_link}"><span>继续训练</span><strong>进入案例故事库 →</strong></a>')
    course_nav = '<nav class="course-bottom-nav">' + ''.join(nav_parts) + '</nav>'

    toc_data = []
    for item in chapters:
        toc_data.append({
            "num": item["num"], "title": item["short_title"], "slug": item["slug"],
            "href": chapter_href(item, from_article), "module": item["module"]
        })

    module_chapters = [c for c in chapters if c["module"] == ch["module"]]
    module_pos = module_chapters.index(ch) + 1
    module_progress = round(module_pos / len(module_chapters) * 100)

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="{esc(ch['description'])}">
<title>{esc(ch['title'])} · 数据分析面试速通课</title>
<link rel="stylesheet" href="{asset_path}style.css">
{SITE_ICON}
<style>:root {{ --theme: {esc(ch['theme'])}; --theme-rgb: {esc(ch['theme_rgb'])}; --module-theme: {esc(module['theme'])}; }}</style>
</head>
<body data-page="lesson" data-default-mode="learn">
<a class="skip-link" href="#lesson-content">跳到正文</a>
<div class="site-progress" style="--lesson-progress:{module_progress}%"><span></span></div>
<div class="ambient-bg" aria-hidden="true">
  <div class="orb orb-one" style="background:radial-gradient(circle,rgba({esc(ch['theme_rgb'])},0.12),transparent 70%)"></div>
  <div class="orb orb-two"></div><div class="orb orb-three"></div>
</div>
<div class="grid-bg"></div>
<nav class="topnav">
  <a href="{home_link}" class="topnav-logo">DATA ANALYSIS</a>
  <div class="topnav-links"><a href="{home_link}">课程</a><a href="{stories_link}">案例故事</a></div>
</nav>
<main class="page lesson-page" id="lesson-content">
  <header class="lesson-header">
    <div class="module-line"><span>MODULE {esc(module['num'])}</span><strong>{esc(module['title'])}</strong><em>{module_pos}/{len(module_chapters)}</em></div>
    <div class="ch-badge">{esc(ch['badge'])}</div>
    <h1 class="ch-title static-title">{esc(ch['title'].replace('鲜食记 · ',''))}</h1>
    <p class="ch-subtitle lesson-description">{esc(ch['description'])}</p>
    <div class="mode-switch" role="group" aria-label="阅读模式">
      <button type="button" class="active" data-mode-target="learn"><span>沉浸学习</span><small>完整案例与推导</small></button>
      <button type="button" data-mode-target="review"><span>速览复习</span><small>框架与面试答案</small></button>
    </div>
  </header>

  <div id="learn-mode" class="learning-mode active">
    {learning_intro}
    <div class="lesson-body">{content}</div>
    {related_html}
  </div>
  <div id="review-mode" class="learning-mode">{review_html}</div>
  {course_nav}
</main>
<button id="toc-toggle" class="toc-toggle" type="button">课程目录</button>
<aside id="toc-panel" class="toc-panel" aria-label="课程目录"></aside>
<div id="toc-overlay" class="toc-overlay"></div>
<script src="{asset_path}main.js"></script>
<script>
window.TOC_CHAPTERS = {json.dumps(toc_data, ensure_ascii=False)};
window.TOC_CURRENT = {json.dumps(ch['slug'], ensure_ascii=False)};
window.COURSE_MODULES = {json.dumps(list(modules_by_id.values()), ensure_ascii=False)};
</script>
</body>
</html>'''


def module_card(module: dict, chapters: list[dict]) -> str:
    return f'''
<a class="module-card" href="#module-{esc(module['id'])}" style="--module-card-theme:{esc(module['theme'])}">
  <div class="module-card-top"><span>MODULE {esc(module['num'])}</span><em>{len(chapters)} 章</em></div>
  <h3>{esc(module['title'])}</h3>
  <p>{esc(module['description'])}</p>
  <strong>{esc(module['outcome'])}</strong>
</a>'''


def chapter_card(ch: dict) -> str:
    type_names = {"guide":"指南","case":"业务实战","concept":"方法理解","interview":"面试训练","career":"职业迁移"}
    visual = ""
    card_class = "course-card reveal"
    if ch.get("visual"):
        card_class += " has-visual"
        visual = f'<div class="course-card-visual"><img src="{esc(ch["visual"])}" alt="{esc(ch.get("visual_alt", ""))}" loading="lazy" decoding="async"></div>'
    return f'''
<a href="{chapter_href(ch)}" class="{card_class}" style="--card-theme:{esc(ch['theme'])}">
  <div class="course-card-num">{esc(ch['num'])}</div>
  <div class="course-card-content"><div class="course-card-meta"><span>{esc(type_names.get(ch.get('content_type'),'课程'))}</span><em>{esc(ch.get('duration',10))} 分钟</em></div><h3>{esc(ch['short_title'])}</h3><p>{esc(ch['description'])}</p></div>
  {visual}<span class="course-card-arrow">→</span>
</a>'''


def story_card(story: dict, href_prefix="stories/", show_visual: bool = False) -> str:
    tags = "".join(f"<span>{esc(tag)}</span>" for tag in story["tags"][:3])
    card_class = "story-library-card reveal"
    visual = ""
    if show_visual and story.get("visual"):
        card_class += " story-library-card-featured"
        visual = f'<div class="story-card-visual"><img src="{esc(story["visual"])}" alt="{esc(story.get("visual_alt", ""))}" loading="lazy" decoding="async"><span>MODEL INCIDENT · LIVE</span></div>'
    return f'''
<a class="{card_class}" href="{href_prefix}{esc(story['output'])}" data-category="{esc(story['category'])}" data-title="{esc(story['title'])} {' '.join(story['tags'])}">
  <div class="story-card-head"><span>CASE {esc(story['num'])}</span><em>{esc(story['difficulty'])} · {esc(story['duration'])} 分钟</em></div>
  {visual}<h3>{esc(story['title'])}</h3><p>{esc(story['subtitle'])}</p>
  <div class="story-card-tags">{tags}</div><strong>开始分析 <i>→</i></strong>
</a>'''


def build_home(chapters: list[dict], modules: list[dict], stories: list[dict]) -> str:
    core_count = sum(ch["module"] != "ml-decision" for ch in chapters)
    extension_count = len(chapters) - core_count
    story_count = len(stories)
    module_count = len(modules)
    module_sections = []
    module_cards = []
    for module in modules:
        items = [ch for ch in chapters if ch["module"] == module["id"]]
        module_cards.append(module_card(module, items))
        module_sections.append(f'''
<section class="course-module" id="module-{esc(module['id'])}">
  <header><div><span>MODULE {esc(module['num'])} · {esc(module['eyebrow'])}</span><h2>{esc(module['title'])}</h2><p>{esc(module['description'])}</p></div><strong>{esc(module['outcome'])}</strong></header>
  <div class="course-list">{''.join(chapter_card(ch) for ch in items)}</div>
</section>''')
    featured = sorted(
        (story for story in stories if story.get("featured")),
        key=lambda story: (story.get("featured_rank", 99), int(story["num"]))
    )[:6]
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="通过一条完整业务主线、核心课程、机器学习扩展和沉浸案例训练真实业务判断能力。">
<title>数据分析面试速通课</title><link rel="stylesheet" href="assets/style.css">{SITE_ICON}</head>
<body data-page="home">
<div class="ambient-bg" aria-hidden="true"><div class="orb orb-one"></div><div class="orb orb-two"></div><div class="orb orb-three"></div></div><div class="grid-bg"></div>
<nav class="topnav"><a href="home.html" class="topnav-logo">DATA ANALYSIS</a><div class="topnav-links"><a class="active" href="#course-map">课程</a><a href="stories/index.html">案例故事</a></div></nav>
<main class="home-page">
  <section class="home-hero">
    <div class="home-kicker">LEARN · PRACTICE · REVIEW</div>
    <h1>把分析思路<br><span>练成面试答案</span></h1>
    <p>一条完整业务主线，{core_count} 章核心课程，{extension_count} 章机器学习决策扩展，{story_count} 个沉浸式案例。既学习成功路径，也审查失败方案。</p>
    <div class="home-actions"><a class="primary" href="index.html">开始系统学习</a><a href="stories/index.html">进入案例故事库</a></div>
    <div class="home-stats"><div><strong>{core_count}</strong><span>核心课程</span></div><div><strong>{extension_count}</strong><span>ML扩展</span></div><div><strong>{story_count}</strong><span>业务案例</span></div><div><strong>{module_count}</strong><span>能力阶段</span></div></div>
  </section>
  <section class="experience-map">
    <div class="experience-step"><span>01</span><strong>课程学习</strong><p>建立稳定、可复用的分析框架。</p></div>
    <i>→</i><div class="experience-step"><span>02</span><strong>案例训练</strong><p>在陌生业务中独立判断下一步。</p></div>
    <i>→</i><div class="experience-step"><span>03</span><strong>速览复习</strong><p>沉淀90秒答案、追问和失分点。</p></div>
  </section>
  <section class="home-section" id="course-map"><header class="home-section-heading"><span>COURSE MAP</span><h2>五个阶段，从业务分析走向模型决策</h2><p>前四个阶段建立分析与表达主线；机器学习作为可选扩展，先训练问题判断、失败识别和行动闭环。</p></header><div class="module-grid">{''.join(module_cards)}</div></section>
  {''.join(module_sections)}
  <section class="home-section featured-stories"><header class="home-section-heading"><span>IMMERSIVE CASES</span><h2>换一个问题，检验你是否真的会用</h2><p>案例不会重复讲概念，而是让你面对数据、做出判断并承担分析顺序带来的后果。</p></header><div class="story-library-grid">{''.join(story_card(s, show_visual=True) for s in featured)}</div><div class="center-action"><a href="stories/index.html">查看全部案例 →</a></div></section>
</main><script src="assets/main.js"></script></body></html>'''


def build_story_index(stories: list[dict]) -> str:
    categories = []
    for s in stories:
        if s["category"] not in categories:
            categories.append(s["category"])
    story_count = len(stories)
    filters = f'<button class="active" data-filter="all">全部 {story_count} 篇</button>' + ''.join(f'<button data-filter="{esc(c)}">{esc(c)}</button>' for c in categories)
    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="{story_count}个沉浸式业务案例，覆盖指标、用户、商品、活动、经营诊断与机器学习决策。">
<title>案例故事库 · 数据分析面试速通课</title><link rel="stylesheet" href="../assets/style.css"><link rel="stylesheet" href="../assets/story-library.css">{SITE_ICON}</head>
<body data-page="story-library"><div class="ambient-bg" aria-hidden="true"><div class="orb orb-one"></div><div class="orb orb-two"></div><div class="orb orb-three"></div></div><div class="grid-bg"></div>
<nav class="topnav"><a href="../home.html" class="topnav-logo">DATA ANALYSIS</a><div class="topnav-links"><a href="../home.html">课程</a><a class="active" href="index.html">案例故事</a></div></nav>
<main class="story-library-page">
  <header class="story-library-hero"><div class="home-kicker">BUSINESS STORY LAB</div><h1>{story_count} 个真实业务问题<br><span>等你来拆解</span></h1><p>这里不再替你讲一遍方法。你会先看到不完整的信息，选择分析方向，再用数据验证自己的判断。</p><div class="home-actions"><a class="primary" href="{esc(stories[0]['output'])}">从案例 01 开始</a><a href="#story-catalog">按能力选择案例</a></div></header>
  <section class="library-guide"><article><span>01</span><strong>进入任务</strong><p>明确角色、时限和业务交付。</p></article><article><span>02</span><strong>查看证据</strong><p>从数据与业务事件中寻找线索。</p></article><article><span>03</span><strong>形成判断</strong><p>区分相关、假设和已验证根因。</p></article><article><span>04</span><strong>迁移复盘</strong><p>回到课程框架和面试表达。</p></article></section>
  <section class="story-catalog" id="story-catalog"><div class="catalog-toolbar"><div><span>CASE CATALOG</span><h2>选择你的下一个业务问题</h2></div><label class="story-search"><span>搜索</span><input id="story-search" type="search" placeholder="标题、能力或标签"></label></div><div class="story-filters" role="group" aria-label="案例分类">{filters}</div><div id="story-grid" class="story-library-grid">{''.join(story_card(s, '') for s in stories)}</div><p id="story-empty" class="story-empty" hidden>没有找到匹配案例，换一个关键词试试。</p></section>
</main><script src="../assets/main.js"></script><script src="../assets/story-library.js"></script></body></html>'''


def inject_story_shell(source: str, story: dict, prev_story: dict | None, next_story: dict | None, chapters_by_slug: dict, story_count: int) -> str:
    head_extra = '<link rel="icon" href="data:,">\n<link rel="stylesheet" href="../assets/story-shell.css">\n'
    if "</head>" in source:
        source = source.replace("</head>", head_extra + "</head>", 1)
    related = []
    for slug in story.get("related_chapters", []):
        ch = chapters_by_slug.get(slug)
        if ch:
            related.append({"num": ch["num"], "title": ch["short_title"], "href": "../index.html" if ch.get("is_root") else f"../articles/{ch['slug']}.html"})
    meta = {
        "id": story["id"], "num": story["num"], "title": story["title"], "subtitle": story["subtitle"],
        "category": story["category"], "duration": story["duration"], "tags": story["tags"],
        "indexHref": "index.html", "homeHref": "../home.html", "relatedChapters": related, "storyCount": story_count,
        "prev": {"title": prev_story["title"], "href": prev_story["output"]} if prev_story else None,
        "next": {"title": next_story["title"], "href": next_story["output"]} if next_story else None,
    }
    boot = f'''<script>window.STORY_META = {json.dumps(meta, ensure_ascii=False).replace('</', '<\\/')};</script>
<script src="../assets/story-shell.js"></script>'''
    if "</body>" in source:
        source = source.replace("</body>", boot + "\n</body>", 1)
    else:
        source += boot
    return source


def build():
    chapters = load_json("chapters.json")
    modules = load_json("modules.json")
    stories = load_json("stories.json")
    modules_by_id = {m["id"]: m for m in modules}
    stories_by_id = {s["id"]: s for s in stories}
    chapters_by_slug = {c["slug"]: c for c in chapters}

    (BASE / "articles").mkdir(exist_ok=True)
    (BASE / "stories").mkdir(exist_ok=True)

    for idx, ch in enumerate(chapters):
        output = BASE / ("index.html" if ch.get("is_root") else f"articles/{ch['slug']}.html")
        write_output(output, build_chapter_page(ch, idx, chapters, modules_by_id, stories_by_id))
        print(f"  COURSE {ch['num']} · {ch['short_title']}")

    write_output(BASE / "home.html", build_home(chapters, modules, stories))
    write_output(BASE / "stories/index.html", build_story_index(stories))

    for idx, story in enumerate(stories):
        source = (BASE / "story-src" / story["source"]).read_text(encoding="utf-8")
        rendered = inject_story_shell(source, story, stories[idx - 1] if idx else None, stories[idx + 1] if idx + 1 < len(stories) else None, chapters_by_slug, len(stories))
        write_output(BASE / "stories" / story["output"], rendered)
        print(f"  STORY  {story['num']} · {story['title']}")

    print(f"\nDONE · {len(chapters)} lessons + {len(stories)} stories + 2 indexes")


if __name__ == "__main__":
    build()

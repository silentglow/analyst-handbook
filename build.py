#!/usr/bin/env python3
"""
数据分析面试速通课 · 静态站点构建器

数据源：
- chapters.json: 核心课程与复习元数据
- modules.json: 课程模块
- stories.json: 案例故事目录与关联
- content/*.html: 课程正文
- story-src/*.html: 原始沉浸式故事
- topics.json / topics-src/*.html: 专题课程

输出：
- index.html / articles/*.html
- home.html
- stories/index.html / stories/*.html
- topics/index.html / topics/*.html
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



def list_items(items, class_name="review-list") -> str:
    return f'<ul class="{class_name}">' + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def build_review(ch: dict) -> str:
    framework = "".join(
        f'<div class="framework-node"><span>{idx:02d}</span><strong>{esc(item)}</strong></div>'
        for idx, item in enumerate(ch.get("framework", []), 1)
    )
    return f'''
<section class="review-sheet" aria-label="面试速览">
  <div class="review-kicker">INTERVIEW REVIEW · {esc(ch.get('duration', 10))} 分钟课程 · 2 分钟回顾</div>
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
    <button class="mode-link" type="button" data-mode-target="learn">返回完整学习</button>
    <a class="mode-link secondary" href="{'home.html' if ch.get('is_root') else '../home.html'}">查看完整课程地图</a>
  </div>
</section>'''



def build_chapter_page(ch: dict, idx: int, chapters: list[dict], modules_by_id: dict) -> str:
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
    <div class="section-eyebrow">本章目标</div>
    <h2>完成这一章，你应该能够</h2>
    <ul>{objectives}</ul>
  </div>
  <div class="lesson-brief-side">
    <span>{esc(ch.get('duration', 10))} MIN</span>
    <strong>{esc({'guide':'学习指南','case':'业务实战','concept':'方法理解','interview':'面试训练','career':'职业迁移'}.get(ch.get('content_type'), '课程'))}</strong>
  </div>
</section>'''

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
<link rel="stylesheet" href="{asset_path}editorial.css">
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
  <a href="{home_link}" class="topnav-logo">分析手册</a>
  <div class="topnav-links"><a href="{home_link}">系统课程</a><a href="{'../topics/index.html' if from_article else 'topics/index.html'}">专题课程</a><a href="{stories_link}">业务案例</a></div>
</nav>
<main class="page lesson-page" id="lesson-content">
  <header class="lesson-header">
    <div class="module-line"><span>阶段 {esc(module['num'])}</span><strong>{esc(module['title'])}</strong><em>{module_pos}/{len(module_chapters)}</em></div>
    <div class="ch-badge">{esc(ch['badge'])}</div>
    <h1 class="ch-title static-title">{esc(ch['title'].replace('鲜食记 · ',''))}</h1>
    <p class="ch-subtitle lesson-description">{esc(ch['description'])}</p>
    <div class="mode-switch" role="group" aria-label="阅读模式">
      <button type="button" class="active" data-mode-target="learn"><span>完整学习</span><small>案例、原理与推导</small></button>
      <button type="button" data-mode-target="review"><span>面试速览</span><small>主线、答案与失分点</small></button>
    </div>
  </header>

  <div id="learn-mode" class="learning-mode active">
    {learning_intro}
    <div class="lesson-body">{content}</div>
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
  <div class="module-card-top"><span>阶段 {esc(module['num'])}</span><em>{len(chapters)} 章</em></div>
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
  <div class="story-card-head"><span>案例 {esc(story['num'])}</span><em>{esc(story['difficulty'])} · {esc(story['duration'])} 分钟</em></div>
  {visual}<h3>{esc(story['title'])}</h3><p>{esc(story['subtitle'])}</p>
  <div class="story-card-tags">{tags}</div><strong>开始分析 <i>→</i></strong>
</a>'''


def build_home(chapters: list[dict], modules: list[dict], stories: list[dict], topics: list[dict]) -> str:
    module_sections = []
    module_cards = []
    for module in modules:
        items = [ch for ch in chapters if ch["module"] == module["id"]]
        module_cards.append(module_card(module, items))
        module_sections.append(f'''
<section class="course-module" id="module-{esc(module['id'])}">
  <header><div><span>阶段 {esc(module['num'])} · {esc(module['eyebrow'])}</span><h2>{esc(module['title'])}</h2><p>{esc(module['description'])}</p></div><strong>{esc(module['outcome'])}</strong></header>
  <div class="course-list">{''.join(chapter_card(ch) for ch in items)}</div>
</section>''')
    topic_rows = []
    for topic in topics:
        topic_rows.append(f'''
<a class="home-topic-row" href="topics/{esc(topic['output'])}">
  <span>{esc(topic['num'])}</span>
  <div><small>{esc(topic['category'])}</small><h3>{esc(topic['title'])}</h3><p>{esc(topic['subtitle'])}</p></div>
  <strong>{esc(topic['duration'])} 分钟 →</strong>
</a>''')
    featured = sorted(
        (story for story in stories if story.get("featured")),
        key=lambda story: (story.get("featured_rank", 99), int(story["num"]))
    )[:3]
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="从业务问题出发，系统学习数据分析、实验设计、机器学习与面试表达。">
<title>分析手册 · 数据分析学习与面试训练</title>
<link rel="stylesheet" href="assets/style.css"><link rel="stylesheet" href="assets/editorial.css">{SITE_ICON}</head>
<body data-page="home">
<nav class="topnav"><a href="home.html" class="topnav-logo">分析手册</a><div class="topnav-links"><a class="active" href="#course-map">系统课程</a><a href="topics/index.html">专题课程</a><a href="stories/index.html">业务案例</a></div></nav>
<main class="home-page">
  <section class="home-hero">
    <div class="home-hero-main"><div class="home-kicker">数据分析 · 业务判断 · 面试表达</div><h1>从业务问题出发，<br><span>练习如何做判断</span></h1><p>这不是一份软件说明书，也不是算法清单。课程保留必要的知识讲解，再用过程演示、失败案例和面试追问，帮助你把“知道”变成能够解释、验证和行动。</p><div class="home-actions"><a class="primary" href="index.html">从系统课程开始</a><a href="topics/index.html">查看专题课程</a></div></div>
    <aside class="home-hero-note"><span>阅读建议</span><ol><li><b>01</b><div><strong>先建立分析主线</strong><small>从问题定义到结果表达，完整走一遍。</small></div></li><li><b>02</b><div><strong>再深入关键专题</strong><small>补 SQL、Python、实验与机器学习。</small></div></li><li><b>03</b><div><strong>最后进入案例</strong><small>在不完整信息中独立做出判断。</small></div></li></ol></aside>
  </section>
  <nav class="home-compass" aria-label="选择学习方式"><a href="#course-map"><b>01</b><div><span>第一次系统学习</span><strong>按阶段建立完整框架</strong><p>适合从头梳理业务分析与面试表达。</p></div></a><a href="#topics"><b>02</b><div><span>针对薄弱点深入</span><strong>进入专题课程</strong><p>保留详细原理、过程演示和失败边界。</p></div></a><a href="stories/index.html"><b>03</b><div><span>直接练习业务判断</span><strong>进入案例库</strong><p>面对证据，判断先查什么、为何这样查。</p></div></a></nav>
  <section class="home-section" id="course-map"><header class="home-section-heading"><span>系统课程</span><h2>五个阶段，建立稳定的分析能力</h2><p>前四个阶段连接业务分析、方法选择与表达；机器学习不是附加算法清单，而是从问题定义、上线条件和失败复盘开始。</p></header><div class="module-grid">{''.join(module_cards)}</div></section>
  {''.join(module_sections)}
  <section class="home-section" id="topics"><header class="home-section-heading"><span>专题深入</span><h2>把关键知识讲透，而不是只留下结论</h2><p>SQL 聚焦业务数据结构与高频题型，Python 进入综合分析，实验与机器学习保留原理、判断过程和面试追问。</p></header><div class="home-topic-list">{''.join(topic_rows)}</div><div class="center-action"><a href="topics/index.html">查看全部专题 →</a></div></section>
  <section class="home-section featured-stories"><header class="home-section-heading"><span>业务案例</span><h2>换一个问题，检验你是否真的会用</h2><p>案例不会替你重复概念，而是给出不完整信息，让你观察证据、识别误判，并说明下一步行动。</p></header><div class="story-library-grid">{''.join(story_card(s, show_visual=True) for s in featured)}</div><div class="center-action"><a href="stories/index.html">进入全部案例 →</a></div></section>
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
<title>业务案例 · 分析手册</title><link rel="stylesheet" href="../assets/style.css"><link rel="stylesheet" href="../assets/story-library.css"><link rel="stylesheet" href="../assets/editorial.css">{SITE_ICON}</head>
<body data-page="story-library"><div class="ambient-bg" aria-hidden="true"><div class="orb orb-one"></div><div class="orb orb-two"></div><div class="orb orb-three"></div></div><div class="grid-bg"></div>
<nav class="topnav"><a href="../home.html" class="topnav-logo">分析手册</a><div class="topnav-links"><a href="../home.html">系统课程</a><a href="../topics/index.html">专题课程</a><a class="active" href="index.html">业务案例</a></div></nav>
<main class="story-library-page">
  <header class="story-library-hero"><div class="home-kicker">业务案例</div><h1>在不完整的信息里，<br><span>练习做判断</span></h1><p>这里不再替你讲一遍方法。你会先看到不完整的信息，选择分析方向，再用数据验证自己的判断。</p><div class="home-actions"><a class="primary" href="{esc(stories[0]['output'])}">从案例 01 开始</a><a href="#story-catalog">按能力选择案例</a></div></header>
  <section class="library-guide"><article><span>01</span><strong>进入任务</strong><p>明确角色、时限和业务交付。</p></article><article><span>02</span><strong>查看证据</strong><p>从数据与业务事件中寻找线索。</p></article><article><span>03</span><strong>形成判断</strong><p>区分相关、假设和已验证根因。</p></article><article><span>04</span><strong>迁移复盘</strong><p>记录误判、证据与下一步行动。</p></article></section>
  <section class="story-catalog" id="story-catalog"><div class="catalog-toolbar"><div><span>案例目录 · 共 {story_count} 篇</span><h2>选择一个业务问题</h2></div><label class="story-search"><span>搜索</span><input id="story-search" type="search" placeholder="标题、能力或标签"></label></div><div class="story-filters" role="group" aria-label="案例分类">{filters}</div><div id="story-grid" class="story-library-grid">{''.join(story_card(s, '') for s in stories)}</div><p id="story-empty" class="story-empty" hidden>没有找到匹配案例，换一个关键词试试。</p></section>
</main><script src="../assets/main.js"></script><script src="../assets/story-library.js"></script></body></html>'''



def build_topic_index(topics: list[dict]) -> str:
    rows = []
    for topic in topics:
        objectives = " / ".join(topic["objectives"][:2])
        rows.append(f'''
<a class="topic-row" href="{esc(topic['output'])}" style="--theme:{esc(topic['theme'])};--theme-rgb:{esc(topic['theme_rgb'])}">
  <span class="topic-row-num">{esc(topic['num'])}</span>
  <div><small>{esc(topic['category'])}</small><h2>{esc(topic['title'])}</h2><p>{esc(topic['subtitle'])}</p><em>{esc(objectives)}</em></div>
  <strong>{esc(topic['duration'])} 分钟&nbsp; →</strong>
</a>''')
    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="description" content="围绕业务 SQL、Python 综合分析、机器学习和 A/B 测试组织的专题课程。">
<title>专题课程 · 分析手册</title><link rel="stylesheet" href="../assets/style.css"><link rel="stylesheet" href="../assets/topic-course.css"><link rel="stylesheet" href="../assets/editorial.css">{SITE_ICON}</head>
<body class="topic-body" data-page="topic-index"><nav class="topnav topic-nav"><a href="../home.html" class="topnav-logo">分析手册</a><div class="topnav-links"><a href="../home.html">系统课程</a><a class="active" href="index.html">专题课程</a><a href="../stories/index.html">业务案例</a></div></nav>
<main class="topic-index"><header class="topic-index-hero"><p>专题课程</p><h1>从真实问题进入方法</h1><div>这里不按软件菜单或算法名堆知识。每一节从一个具体问题开始，解释判断过程、实现方法、失败边界和面试表达。</div></header>
<section class="topic-list" aria-label="专题课程列表">{''.join(rows)}</section>
<section class="topic-note"><h2>内容怎么读</h2><p>先看过程演示，理解为什么这样判断；再读下方的知识解释和失败案例。动画是正文的一部分，不是装饰，也不会代替完整文字。</p></section>
</main><script src="../assets/main.js"></script></body></html>'''


def build_topic_page(topic: dict, idx: int, topics: list[dict]) -> str:
    content = (BASE / "topics-src" / topic["source"]).read_text(encoding="utf-8")
    objectives = "".join(f"<li>{esc(item)}</li>" for item in topic["objectives"])
    links = []
    if idx:
        prev = topics[idx - 1]
        links.append(f'<a href="{esc(prev["output"])}"><span>上一节</span><strong>← {esc(prev["title"])}</strong></a>')
    else:
        links.append('<a href="index.html"><span>课程目录</span><strong>← 返回专题课程</strong></a>')
    if idx + 1 < len(topics):
        nxt = topics[idx + 1]
        links.append(f'<a href="{esc(nxt["output"])}"><span>下一节</span><strong>{esc(nxt["title"])} →</strong></a>')
    else:
        links.append('<a href="index.html"><span>完成本组</span><strong>返回专题课程 →</strong></a>')
    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="description" content="{esc(topic['subtitle'])}"><title>{esc(topic['title'])} · 专题课程</title>
<link rel="stylesheet" href="../assets/style.css"><link rel="stylesheet" href="../assets/topic-course.css">{SITE_ICON}
<style>:root{{--theme:{esc(topic['theme'])};--theme-rgb:{esc(topic['theme_rgb'])}}}</style><link rel="stylesheet" href="../assets/editorial.css"></head>
<body class="topic-body" data-page="topic"><a class="skip-link" href="#topic-content">跳到正文</a>
<nav class="topnav topic-nav"><a href="../home.html" class="topnav-logo">分析手册</a><div class="topnav-links"><a href="../home.html">系统课程</a><a class="active" href="index.html">专题课程</a><a href="../stories/index.html">业务案例</a></div></nav>
<main class="topic-page" id="topic-content"><header class="topic-hero"><div class="topic-breadcrumb"><a href="index.html">专题课程</a><span>/</span><span>{esc(topic['category'])}</span></div><p class="topic-number">{esc(topic['num'])} · {esc(topic['level'])} · {esc(topic['duration'])} 分钟</p><h1>{esc(topic['title'])}</h1><div class="topic-lead">{esc(topic['subtitle'])}</div></header>
<section class="topic-objectives" aria-labelledby="objectives-title"><h2 id="objectives-title">这一节要解决什么</h2><ol>{objectives}</ol></section>
{content}
<nav class="topic-pagination" aria-label="专题课程翻页">{''.join(links)}</nav></main>
<script src="../assets/topic-course.js"></script></body></html>'''

def inject_story_shell(source: str, story: dict, prev_story: dict | None, next_story: dict | None, story_count: int) -> str:
    head_extra = '<link rel="icon" href="data:,">\n<link rel="stylesheet" href="../assets/story-shell.css">\n'
    if "</head>" in source:
        source = source.replace("</head>", head_extra + "</head>", 1)
    meta = {
        "id": story["id"], "num": story["num"], "title": story["title"], "subtitle": story["subtitle"],
        "category": story["category"], "duration": story["duration"], "tags": story["tags"],
        "indexHref": "index.html", "homeHref": "../home.html", "storyCount": story_count,
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
    topics = load_json("topics.json")
    modules_by_id = {m["id"]: m for m in modules}

    (BASE / "articles").mkdir(exist_ok=True)
    (BASE / "stories").mkdir(exist_ok=True)
    (BASE / "topics").mkdir(exist_ok=True)

    for idx, ch in enumerate(chapters):
        output = BASE / ("index.html" if ch.get("is_root") else f"articles/{ch['slug']}.html")
        write_output(output, build_chapter_page(ch, idx, chapters, modules_by_id))
        print(f"  COURSE {ch['num']} · {ch['short_title']}")

    write_output(BASE / "home.html", build_home(chapters, modules, stories, topics))
    write_output(BASE / "stories/index.html", build_story_index(stories))
    write_output(BASE / "topics/index.html", build_topic_index(topics))

    for idx, topic in enumerate(topics):
        write_output(BASE / "topics" / topic["output"], build_topic_page(topic, idx, topics))
        print(f"  TOPIC  {topic['num']} · {topic['title']}")

    for idx, story in enumerate(stories):
        source = (BASE / "story-src" / story["source"]).read_text(encoding="utf-8")
        rendered = inject_story_shell(source, story, stories[idx - 1] if idx else None, stories[idx + 1] if idx + 1 < len(stories) else None, len(stories))
        write_output(BASE / "stories" / story["output"], rendered)
        print(f"  STORY  {story['num']} · {story['title']}")

    print(f"\nDONE · {len(chapters)} lessons + {len(stories)} stories + {len(topics)} topics + 3 indexes")


if __name__ == "__main__":
    build()

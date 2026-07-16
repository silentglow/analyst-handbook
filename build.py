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
    """All lessons live in articles; return a path for the current directory."""
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
    <a class="mode-link secondary" href="{'courses.html' if ch.get('is_root') else '../courses.html'}">查看完整课程地图</a>
  </div>
</section>'''



def build_chapter_page(ch: dict, idx: int, chapters: list[dict], modules_by_id: dict) -> str:
    is_root = ch.get("is_root", False)
    from_article = not is_root
    asset_path = "../assets/" if from_article else "assets/"
    home_link = "../index.html" if from_article else "index.html"
    courses_link = "../courses.html" if from_article else "courses.html"
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
<link rel="stylesheet" href="{asset_path}experience.css">
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
  <div class="topnav-links"><a class="active" href="{courses_link}">系统课程</a><a href="{'../topics/index.html' if from_article else 'topics/index.html'}">专题课程</a><a href="{stories_link}">业务案例</a></div>
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
    {build_framework_visual(ch)}
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


def build_framework_visual(ch: dict) -> str:
    nodes = "".join(
        f'<li><span>{idx:02d}</span><strong>{esc(item)}</strong></li>'
        for idx, item in enumerate(ch.get("framework", []), 1)
    )
    return f'''<section class="lesson-framework reveal" aria-label="本章判断路径">
  <div class="lesson-framework__intro"><span>本章判断路径</span><p>先理解顺序，再进入细节。每一步都应该缩小问题，而不是增加术语。</p></div>
  <ol>{nodes}</ol>
</section>'''


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
    steps = "".join(f"<i title=\"{esc(item)}\"></i>" for item in ch.get("framework", [])[:5])
    return f'''
<a href="{chapter_href(ch)}" class="course-card reveal" style="--card-theme:{esc(ch['theme'])}">
  <div class="course-card-num">{esc(ch['num'])}</div>
  <div class="course-card-content"><div class="course-card-meta"><span>{esc(type_names.get(ch.get('content_type'),'课程'))}</span><em>{esc(ch.get('duration',10))} 分钟</em></div><h3>{esc(ch['short_title'])}</h3><p>{esc(ch['description'])}</p><div class="course-card-path" aria-label="{len(ch.get('framework', []))}步学习路径">{steps}</div></div>
  <span class="course-card-arrow">→</span>
</a>'''


def story_card(story: dict, href_prefix="stories/", show_visual: bool = False) -> str:
    tags = "".join(f"<span>{esc(tag)}</span>" for tag in story["tags"][:3])
    n = int(story["num"])
    values = [26 + ((n * 17 + i * 23) % 58) for i in range(7)]
    bars = "".join(f'<i style="--v:{v}%"></i>' for v in values)
    visual = f'''<div class="story-card-signal" aria-hidden="true"><div><span>{esc(story['category'])}</span><b>CASE {esc(story['num'])}</b></div><div class="story-card-bars">{bars}</div><em>?</em></div>'''
    return f'''
<a class="story-library-card reveal" href="{href_prefix}{esc(story['output'])}" data-category="{esc(story['category'])}" data-title="{esc(story['title'])} {' '.join(story['tags'])}">
  <div class="story-card-head"><span>案例 {esc(story['num'])}</span><em>{esc(story['difficulty'])} · {esc(story['duration'])} 分钟</em></div>
  {visual}<h3>{esc(story['title'])}</h3><p>{esc(story['subtitle'])}</p>
  <div class="story-card-tags">{tags}</div><strong>进入现场 <i>→</i></strong>
</a>'''


def build_landing(chapters: list[dict], modules: list[dict], stories: list[dict], topics: list[dict]) -> str:
    first_lesson = chapter_href(chapters[0])
    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="description" content="在真实业务问题中练习定义、验证、决策与表达。"><title>分析手册 · 练习在不确定中做判断</title>
<link rel="stylesheet" href="assets/style.css"><link rel="stylesheet" href="assets/editorial.css"><link rel="stylesheet" href="assets/experience.css">{SITE_ICON}</head>
<body data-page="landing"><a class="skip-link" href="#main">跳到正文</a>
<nav class="topnav"><a href="index.html" class="topnav-logo">分析手册</a><div class="topnav-links"><a href="courses.html">系统课程</a><a href="topics/index.html">专题课程</a><a href="stories/index.html">业务案例</a></div></nav>
<main class="landing" id="main">
  <section class="landing-hero">
    <div class="landing-hero__copy"><p class="landing-eyebrow">ANALYST HANDBOOK · 2026</p><h1>在不确定中，<br><span>练习做判断。</span></h1><p class="landing-lead">不是背更多框架，而是学习如何把模糊问题变成证据、选择与行动。系统课建立方法，专题拆透机制，业务案例检验你是否真的会用。</p><div class="home-actions"><a class="primary" href="courses.html">开始建立框架</a><a href="stories/index.html">直接进入案例</a></div></div>
    <div class="landing-hero__canvas" aria-label="从异常信号到业务判断的过程示意">
      <div class="canvas-head"><span>LIVE BRIEF · 09:30</span><strong>新用户次日打卡率异常</strong></div>
      <div class="canvas-signal"><span>45%</span><i></i><i></i><i></i><i></i><i class="fall"></i><i class="fall"></i><i class="fall"></i><b>33%</b></div>
      <ol class="canvas-reasoning"><li class="done"><b>01</b><span>异常是真的吗？</span><em>口径与埋点已确认</em></li><li class="active"><b>02</b><span>问题发生在哪？</span><em>正在检查渠道结构</em></li><li><b>03</b><span>为什么发生？</span><em>等待行为证据</em></li></ol>
      <div class="canvas-note"><span>当前判断</span><strong>先缩小范围，不急着宣布根因。</strong></div>
    </div>
  </section>
  <section class="landing-modes" aria-labelledby="modes-title"><header><p>一个系统 · 三种学习模式</p><h2 id="modes-title">不同内容，应该带来不同的学习动作</h2></header><div class="mode-grid">
    <a class="mode-card mode-card--course" href="courses.html"><span>01 · 建立框架</span><h3>系统课程</h3><p>沿一条完整业务主线，理解问题定义、分析顺序、方法选择与面试表达。</p><div class="mode-course-visual"><i></i><i></i><i></i><i></i><i></i></div><strong>{len(chapters)} 章 · 连续学习 →</strong></a>
    <a class="mode-card mode-card--topic" href="topics/index.html"><span>02 · 拆透方法</span><h3>专题课程</h3><p>播放过程、改变参数、观察边界。让 SQL、实验和机器学习真正“发生”在眼前。</p><div class="mode-topic-visual"><i>A</i><b>→</b><i>B</i><b>→</b><i>?</i></div><strong>{len(topics)} 个专题 · 过程演示 →</strong></a>
    <a class="mode-card mode-card--case" href="stories/index.html"><span>03 · 进入现场</span><h3>业务案例</h3><p>接收有限证据，面对误导线索，做出选择并看到判断带来的后果。</p><div class="mode-case-visual"><span>证据 01</span><span>证据 02</span><em>你的判断？</em></div><strong>{len(stories)} 个案例 · 决策训练 →</strong></a>
  </div></section>
  <section class="learning-loop"><div><p>学习闭环</p><h2>内容不是被“看完”的，<br>而是被反复调用的。</h2></div><ol><li><span>01</span><strong>理解</strong><p>建立概念和判断顺序。</p></li><li><span>02</span><strong>观察</strong><p>看证据如何改变结论。</p></li><li><span>03</span><strong>决策</strong><p>在限制条件下选择行动。</p></li><li><span>04</span><strong>复盘</strong><p>解释误判、边界与迁移。</p></li></ol></section>
  <section class="landing-start"><p>如果你第一次来到这里</p><h2>先完成第一章，建立这套手册的使用方式。</h2><a href="{first_lesson}">开始第 01 章 <span>→</span></a></section>
</main><footer class="site-footer"><span>分析手册</span><p>为真实业务判断而设计，不为堆积知识而设计。</p></footer><script src="assets/main.js"></script></body></html>'''


def build_course_index(chapters: list[dict], modules: list[dict], stories: list[dict], topics: list[dict]) -> str:
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
    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="description" content="28章系统课程：从业务问题、分析方法到机器学习与面试表达。"><title>系统课程 · 分析手册</title>
<link rel="stylesheet" href="assets/style.css"><link rel="stylesheet" href="assets/editorial.css"><link rel="stylesheet" href="assets/experience.css">{SITE_ICON}</head>
<body data-page="courses"><nav class="topnav"><a href="index.html" class="topnav-logo">分析手册</a><div class="topnav-links"><a class="active" href="courses.html">系统课程</a><a href="topics/index.html">专题课程</a><a href="stories/index.html">业务案例</a></div></nav>
<main class="course-index">
<header class="course-index-hero"><div><p>系统课程 · {len(chapters)} 章</p><h1>先建立一条<br>稳定的判断路径</h1></div><div><p>课程不是 28 篇彼此独立的文章。它从一场业务异常开始，逐步进入方法选择、面试表达和机器学习决策。</p><a href="{chapter_href(chapters[0])}">从第 01 章开始 →</a></div></header>
<nav class="module-grid" aria-label="课程阶段">{''.join(module_cards)}</nav>
{''.join(module_sections)}
</main><footer class="site-footer"><span>系统课程</span><p>问题 → 证据 → 方法 → 决策 → 表达</p></footer><script src="assets/main.js"></script></body></html>'''


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
<title>业务案例 · 分析手册</title><link rel="stylesheet" href="../assets/style.css"><link rel="stylesheet" href="../assets/story-library.css"><link rel="stylesheet" href="../assets/editorial.css"><link rel="stylesheet" href="../assets/experience.css">{SITE_ICON}</head>
<body data-page="story-library"><div class="ambient-bg" aria-hidden="true"><div class="orb orb-one"></div><div class="orb orb-two"></div><div class="orb orb-three"></div></div><div class="grid-bg"></div>
<nav class="topnav"><a href="../index.html" class="topnav-logo">分析手册</a><div class="topnav-links"><a href="../courses.html">系统课程</a><a href="../topics/index.html">专题课程</a><a class="active" href="index.html">业务案例</a></div></nav>
<main class="story-library-page">
  <header class="story-library-hero"><div class="story-hero-copy"><div class="home-kicker">业务案例</div><h1>信息并不完整，<br><span>你仍然要做判断</span></h1><p>先接收任务，再观察证据、选择方向、验证假设。案例不会替你重复概念，而是让你真正经历一次业务分析。</p><div class="home-actions"><a class="primary" href="{esc(stories[0]['output'])}">进入第一个案例</a><a href="#story-catalog">浏览全部案例</a></div></div><div class="case-preview" aria-label="案例任务示意"><div class="case-preview-head"><span>CASE 01</span><em>限时决策</em></div><h2>大促 GMV 上升，<br>为什么利润反而下降？</h2><div class="case-clues"><span>客单价 <b>+12%</b></span><span>毛利率 <b>−8.4%</b></span><span>退款率 <b>+5.7%</b></span></div><div class="case-preview-action"><i></i><span>还有 3 条证据尚未查看</span><b>→</b></div></div></header>
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
<title>专题课程 · 分析手册</title><link rel="stylesheet" href="../assets/style.css"><link rel="stylesheet" href="../assets/topic-course.css"><link rel="stylesheet" href="../assets/editorial.css"><link rel="stylesheet" href="../assets/experience.css">{SITE_ICON}</head>
<body class="topic-body" data-page="topic-index"><nav class="topnav topic-nav"><a href="../index.html" class="topnav-logo">分析手册</a><div class="topnav-links"><a href="../courses.html">系统课程</a><a class="active" href="index.html">专题课程</a><a href="../stories/index.html">业务案例</a></div></nav>
<main class="topic-index"><header class="topic-index-hero"><div class="topic-index-copy"><p>专题课程</p><h1>看见方法<br>如何发生</h1><div>这里不按软件菜单或算法名堆知识。每一节从一个具体问题开始，用连续演示解释判断过程、实现方法、失败边界和面试表达。</div></div><div class="topic-index-visual" aria-hidden="true"><span class="topic-orbit orbit-one">SQL</span><span class="topic-orbit orbit-two">Python</span><span class="topic-orbit orbit-three">实验</span><span class="topic-orbit orbit-four">ML</span><strong>业务<br>问题</strong><i></i></div></header>
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
<style>:root{{--theme:{esc(topic['theme'])};--theme-rgb:{esc(topic['theme_rgb'])}}}</style><link rel="stylesheet" href="../assets/editorial.css"><link rel="stylesheet" href="../assets/experience.css"></head>
<body class="topic-body" data-page="topic"><a class="skip-link" href="#topic-content">跳到正文</a>
<nav class="topnav topic-nav"><a href="../index.html" class="topnav-logo">分析手册</a><div class="topnav-links"><a href="../courses.html">系统课程</a><a class="active" href="index.html">专题课程</a><a href="../stories/index.html">业务案例</a></div></nav>
<main class="topic-page" id="topic-content"><header class="topic-hero"><div class="topic-breadcrumb"><a href="index.html">专题课程</a><span>/</span><span>{esc(topic['category'])}</span></div><p class="topic-number">{esc(topic['num'])} · {esc(topic['level'])} · {esc(topic['duration'])} 分钟</p><h1>{esc(topic['title'])}</h1><div class="topic-lead">{esc(topic['subtitle'])}</div></header>
<section class="topic-objectives" aria-labelledby="objectives-title"><h2 id="objectives-title">这一节要解决什么</h2><ol>{objectives}</ol></section>
{content}
<nav class="topic-pagination" aria-label="专题课程翻页">{''.join(links)}</nav></main>
<script src="../assets/topic-course.js"></script></body></html>'''

def inject_story_shell(source: str, story: dict, prev_story: dict | None, next_story: dict | None, story_count: int) -> str:
    head_extra = '<link rel="icon" href="data:,">\n<link rel="stylesheet" href="../assets/story-shell.css">\n<link rel="stylesheet" href="../assets/experience-story.css">\n'
    if "</head>" in source:
        source = source.replace("</head>", head_extra + "</head>", 1)
    if "<body>" in source:
        source = source.replace("<body>", f'<body class="case-story" data-story="{esc(story["id"])}">', 1)
    elif re.search(r"<body\s+", source, flags=re.I):
        source = re.sub(r"<body\s+", f'<body class="case-story" data-story="{esc(story["id"])}" ', source, count=1, flags=re.I)
    meta = {
        "id": story["id"], "num": story["num"], "title": story["title"], "subtitle": story["subtitle"],
        "category": story["category"], "duration": story["duration"], "tags": story["tags"],
        "indexHref": "index.html", "homeHref": "../index.html", "storyCount": story_count,
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
        output = BASE / f"articles/{ch['slug']}.html"
        write_output(output, build_chapter_page(ch, idx, chapters, modules_by_id))
        print(f"  COURSE {ch['num']} · {ch['short_title']}")

    write_output(BASE / "index.html", build_landing(chapters, modules, stories, topics))
    write_output(BASE / "home.html", build_landing(chapters, modules, stories, topics))
    write_output(BASE / "courses.html", build_course_index(chapters, modules, stories, topics))
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

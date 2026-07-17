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
- assets/css/*.css: 分层样式源(tokens/base/components/page-*)

输出：
- index.html / articles/*.html
- home.html
- stories/index.html / stories/*.html
- topics/index.html / topics/*.html
- assets/app.css / assets/story.css(打包产物,?v= 为内容 hash)
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent

SITE_ICON = '<link rel="icon" href="data:,">'
# 有 JS 时才隐藏 .reveal 初始状态;无 JS 环境正文保持可见。
JS_FLAG = '<script>document.documentElement.classList.add("js")</script>'

CSS_DIR = BASE / "assets" / "css"
APP_CSS_SOURCES = [
    "tokens.css", "base.css", "components.css",
    "page-landing.css", "page-courses.css", "page-lesson.css",
    "page-topics.css", "page-stories.css",
]
# 故事页刻意不引入全站 tokens:旧版案例在内联样式里定义了同名 :root 变量
# (--bg/--radius/--shadow 等),注入令牌会覆盖它们的取值。
STORY_CSS_SOURCES = ["story-pages.css"]
# build() 打包后填入 {"app": hash, "story": hash}
ASSETS: dict[str, str] = {}


def bundle_css(sources: list[str], output_name: str) -> str:
    """Concatenate layered CSS sources into one bundle; return content hash."""
    parts = []
    for name in sources:
        text = (CSS_DIR / name).read_text(encoding="utf-8").strip()
        parts.append(f"/* ==================== {name} ==================== */\n{text}\n")
    bundle = "\n".join(parts)
    (BASE / "assets" / output_name).write_text(bundle, encoding="utf-8")
    return hashlib.md5(bundle.encode("utf-8")).hexdigest()[:10]


def app_css_link(asset_path: str) -> str:
    return f'<link rel="stylesheet" href="{asset_path}app.css?v={ASSETS["app"]}">'


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



VISUAL_KINDS = {
    "ch02": "briefing", "ch03": "tree", "ch04": "signal", "ch05": "experiment", "ch06": "route",
    "ch07": "tree", "ch08": "signal", "ch09": "signal", "ch10": "compare", "ch11": "compare",
    "ch12": "tree", "ch13": "route", "ch14": "tree", "ch15": "briefing", "ch16": "compare",
    "ch17": "tree", "ch18": "signal", "ch19": "route", "ch20": "route", "ch21": "briefing",
    "ch22": "experiment", "ch23": "tree", "ch24": "route", "ml01": "decision", "ml02": "decision",
    "ml03": "signal", "ml04": "decision",
}

HANDOFFS = {
    "guide": ("这门课围绕一条完整判断链反复训练。", "先进入一个真实业务现场，在信息不完整时明确目标、问题和交付。", "开始第一场业务任务"),
    "ch02": ("你已把一句模糊的“留存不太好”，改写成了可分析、可汇报的业务任务。", "先别急着找原因。下一步要确认该看哪些指标，以及它们之间是什么关系。", "搭建鲜食记指标树"),
    "ch03": ("你已完成指标口径与指标树，知道异常究竟发生在哪一个结果指标上。", "下一步沿时间、渠道和行为证据逐层缩小范围，再验证根因。", "开始排查这次异动"),
    "ch04": ("你已定位到问题：渠道用户预期与产品体验错位；数据延迟已排除。", "有了根因还不能直接上线方案。下一步要把建议变成可证伪的实验。", "设计验证方案"),
    "ch05": ("你已把产品建议转成了包含分流、指标、样本量与停止规则的实验方案。", "即使实验显著，也不能直接全量。下一步要评估收益、风险、灰度与回退。", "制定上线与灰度策略"),
    "ch06": ("你已走完从问题定义到策略落地的第一条完整业务分析闭环。", "接下来进入工具箱，但每个方法仍然要回到一个具体业务决策。", "进入用户分层任务"),
    "ml01": ("你已能先还原业务决策，再判断机器学习是否值得做。", "下一步进入真实履约场景，把模型分数转成有限运营容量下的动作。", "进入履约风险决策"),
    "ml03": ("你已识别需求预测中时间穿越、缺货偏差和平均误差的陷阱。", "最后要学会复盘：模型失败究竟发生在数据、评估、部署还是业务动作。", "进入模型失败复盘"),
}


def build_lesson_visual(ch: dict) -> str:
    # Turn each framework into a visual explanation that carries meaning.
    if ch["slug"] == "guide":
        return ""
    steps = ch.get("framework", [])
    kind = VISUAL_KINDS.get(ch["slug"], "route")
    eyebrow = {"experiment": "实验系统图", "tree": "结构关系图", "signal": "证据收敛图", "compare": "对照判断图", "decision": "决策门", "briefing": "任务现场", "route": "行动路径图"}[kind]

    if kind == "experiment":
        nodes = "".join(f'<li><span>{idx:02d}</span><strong>{esc(item)}</strong></li>' for idx, item in enumerate(steps[:5], 1))
        canvas = f'''<div class="experiment-canvas"><div class="experiment-source"><small>同一目标人群</small><strong>随机分流</strong></div><div class="experiment-lanes"><div><span>A · 对照</span><b>保持原体验</b></div><div><span>B · 实验</span><b>只改变一个关键变量</b></div></div><div class="experiment-gate"><small>统一口径比较</small><strong>主指标 × 护栏指标</strong></div></div><ol class="visual-step-strip">{nodes}</ol>'''
    elif kind == "tree":
        branches = "".join(f'<li><span>{idx:02d}</span><strong>{esc(item)}</strong></li>' for idx, item in enumerate(steps[:4], 1))
        canvas = f'''<div class="tree-canvas"><div class="tree-root"><small>业务问题</small><strong>{esc(ch['short_title'])}</strong></div><ul>{branches}</ul><div class="tree-output"><small>最终输出</small><strong>{esc(steps[-1] if steps else '形成判断')}</strong></div></div>'''
    elif kind in {"signal", "compare"}:
        bars = "".join(f'<i style="--bar:{42 + ((idx * 19) % 48)}%"><span>{idx:02d}</span></i>' for idx, _ in enumerate(steps[:5], 1))
        labels = "".join(f'<li><span>{idx:02d}</span>{esc(item)}</li>' for idx, item in enumerate(steps[:5], 1))
        canvas = f'''<div class="signal-canvas"><div class="signal-chart" aria-hidden="true">{bars}</div><div class="signal-reading"><small>观察整组证据</small><strong>让证据逐步缩小解释空间</strong><ol>{labels}</ol></div></div>'''
    elif kind == "decision":
        gates = "".join(f'<li><span>{idx:02d}</span><strong>{esc(item)}</strong></li>' for idx, item in enumerate(steps[:5], 1))
        canvas = f'''<div class="decision-canvas"><div class="decision-input"><small>输入</small><strong>一个看似适合建模的问题</strong></div><ol>{gates}</ol><div class="decision-output"><small>输出</small><strong>建模 / 规则 / 暂不做</strong></div></div>'''
    else:
        nodes = "".join(f'<li><span>{idx:02d}</span><strong>{esc(item)}</strong></li>' for idx, item in enumerate(steps, 1))
        canvas = f'''<div class="route-canvas"><div class="route-question"><small>当前任务</small><strong>{esc(ch['short_title'])}</strong></div><ol>{nodes}</ol><div class="route-result"><small>带走</small><strong>{esc(steps[-1] if steps else '形成业务判断')}</strong></div></div>'''

    return f'''<section class="lesson-visual lesson-visual--{kind} reveal" aria-label="{eyebrow}"><header><div><span>{eyebrow}</span><h2>先看懂关系，再进入细节</h2></div><p>这张图展示本章的信息流动，以及最后需要形成的判断。</p></header>{canvas}</section>'''


def build_chapter_transition(ch: dict, idx: int, chapters: list[dict], from_article: bool, stories_link: str) -> str:
    prev = chapters[idx - 1] if idx > 0 else None
    if idx < len(chapters) - 1:
        nxt = chapters[idx + 1]
        default_done = f"你已完成“{ch['short_title']}”的判断路径，并得到本章应交付的分析结论。"
        default_why = f"下一步继续解决：{nxt['description']}"
        done, why, action = HANDOFFS.get(ch["slug"], (default_done, default_why, f"继续：{nxt['short_title']}"))
        href, next_num, next_title = chapter_href(nxt, from_article), nxt["num"], nxt["short_title"]
    else:
        done, why, action = "你已经完成整套系统课程，现在需要在陌生业务证据中独立做判断。", "进入案例故事库，先做选择，再与真实复盘结果对照。", "开始独立案例训练"
        href, next_num, next_title = stories_link, "CASE", "业务案例库"
    previous_link = f'<a class="chapter-back-link" href="{chapter_href(prev, from_article)}">← 返回 {esc(prev["short_title"])}</a>' if prev else ""
    return f'''<nav class="chapter-handoff" aria-label="章节衔接"><div class="handoff-complete"><span>本章判断已完成</span><p>{esc(done)}</p></div><div class="handoff-next"><div class="handoff-next-copy"><span>为什么现在进入下一章</span><p>{esc(why)}</p></div><div class="handoff-target"><small>{esc(next_num)}</small><strong>{esc(next_title)}</strong></div></div><div class="handoff-actions">{previous_link}<a class="handoff-primary" href="{href}"><span>{esc(action)}</span><b aria-hidden="true">→</b></a></div></nav>'''


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
    learning_intro = f'''<section class="lesson-brief reveal"><div class="lesson-brief-main"><div class="section-eyebrow">本章任务</div><h2>学完后，你要交付什么</h2><ul>{objectives}</ul></div><div class="lesson-brief-side"><span>{esc(ch.get('duration', 10))} MIN</span><strong>{esc({'guide':'学习指南','case':'业务实战','concept':'方法理解','interview':'面试训练','career':'职业迁移'}.get(ch.get('content_type'), '课程'))}</strong></div></section>'''
    review_html = build_review(ch)
    course_nav = build_chapter_transition(ch, idx, chapters, from_article, stories_link)
    chapter_visual = "" if 'class="lesson-visual' in content else build_lesson_visual(ch)
    toc_data = [{"num": item["num"], "title": item["short_title"], "slug": item["slug"], "href": chapter_href(item, from_article), "module": item["module"], "description": item["description"]} for item in chapters]
    module_chapters = [c for c in chapters if c["module"] == ch["module"]]
    module_pos = module_chapters.index(ch) + 1
    module_progress = round(module_pos / len(module_chapters) * 100)
    lesson_body_class = "lesson-body lesson-body--guide" if ch["slug"] == "guide" else "lesson-body"

    return f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><meta name="description" content="{esc(ch['description'])}"><title>{esc(ch['title'])} · 分析手册</title>{SITE_ICON}{JS_FLAG}<style>:root {{ --theme: {esc(ch['theme'])}; --theme-rgb: {esc(ch['theme_rgb'])}; --module-theme: {esc(module['theme'])}; }}</style>{app_css_link(asset_path)}</head>
<body data-page="lesson" data-lesson="{esc(ch['slug'])}" data-default-mode="learn"><a class="skip-link" href="#lesson-content">跳到正文</a><div class="site-progress" style="--lesson-progress:{module_progress}%"><span></span></div><nav class="topnav"><a href="{home_link}" class="topnav-logo">分析手册</a><div class="topnav-links"><a class="active" href="{courses_link}">系统课程</a><a href="{'../topics/index.html' if from_article else 'topics/index.html'}">专题课程</a><a href="{stories_link}">业务案例</a></div></nav>
<main class="page lesson-page" id="lesson-content"><header class="lesson-header"><div class="module-line"><span>阶段 {esc(module['num'])}</span><strong>{esc(module['title'])}</strong><em>本阶段 {module_pos}/{len(module_chapters)}</em></div><p class="lesson-series">分析手册 · 系统课程</p><div class="lesson-title-row"><div><div class="ch-badge">{esc(ch['badge'])}</div><h1 class="ch-title static-title">{esc(ch['short_title'])}</h1></div><span class="lesson-duration">{esc(ch.get('duration', 10))}<small>分钟</small></span></div><p class="ch-subtitle lesson-description">{esc(ch['description'])}</p><div class="mode-switch" role="group" aria-label="阅读模式"><button type="button" class="active" data-mode-target="learn"><span>完整学习</span><small>案例、图解与推导</small></button><button type="button" data-mode-target="review"><span>面试速览</span><small>主线、答案与失分点</small></button></div></header>
<div id="learn-mode" class="learning-mode active">{learning_intro}{chapter_visual}<div class="{lesson_body_class}">{content}</div></div><div id="review-mode" class="learning-mode">{review_html}</div>{course_nav}</main>
<button id="toc-toggle" class="toc-toggle" type="button"><span class="toc-toggle-icon" aria-hidden="true"><i></i><i></i><i></i></span><span class="toc-toggle-copy"><small>当前路线</small><strong>{esc(ch['num'])} · {esc(ch['short_title'])}</strong></span></button><aside id="toc-panel" class="toc-panel" aria-label="课程路线"></aside><div id="toc-overlay" class="toc-overlay"></div>
<script src="{asset_path}main.js"></script><script>window.TOC_CHAPTERS = {json.dumps(toc_data, ensure_ascii=False)}; window.TOC_CURRENT = {json.dumps(ch['slug'], ensure_ascii=False)}; window.TOC_CURRENT_MODULE = {json.dumps(ch['module'], ensure_ascii=False)}; window.COURSE_MODULES = {json.dumps(list(modules_by_id.values()), ensure_ascii=False)};</script></body></html>'''

COURSE_OUTPUTS = {
    "guide": "一张个人学习路线与成果验收表",
    "ch02": "一份业务问题定义与汇报任务单",
    "ch03": "一棵口径明确、可下钻的指标树",
    "ch04": "一条从异常到根因的完整证据链",
    "ch05": "一份可上线、可回退的实验方案",
    "ch06": "一份包含收益、风险与灰度的上线决策",
    "ch07": "一套可执行的用户分层运营方案",
    "ch08": "一张 Cohort 留存诊断图与动作建议",
    "ch09": "一份能够回算的目标拆解表",
    "ch10": "一份避免汇总误判的分层分析结论",
    "ch11": "一份显著性、效应量与样本量判断说明",
    "ch12": "一份说明识别条件与局限的因果方案",
    "ch13": "一套有人审、有证据的 AI 分析流程",
    "ch14": "一张商业模式与关键指标地图",
    "ch15": "30 秒、90 秒与 3 分钟三个表达版本",
    "ch16": "一张一面与二面的回答侧重点清单",
    "ch17": "一套包含护栏指标的业务指标体系",
    "ch18": "一份 DAU 异动排查的结构化答案",
    "ch19": "一份包含上下界与敏感性的费米估算",
    "ch20": "一段可追问、可验证的 STAR 项目经历",
    "ch21": "一份完整模拟面试记录与复盘",
    "ch22": "一份收益—行为—生态三层策略评估",
    "ch23": "一份能解释数据结构与口径的 SQL 答案",
    "ch24": "一份与目标岗位对应的 90 天迁移计划",
    "ml01": "一张决定做分析、规则、实验还是模型的审查单",
    "ml02": "一份按处理容量排序的风险干预名单",
    "ml03": "一套按时间回测、可转成补货动作的预测方案",
    "ml04": "一份模型叫停、降级、修复与重测预案",
}


def module_card(module: dict, chapters: list[dict]) -> str:
    return f'''
<a class="stage-rail-link" href="#module-{esc(module['id'])}" data-stage-link="{esc(module['id'])}">
  <span class="stage-rail-index">{esc(module['num'])}</span>
  <span class="stage-rail-copy"><small>{esc(module['eyebrow'])}</small><strong>{esc(module['title'])}</strong></span>
  <em>{len(chapters)} 章</em>
</a>'''


def chapter_input(ch: dict) -> str:
    description = ch.get("description", "")
    parts = re.split(r"[。；]", description, maxsplit=1)
    return parts[0].strip("，。； ") or description


def chapter_card(ch: dict) -> str:
    type_names = {"guide":"指南","case":"业务实战","concept":"方法理解","interview":"面试训练","career":"职业迁移"}
    action = " → ".join(ch.get("framework", [])[:5]) or "观察 → 判断 → 输出"
    output = COURSE_OUTPUTS.get(ch["slug"], ch.get("objectives", ["一份可复用的分析结论"])[0])
    return f'''
<a href="{chapter_href(ch)}" class="curriculum-card reveal" style="--card-theme:{esc(ch['theme'])}">
  <div class="curriculum-card-head"><span class="curriculum-num">{esc(ch['num'])}</span><span>{esc(type_names.get(ch.get('content_type'),'课程'))}</span><em>{esc(ch.get('duration',10))} 分钟</em></div>
  <h3>{esc(ch['short_title'])}</h3>
  <p class="curriculum-summary">{esc(ch['description'])}</p>
  <dl class="curriculum-io">
    <div><dt>输入</dt><dd>{esc(chapter_input(ch))}</dd></div>
    <div><dt>判断</dt><dd>{esc(action)}</dd></div>
    <div><dt>产出</dt><dd>{esc(output)}</dd></div>
  </dl>
  <div class="curriculum-enter"><span>进入本章</span><b aria-hidden="true">↗</b></div>
</a>'''


def stage_visual(module_id: str) -> str:
    visuals = {
        "business-loop": '''<div class="stage-visual stage-visual-loop" aria-label="从异常到上线的业务闭环图">
          <div class="loop-alert"><span>业务异常</span><strong>打卡率 −18.6%</strong></div>
          <div class="loop-track"><i></i><i></i><i></i><i></i></div>
          <div class="loop-steps"><span>定义问题</span><span>检查证据</span><span>验证假设</span><span>灰度上线</span></div>
          <div class="loop-result"><small>最终判断</small><b>根因：渠道预期与产品体验错位</b></div>
        </div>''',
        "analysis-toolbox": '''<div class="stage-visual stage-visual-toolbox" aria-label="从业务问题选择分析方法的关系图">
          <div class="tool-question">这是什么问题？</div>
          <div class="tool-lines" aria-hidden="true"></div>
          <div class="tool-grid"><span>人群差异<small>分层 / Cohort</small></span><span>结果异常<small>指标树 / 下钻</small></span><span>策略增量<small>实验 / 因果</small></span><span>经营结果<small>目标 / 商业模式</small></span></div>
          <strong>先识别问题，再选择工具</strong>
        </div>''',
        "interview-output": '''<div class="stage-visual stage-visual-answer" aria-label="面试答案的三层表达结构">
          <div class="answer-clock"><span>30s</span><span>90s</span><span>3min</span></div>
          <div class="answer-stack"><p><b>结论</b>先回答面试官真正问的问题</p><p><b>证据</b>用项目事实支撑判断</p><p><b>取舍</b>说明限制、风险与下一步</p></div>
          <div class="answer-feedback"><i></i><span>表达训练：压缩判断过程</span></div>
        </div>''',
        "mock-career": '''<div class="stage-visual stage-visual-simulation" aria-label="完整模拟面试时间线">
          <div class="simulation-timeline"><i></i><i></i><i></i><i></i></div>
          <ol><li><b>00:00</b><span>自我定位</span></li><li><b>08:00</b><span>项目深挖</span></li><li><b>22:00</b><span>陌生案例</span></li><li><b>38:00</b><span>反问复盘</span></li></ol>
          <p><span>压力变化</span><i></i><b>稳定结构</b></p>
        </div>''',
        "ml-decision": '''<div class="stage-visual stage-visual-model" aria-label="机器学习项目的决策门">
          <div class="model-score"><small>离线 AUC</small><strong>0.94</strong><span>看起来很好</span></div>
          <div class="model-gate"><i></i><b>叫停</b><p>标签泄漏</p><p>没有行动出口</p></div>
          <div class="model-route"><span>规则基线</span><i>→</i><span>小流量验证</span><i>→</i><strong>业务净收益</strong></div>
        </div>''',
    }
    return visuals[module_id]

def story_visual(story: dict) -> str:
    # Compact, case-specific visual metaphor for the catalog card.
    n = int(story["num"])
    category = esc(story["category"])
    label = f'<div class="case-visual-label"><span>{category}</span><b>CASE {esc(story["num"])}</b></div>'
    visuals = {
        1: '<div class="viz-waterfall"><i style="--h:72%"></i><i class="plus" style="--h:91%"></i><i class="cost" style="--h:48%"></i><i class="cost" style="--h:24%"></i></div><strong class="viz-caption">GMV ↑ &nbsp; 利润 ↓</strong>',
        2: '<div class="viz-reports"><i></i><i></i><i></i><span>100</span><b>没有决策</b></div>',
        3: '<div class="viz-venn"><i>财务</i><i>业务</i><b>?</b></div>',
        4: '<div class="viz-funnel"><i></i><i></i><i class="break"></i><i></i><b>断点</b></div>',
        5: '<div class="viz-basket"><span>商品数</span><b>2.8</b><i>×</i><span>件单价</span><b>¥42</b></div>',
        6: '<div class="viz-cohort">' + ''.join(f'<i style="--o:{v}"></i>' for v in (1,.86,.68,.47,.31,.2,.13,.08,.65,.54,.42,.28,.17,.1)) + '</div>',
        7: '<div class="viz-balance"><span>速度</span><i></i><span>质量</span><b>KPI</b></div>',
        8: '<div class="viz-rfm"><i></i><i></i><i></i><i class="vip"></i><b>VIP</b></div>',
        9: '<div class="viz-retention"><svg viewBox="0 0 240 90"><path d="M5 14 C42 15 56 38 83 44 S126 62 158 65 S202 69 235 70"/><path class="compare" d="M5 13 C50 14 71 24 102 28 S178 38 235 40"/></svg><b>激活断点</b></div>',
        10: '<div class="viz-timeline"><i></i><i></i><i></i><i class="quiet"></i><i class="quiet"></i><span>多久算沉默？</span></div>',
        11: '<div class="viz-ltv"><svg viewBox="0 0 240 90"><path d="M5 78 Q50 47 86 43 T150 24 T235 12"/></svg><span>LTV</span><b>回收期</b></div>',
        12: '<div class="viz-radar"><i></i><span>可行动画像</span></div>',
        13: '<div class="viz-pareto"><i></i><i></i><i></i><i></i><i></i><svg viewBox="0 0 240 80"><path d="M4 68 Q60 15 236 10"/></svg><b>20% → 80%</b></div>',
        14: '<div class="viz-matrix"><i></i><i class="star">爆款</i><i></i><i></i></div>',
        15: '<div class="viz-aging"><i><b>0–30</b></i><i><b>31–60</b></i><i><b>61–90</b></i><i class="risk"><b>90+</b></i></div>',
        16: '<div class="viz-elasticity"><svg viewBox="0 0 240 90"><path d="M8 12 Q86 26 230 78"/><line x1="102" y1="8" x2="102" y2="82"/></svg><b>利润最优点</b></div>',
        17: '<div class="viz-balance campaign"><span>GMV</span><i></i><span>利润</span><b>大促复盘</b></div>',
        18: '<div class="viz-experiment"><section><span>A</span><b>自然转化</b></section><section><span>B</span><b>优惠券</b></section><i>增量？</i></div>',
        19: '<div class="viz-live"><i style="--w:100%"></i><i style="--w:68%"></i><i style="--w:31%"></i><i class="break" style="--w:11%"></i><b>停留 → 下单</b></div>',
        20: '<div class="viz-membership"><span>会员日</span><i>+18%</i><b>来自谁？</b></div>',
        21: '<div class="viz-roi"><i style="--h:78%"><b>A</b></i><i style="--h:48%"><b>B</b></i><i class="winner" style="--h:92%"><b>C</b></i><i style="--h:34%"><b>D</b></i></div>',
        22: '<div class="viz-path"><span>搜索</span><i>→</i><span>内容</span><i>→</i><span>广告</span><b>谁贡献了转化？</b></div>',
        23: '<div class="viz-dual"><section><span>自然</span><i></i><b>长期价值</b></section><section><span>付费</span><i></i><b>即时规模</b></section></div>',
        24: '<div class="viz-tree"><strong>销售额 −20%</strong><i></i><section><span>流量</span><span>转化</span><span>客单</span></section><b>从哪里下钻？</b></div>',
        25: '<div class="viz-roadmap"><i></i><i></i><i></i><i></i><span>复盘</span><span>目标</span><span>策略</span><span>资源</span></div>',
        26: '<div class="viz-model"><strong>0.94</strong><span>离线 AUC</span><i></i><b>运营叫停</b><em>超时订单更多</em></div>',
    }
    return f'<div class="case-visual case-visual--{n:02d}" aria-hidden="true">{label}{visuals[n]}</div>'


def story_card(story: dict, href_prefix="stories/", show_visual: bool = False) -> str:
    tags = "".join(f"<span>{esc(tag)}</span>" for tag in story["tags"][:3])
    return f'''
<a class="story-library-card reveal case-card-{esc(story['num'])}" href="{href_prefix}{esc(story['output'])}" data-category="{esc(story['category'])}" data-title="{esc(story['title'])} {' '.join(story['tags'])}">
  <div class="story-card-head"><span>案例 {esc(story['num'])}</span><em>{esc(story['difficulty'])} · {esc(story['duration'])} 分钟</em></div>
  {story_visual(story)}
  <div class="story-card-copy"><h3>{esc(story['title'])}</h3><p>{esc(story['subtitle'])}</p></div>
  <div class="story-card-tags">{tags}</div><strong>进入现场 <i>→</i></strong>
</a>'''

def build_landing(chapters: list[dict], modules: list[dict], stories: list[dict], topics: list[dict]) -> str:
    first_lesson = chapter_href(chapters[0])
    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="description" content="在真实业务问题中练习定义、验证、决策与表达。"><title>分析手册 · 练习在不确定中做判断</title>
{app_css_link('assets/')}{SITE_ICON}{JS_FLAG}</head>
<body data-page="landing"><a class="skip-link" href="#main">跳到正文</a>
<nav class="topnav"><a href="index.html" class="topnav-logo">分析手册</a><div class="topnav-links"><a href="courses.html">系统课程</a><a href="topics/index.html">专题课程</a><a href="stories/index.html">业务案例</a></div></nav>
<main class="landing" id="main">
  <section class="landing-hero">
    <div class="landing-hero__copy"><p class="landing-eyebrow">ANALYST HANDBOOK · 2026</p><h1>在不确定中，<br><span>练习做判断。</span></h1><p class="landing-lead">把模糊问题逐步转化为证据、选择与行动。系统课建立方法，专题拆透机制，业务案例检验你是否真的会用。</p><div class="home-actions"><a class="primary" href="courses.html">开始建立框架</a><a href="stories/index.html">直接进入案例</a></div></div>
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
  <section class="learning-loop"><div><p>学习闭环</p><h2>课程内容会在不同业务问题中反复调用。</h2><small>每一轮都应留下新的判断依据与可复用成果。</small></div><ol><li><span>01</span><div><strong>理解</strong><p>先建立概念、适用边界和判断顺序。</p></div></li><li><span>02</span><div><strong>观察</strong><p>让数据和业务证据真正改变你的初始结论。</p></div></li><li><span>03</span><div><strong>决策</strong><p>在时间、资源和风险限制下选择下一步行动。</p></div></li><li><span>04</span><div><strong>复盘</strong><p>解释为什么会误判，以及方法如何迁移到陌生场景。</p></div></li></ol></section>
  <section class="landing-start"><p>如果你第一次来到这里</p><h2>先完成第一章，建立这套手册的使用方式。</h2><a href="{first_lesson}">开始第 01 章 <span>→</span></a></section>
</main><footer class="site-footer"><span>分析手册</span><p>为真实业务判断与能力迁移而设计。</p></footer><script src="assets/main.js"></script></body></html>'''


def build_course_index(chapters: list[dict], modules: list[dict], stories: list[dict], topics: list[dict]) -> str:
    module_sections = []
    module_cards = []
    for module in modules:
        items = [ch for ch in chapters if ch["module"] == module["id"]]
        module_cards.append(module_card(module, items))
        module_sections.append(f'''
<section class="curriculum-stage stage-{esc(module['id'])}" id="module-{esc(module['id'])}" data-course-stage="{esc(module['id'])}" style="--stage-theme:{esc(module['theme'])}">
  <header class="curriculum-stage-head">
    <div class="curriculum-stage-copy"><span>阶段 {esc(module['num'])} · {esc(module['eyebrow'])}</span><h2>{esc(module['title'])}</h2><p>{esc(module['description'])}</p><div class="stage-outcome"><small>阶段成果</small><strong>{esc(module['outcome'])}</strong></div></div>
    {stage_visual(module['id'])}
  </header>
  <div class="curriculum-grid">{''.join(chapter_card(ch) for ch in items)}</div>
</section>''')
    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="description" content="28章系统课程：从业务问题、分析方法到机器学习与面试表达。"><title>系统课程 · 分析手册</title>
{app_css_link('assets/')}{SITE_ICON}{JS_FLAG}</head>
<body data-page="courses"><nav class="topnav"><a href="index.html" class="topnav-logo">分析手册</a><div class="topnav-links"><a class="active" href="courses.html">系统课程</a><a href="topics/index.html">专题课程</a><a href="stories/index.html">业务案例</a></div></nav>
<main class="course-system">
<header class="course-system-hero">
  <div class="course-system-copy"><p>系统课程 · {len(chapters)} 章 · 5 个能力阶段</p><h1>用 28 章内容，<br><span>建立一套判断系统</span></h1><div class="course-system-lead">从一场真实业务异常出发，学习如何寻找证据、选择方法、形成决策，并把完整判断讲给面试官与业务负责人听。</div><div class="course-system-actions"><a class="primary" href="{chapter_href(chapters[0])}">从第一场任务开始 <b>→</b></a><a href="#course-system-map">查看五阶段路线</a></div><dl class="course-system-stats"><div><dt>{len(chapters)}</dt><dd>章完整课程</dd></div><div><dt>5</dt><dd>次能力升级</dd></div><div><dt>1</dt><dd>套可迁移系统</dd></div></dl></div>
  <div class="decision-engine" data-course-engine aria-label="业务问题转化为决策的动态演示">
    <div class="decision-engine-bar"><span><i></i>判断引擎运行中</span><em>真实业务现场</em></div>
    <div class="decision-incident"><small>当前任务</small><strong>新用户打卡率突然下跌 18.6%</strong><p>运营希望今天给出原因和上线建议</p></div>
    <div class="decision-signals"><span><small>新用户量</small><b>+21%</b></span><span class="is-alert"><small>首日完成率</small><b>−18.6%</b></span><span><small>系统报错</small><b>稳定</b></span></div>
    <div class="decision-pipeline" aria-label="问题、证据、方法、决策、表达">
      <span class="is-active"><i>01</i><b>问题</b></span><span><i>02</i><b>证据</b></span><span><i>03</i><b>方法</b></span><span><i>04</i><b>决策</b></span><span><i>05</i><b>表达</b></span>
    </div>
    <div class="decision-output"><small>最终交付</small><strong>一条可验证、可上线、可解释的判断链</strong></div>
  </div>
</header>
<section class="learning-os" aria-labelledby="learning-os-title">
  <header><p>学习操作系统</p><h2 id="learning-os-title">每一章都要完成一次<br>输入、判断与输出</h2><div>沉浸感来自持续接收任务、观察证据、做出选择并获得反馈。</div></header>
  <div class="learning-os-grid">
    <article class="os-scene"><div class="os-visual"><span>09:42</span><i></i><i></i><b>异常 −18.6%</b></div><small>01 · 进入现场</small><h3>先接收一个不完整的问题</h3><p>知道谁在等结论、为什么现在要判断，以及最后必须交付什么。</p></article>
    <article class="os-reason"><div class="os-visual"><span>现象</span><i>→</i><span>证据</span><i>→</i><strong>判断</strong></div><small>02 · 看见关系</small><h3>把文字变成可以检查的结构</h3><p>用指标树、实验分流、因果路径和决策门看见推理中间过程。</p></article>
    <article class="os-output"><div class="os-visual"><span></span><span></span><b>可复用</b><i>✓</i></div><small>03 · 完成产出</small><h3>每次学习都留下业务成果</h3><p>每章都会留下方案、清单、图表、答案或复盘。</p></article>
  </div>
</section>
<section class="course-map-intro" id="course-system-map"><p>完整课程地图</p><h2>五次能力升级，共用一条判断主线</h2><div>滚动页面时，路线会自动告诉你现在位于哪个阶段。你也可以直接选择阶段开始。</div></section>
<nav class="stage-rail" aria-label="课程阶段">{''.join(module_cards)}</nav>
<div class="curriculum-stages">{''.join(module_sections)}</div>
<section class="course-finish"><div><p>课程最终目标</p><h2>在陌生问题里，稳定地把判断做完</h2></div><a href="{chapter_href(chapters[0])}">开始第一章 <span>→</span></a></section>
</main><footer class="site-footer"><span>系统课程</span><p>问题 → 证据 → 方法 → 决策 → 表达</p></footer><script src="assets/main.js"></script><script src="assets/course-index.js"></script></body></html>'''

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
<title>业务案例 · 分析手册</title>{app_css_link('../assets/')}{SITE_ICON}{JS_FLAG}</head>
<body data-page="story-library">
<nav class="topnav"><a href="../index.html" class="topnav-logo">分析手册</a><div class="topnav-links"><a href="../courses.html">系统课程</a><a href="../topics/index.html">专题课程</a><a class="active" href="index.html">业务案例</a></div></nav>
<main class="story-library-page">
  <header class="story-library-hero"><div class="story-hero-copy"><div class="home-kicker">业务案例</div><h1>信息并不完整，<br><span>你仍然要做判断</span></h1><p>先接收任务，再观察证据、选择方向、验证假设。案例让你完整经历一次业务分析。</p><div class="home-actions"><a class="primary" href="{esc(stories[0]['output'])}">进入第一个案例</a><a href="#story-catalog">浏览全部案例</a></div></div><div class="case-preview" aria-label="案例任务示意"><div class="case-preview-head"><span>CASE 01</span><em>限时决策</em></div><h2>大促 GMV 上升，<br>为什么利润反而下降？</h2><div class="case-clues"><span>客单价 <b>+12%</b></span><span>毛利率 <b>−8.4%</b></span><span>退款率 <b>+5.7%</b></span></div><div class="case-preview-action"><i></i><span>还有 3 条证据尚未查看</span><b>→</b></div></div></header>
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
<meta name="description" content="围绕业务分析、机器学习、A/B 测试、业务工作坊和分析交付组织的专题课程。">
<title>专题课程 · 分析手册</title>{app_css_link('../assets/')}{SITE_ICON}{JS_FLAG}</head>
<body class="topic-body" data-page="topic-index"><nav class="topnav topic-nav"><a href="../index.html" class="topnav-logo">分析手册</a><div class="topnav-links"><a href="../courses.html">系统课程</a><a class="active" href="index.html">专题课程</a><a href="../stories/index.html">业务案例</a></div></nav>
<main class="topic-index"><header class="topic-index-hero"><div class="topic-index-copy"><p>专题课程</p><h1>看见方法<br>如何发生</h1><div>这里不按软件菜单或算法名堆知识。每一节从一个具体问题开始，用连续演示解释判断过程、实现方法、失败边界和面试表达。</div></div><div class="topic-index-visual" aria-hidden="true"><span class="topic-orbit orbit-one">方法</span><span class="topic-orbit orbit-two">业务</span><span class="topic-orbit orbit-three">实验</span><span class="topic-orbit orbit-four">ML</span><strong>业务<br>问题</strong><i></i></div></header>
<section class="topic-list" aria-label="专题课程列表">{''.join(rows)}</section>
<section class="topic-note"><h2>内容怎么读</h2><p>先看过程演示，理解为什么这样判断；再读下方的知识解释和失败案例。动画负责展示过程，正文负责完整解释，两者共同构成课程内容。</p></section>
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
{SITE_ICON}{JS_FLAG}
<style>:root{{--theme:{esc(topic['theme'])};--theme-rgb:{esc(topic['theme_rgb'])}}}</style>{app_css_link('../assets/')}</head>
<body class="topic-body" data-page="topic"><a class="skip-link" href="#topic-content">跳到正文</a>
<nav class="topnav topic-nav"><a href="../index.html" class="topnav-logo">分析手册</a><div class="topnav-links"><a href="../courses.html">系统课程</a><a class="active" href="index.html">专题课程</a><a href="../stories/index.html">业务案例</a></div></nav>
<main class="topic-page" id="topic-content"><header class="topic-hero"><div class="topic-breadcrumb"><a href="index.html">专题课程</a><span>/</span><span>{esc(topic['category'])}</span></div><p class="topic-number">{esc(topic['num'])} · {esc(topic['level'])} · {esc(topic['duration'])} 分钟</p><h1>{esc(topic['title'])}</h1><div class="topic-lead">{esc(topic['subtitle'])}</div></header>
<section class="topic-objectives" aria-labelledby="objectives-title"><h2 id="objectives-title">这一节要解决什么</h2><ol>{objectives}</ol></section>
{content}
<nav class="topic-pagination" aria-label="专题课程翻页">{''.join(links)}</nav></main>
<script src="../assets/topic-course.js"></script></body></html>'''

def inject_story_shell(source: str, story: dict, prev_story: dict | None, next_story: dict | None, story_count: int) -> str:
    head_extra = f'<link rel="icon" href="data:,">\n<link rel="stylesheet" href="../assets/story.css?v={ASSETS["story"]}">\n'
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

    ASSETS["app"] = bundle_css(APP_CSS_SOURCES, "app.css")
    ASSETS["story"] = bundle_css(STORY_CSS_SOURCES, "story.css")
    print(f"  CSS    app.css?v={ASSETS['app']} · story.css?v={ASSETS['story']}")

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

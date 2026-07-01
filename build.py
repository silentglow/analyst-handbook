#!/usr/bin/env python3
"""
数据分析面试速通课 · 构建脚本
读取 chapters.json 中的章节数据，生成 HTML 页面。
新增章节只需要在 chapters.json 中添加数据，运行 python build.py 即可。
"""
import json
import os

TAILWIND_CDN = '''<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {
    theme: {
      extend: {
        colors: {
          surface: { 900: '#06070a', 800: '#0c0d12' },
          accent: { cyan: '#5eead4', purple: '#a78bfa', blue: '#60a5fa', amber: '#fbbf24' },
        }
      }
    }
  }
</script>'''

TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="stylesheet" href="{asset_path}style.css">
{tailwind}
<style>:root {{ --theme: {theme}; --theme-rgb: {theme_rgb}; }}</style>
</head>
<body>
<div style="position:fixed;inset:0;pointer-events:none;z-index:0;overflow:hidden">
  <div class="orb" style="width:600px;height:600px;background:radial-gradient(circle,rgba({theme_rgb},0.12),transparent 70%);top:-200px;left:-100px"></div>
  <div class="orb" style="width:500px;height:500px;background:radial-gradient(circle,rgba(167,139,250,0.10),transparent 70%);top:30%;right:-150px;animation-delay:-3s"></div>
  <div class="orb" style="width:400px;height:400px;background:radial-gradient(circle,rgba(96,165,250,0.06),transparent 70%);bottom:-100px;left:30%;animation-delay:-6s"></div>
</div>
<div class="grid-bg"></div>
<nav class="topnav">
  <a href="{home_link}" class="topnav-logo">DATA ANALYSIS</a>
  <div class="topnav-links">
    <a href="{home_link}">目录</a>
    <a href="#">笔记</a>
  </div>
</nav>
<main class="page">
  <header style="margin-bottom:48px">
    <div class="ch-badge">{badge}</div>
    <h1 class="ch-title" id="typewriter"></h1>
    {subtitle_html}
  </header>
  {content}
  {nav_html}
</main>
<div id="toc-toggle" class="toc-toggle">目录</div>
<div id="toc-panel" class="toc-panel"></div>
<div id="toc-overlay" class="toc-overlay"></div>
<script src="{asset_path}main.js"></script>
<script>
const TOC_CHAPTERS = {toc_data};
const TOC_CURRENT = "{slug}";
initTypewriter('typewriter', {typewriter_lines});
</script>
</body>
</html>'''

NEXT_TPL = '''  <div class="next-ch reveal">
    <div class="next-label">{label}</div>
    <a href="{link}" class="next-link">{text} <span class="arr">→</span></a>
  </div>'''

PREV_TPL = '''  <div class="prev-ch reveal" style="margin-bottom:48px">
    <a href="{link}" class="next-link" style="font-size:16px"><span class="arr" style="transform:rotate(180deg);display:inline-block">→</span> {text}</a>
  </div>'''

SUBTITLE_TPL = '    <p class="ch-subtitle" style="opacity:0;animation:fadeUp 1s ease-out 1.5s forwards">{text}</p>'


def build():
    base = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base, 'chapters.json'), 'r', encoding='utf-8') as f:
        chapters = json.load(f)

    for idx, ch in enumerate(chapters):
        slug = ch['slug']
        is_root = ch.get('is_root', False)
        
        if is_root:
            out_path = os.path.join(base, 'index.html')
            asset_path = 'assets/'
            home_link = 'home.html'
        else:
            out_path = os.path.join(base, 'articles', f'{slug}.html')
            asset_path = '../assets/'
            home_link = '../home.html'
        # Build prev and next navigation
        prev_html = ''
        if idx > 0:
            prev_ch = chapters[idx - 1]
            prev_html = PREV_TPL.format(
                link=f"{prev_ch['slug']}.html" if not prev_ch.get('is_root') else '../index.html',
                text=f"上一章 · {prev_ch['short_title']}"
            )

        next_html = ''
        if 'next' in ch:
            n = ch['next']
            next_html = NEXT_TPL.format(
                label=n.get('label', '下一章'),
                link=n['link'],
                text=n['text']
            )

        nav_html = prev_html + '\n' + next_html if prev_html else next_html

        subtitle_html = ''
        if 'subtitle' in ch:
            subtitle_html = SUBTITLE_TPL.format(text=ch['subtitle'])

        content_path = os.path.join(base, 'content', f'{slug}.html')
        with open(content_path, 'r', encoding='utf-8') as f:
            content = f.read()

        toc_data = json.dumps([{
            'num': c['num'],
            'title': c['short_title'],
            'slug': c['slug'],
            'is_root': c.get('is_root', False)
        } for c in chapters], ensure_ascii=False)

        html = TEMPLATE.format(
            title=ch['title'],
            theme=ch['theme'],
            theme_rgb=ch['theme_rgb'],
            badge=ch['badge'],
            typewriter_lines=json.dumps(ch['typewriter'], ensure_ascii=False),
            subtitle_html=subtitle_html,
            content=content,
            nav_html=nav_html,
            asset_path=asset_path,
            home_link=home_link,
            tailwind=TAILWIND_CDN,
            slug=slug,
            toc_data=toc_data,
        )

        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f'  ✅ {slug}')

    build_home(base, chapters)
    print(f'\n✅ 共生成 {len(chapters)} 个章节 + 首页')


def build_home(base, chapters):
    cards = []
    colors = {
        '#5eead4': ('cyan', '5eead4'),
        '#fbbf24': ('amber', 'fbbf24'),
        '#a78bfa': ('purple', 'a78bfa'),
        '#60a5fa': ('blue', '60a5fa'),
    }
    for ch in chapters:
        slug = ch['slug']
        if ch.get('is_root'):
            link = 'index.html'
        else:
            link = f'articles/{slug}.html'
        theme = ch['theme']
        cname = colors.get(theme, ('cyan', '5eead4'))[0]
        cards.append(f'    <a href="{link}" class="glass reveal block p-6 transition-all duration-300 cursor-pointer group no-underline">\n'
                     f'      <div class="flex items-center gap-5">\n'
                     f'        <span class="font-mono text-2xl text-accent-{cname} font-bold shrink-0">{ch["num"]}</span>\n'
                     f'        <div class="flex-1 min-w-0">\n'
                     f'          <h3 class="text-white font-semibold text-lg mb-1 group-hover:text-accent-{cname} transition-colors">{ch["short_title"]}</h3>\n'
                     f'          <p class="text-white/40 text-sm leading-relaxed">{ch["description"]}</p>\n'
                     f'        </div>\n'
                     f'        <span class="text-white/20 group-hover:text-accent-{cname} group-hover:translate-x-1 transition-all shrink-0">→</span>\n'
                     f'      </div>\n'
                     f'    </a>')

    cards_html = '\n'.join(cards)

    home_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>数据分析面试速通课</title>
<link rel="stylesheet" href="assets/style.css">
{TAILWIND_CDN}
</head>
<body>
<div style="position:fixed;inset:0;pointer-events:none;z-index:0;overflow:hidden">
  <div class="orb" style="width:600px;height:600px;background:radial-gradient(circle,rgba(94,234,212,0.12),transparent 70%);top:-200px;left:-100px"></div>
  <div class="orb" style="width:500px;height:500px;background:radial-gradient(circle,rgba(167,139,250,0.10),transparent 70%);top:30%;right:-150px;animation-delay:-3s"></div>
  <div class="orb" style="width:400px;height:400px;background:radial-gradient(circle,rgba(96,165,250,0.06),transparent 70%);bottom:-100px;left:30%;animation-delay:-6s"></div>
</div>
<div class="grid-bg"></div>
<nav class="topnav">
  <a href="home.html" class="topnav-logo">DATA ANALYSIS</a>
  <div class="topnav-links"><a href="#">笔记</a></div>
</nav>
<main class="page">
  <header style="margin-bottom:48px">
    <h1 class="ch-title" style="min-height:auto;background:linear-gradient(135deg,#fff 0%,#5eead4 50%,#a78bfa 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">数据分析面试速通课</h1>
    <p class="ch-subtitle" style="opacity:0;animation:fadeUp 1s ease-out 0.5s forwards">跟着鲜食记APP的真实业务案例，走完从发现问题到解决问题的完整链路。</p>
  </header>
  <div class="space-y-4">
{cards_html}
  </div>
  <div class="reveal" style="margin-top:64px;padding-top:32px;border-top:1px solid rgba(255,255,255,0.06);text-align:center">
    <p style="color:rgba(255,255,255,0.3);font-size:14px">建议按顺序阅读，每一章都建立在前一章的基础上。</p>
  </div>
</main>
<script src="assets/main.js"></script>
</body>
</html>'''

    with open(os.path.join(base, 'home.html'), 'w', encoding='utf-8') as f:
        f.write(home_html)


if __name__ == '__main__':
    build()
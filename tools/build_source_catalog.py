#!/usr/bin/env python3
"""Build the course-reform ledger without copying the multi-GB source DOCX files."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

PROJECT = Path(__file__).resolve().parents[1]
SOURCE = Path('/Users/gq/Projects/data_learn')
INVENTORY = Path('/tmp/data_learn_inventory.json')
OUT = PROJECT / 'data' / 'content-reform-ledger.json'

RANGES = [
    (1, 7, '数据分析基础', 'business-foundations'),
    (12, 37, 'Excel', 'business-toolkit'),
    (38, 48, 'Tableau', 'business-toolkit'),
    (49, 70, 'SQL', 'business-sql'),
    (71, 85, 'Python', 'python-case-lab'),
    (86, 156, '机器学习', 'machine-learning-zero-to-one'),
    (157, 179, '业务方法', 'business-foundations'),
    (180, 214, 'A/B 测试', 'ab-testing'),
    (215, 231, '游戏氪金', 'business-case-lab'),
    (232, 245, '异常订单', 'business-case-lab'),
    (246, 287, '广告投放', 'business-case-lab'),
    (288, 305, '用户流失', 'machine-learning-zero-to-one'),
    (306, 318, '数据分析报告', 'interview-and-communication'),
]


def sequence(name: str) -> int:
    match = re.match(r'(\d+)_', name)
    return int(match.group(1)) if match else 9999


def classify(seq: int) -> tuple[str, str]:
    for lo, hi, category, track in RANGES:
        if lo <= seq <= hi:
            return category, track
    return '待复核', 'source-review'


def decision(seq: int, name: str, category: str) -> dict:
    case = any(word in name for word in ('案例', '实操', '实战', '项目'))
    interview = '面试' in name
    animation_words = ('原理', '流程', '分流', '树', '聚类', 'KMeans', 'kmeans', '假设检验', '漏斗', '留存', '异动', '归因', '开窗', '多表')
    animation = any(word in name for word in animation_words)

    if category == 'Excel':
        if case or seq >= 31:
            return dict(disposition='重构为业务任务', formats=['综合案例', '按需展开工具', '自测'], collection='业务技术实验室 · Excel', rationale='保留完整业务任务和操作判断，但不把函数与菜单拆成冗长主线。', animation_candidate=animation)
        return dict(disposition='合并为按需参考', formats=['可搜索参考', '微交互演示'], collection='业务技术实验室 · Excel 参考', rationale='基础操作有价值，但应在案例需要时展开，避免连续阅读工具说明。', animation_candidate=animation)
    if category == 'Tableau':
        if case:
            return dict(disposition='重构为可视化决策案例', formats=['综合案例', '图表选择复盘'], collection='可视化表达专题', rationale='保留从问题到图表再到判断的过程，去除软件界面截图依赖。', animation_candidate=True)
        return dict(disposition='合并为可视化参考', formats=['图表选择卡', '交互演示'], collection='可视化表达专题', rationale='软件按钮会过时，保留图表语义、适用条件与表达风险。', animation_candidate=True)
    if category == 'SQL':
        if seq <= 56:
            return dict(disposition='压缩为按需参考', formats=['数据结构速查', '高频题前置知识'], collection='业务 SQL', rationale='SQL 语法本身不作为完整主线，只保留解决业务查询所需的最小知识。', animation_candidate=False)
        return dict(disposition='重构为业务 SQL 题型', formats=['业务数据结构', '高频面试题', '错误查询复盘'], collection='业务 SQL', rationale='围绕粒度、主键、事实表/维表及业务指标组织，而不是照搬语法章节。', animation_candidate=animation)
    if category == 'Python':
        if case or seq >= 79:
            return dict(disposition='重构为综合分析案例', formats=['Python 综合案例', '代码解释', '业务交付'], collection='Python 综合分析', rationale='保留清洗、探索、建模和交付的完整链路，基础语法仅在使用处展开。', animation_candidate=animation)
        return dict(disposition='合并为案例内参考', formats=['按需代码卡', '常见错误'], collection='Python 综合分析 · 参考', rationale='不单独铺设大量变量、容器和循环基础，转为案例中的即时帮助。', animation_candidate=False)
    if category == '机器学习':
        return dict(disposition='完整重构并纳入系统课', formats=['原理课', '参数实验', '代码实战', '评估调优', '面试追问'], collection='机器学习从 0 到 1', rationale='该部分讲解完整，保留原理—代码—评估—调优链路，并补充业务判断与失败案例。', animation_candidate=animation)
    if category == 'A/B 测试':
        return dict(disposition='完整重构并保留详细度', formats=['系统课', 'HTML 动画', '面试题与详解', 'Python 实战', '失败案例'], collection='A/B 测试专题', rationale='知识讲解、问题回答与追问均有价值，重排结构但不做过度压缩。', animation_candidate=True if animation or 188 <= seq <= 214 else False)
    if category == '业务方法':
        return dict(disposition='重构为业务判断课程', formats=['方法课', '决策动画', '失败案例', '面试表达'], collection='业务分析与面试', rationale='从方法定义转向真实决策过程，明确证据、边界与错误方向。', animation_candidate=animation)
    if category in ('游戏氪金', '异常订单', '广告投放'):
        return dict(disposition='并入端到端业务案例', formats=['综合案例', '证据关卡', '复盘', '面试项目'], collection=f'业务案例 · {category}', rationale='保留项目完整性，合并重复操作，把每一步改造成可判断、可复盘的业务任务。', animation_candidate=animation)
    if category == '用户流失':
        return dict(disposition='拆解为方法实验，不作典型主线', formats=['特征工程实验', '模型评估', '定义风险复盘'], collection='机器学习从 0 到 1 · 方法实验', rationale='真实业务中流失标签与观察窗口常不稳定；提取通用建模知识，同时明确它不应被包装成天然成立的基础案例。', animation_candidate=animation)
    if category == '数据分析报告':
        return dict(disposition='重构为交付与表达训练', formats=['报告工作坊', '反例改写', '面试表达'], collection='分析交付与沟通', rationale='保留报告结构与制作流程，改为从业务决策倒推表达，而不是版式说明书。', animation_candidate=animation)
    if category == '数据分析基础':
        return dict(disposition='合并为学习起点', formats=['学习指南', '能力地图', '情境自测'], collection='业务分析与面试', rationale='保留数据思维和岗位价值，删除重复定义，用真实任务建立学习动机。', animation_candidate=animation)
    return dict(disposition='人工复核', formats=['来源审查'], collection='来源治理', rationale='编号不在当前课程范围内，发布前需人工确认归属。', animation_candidate=False)


PUBLISHED_SAMPLES = {
    164: 'labs/incident-analysis.html',
    59: 'labs/sql-grain.html', 61: 'labs/sql-grain.html', 62: 'labs/sql-grain.html',
    79: 'labs/python-customer-value.html', 80: 'labs/python-customer-value.html', 83: 'labs/python-customer-value.html',
    93: 'labs/kmeans-lab.html', 94: 'labs/kmeans-lab.html', 95: 'labs/kmeans-lab.html', 96: 'labs/kmeans-lab.html',
    97: 'labs/kmeans-lab.html', 98: 'labs/kmeans-lab.html', 99: 'labs/kmeans-lab.html', 100: 'labs/kmeans-lab.html',
    188: 'labs/ab-test-flow.html', 213: 'labs/ab-test-flow.html', 214: 'labs/ab-test-flow.html',
}

def load_metrics(files: list[Path]) -> dict[str, dict]:
    if INVENTORY.exists():
        return {row['file']: row for row in json.loads(INVENTORY.read_text(encoding='utf-8'))}
    namespace = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    result = {}
    for path in files:
        with ZipFile(path) as archive:
            root = ET.fromstring(archive.read('word/document.xml'))
            paragraphs = root.findall('.//w:p', namespace)
            text_chars = sum(len(''.join(node.text or '' for node in p.findall('.//w:t', namespace))) for p in paragraphs)
            media = [info for info in archive.infolist() if info.filename.startswith('word/media/')]
            result[path.name] = {
                'file': path.name, 'mb': round(path.stat().st_size / 1024 / 1024, 2),
                'images': len(media), 'image_mb': round(sum(info.file_size for info in media) / 1024 / 1024, 2),
                'paragraphs': len(paragraphs), 'text_chars': text_chars,
            }
    return result

def main() -> None:
    files = sorted(SOURCE.glob('*.docx'), key=lambda p: (sequence(p.name), p.name))
    if not files:
        raise SystemExit(f'No DOCX files found in: {SOURCE}')
    metrics = load_metrics(files)
    rows = []
    for idx, path in enumerate(files, 1):
        seq = sequence(path.name)
        category, track = classify(seq)
        policy = decision(seq, path.name, category)
        measure = metrics.get(path.name, {})
        rows.append({
            'ledger_id': f'SRC-{idx:03d}',
            'sequence': seq,
            'source_file': path.name,
            'source_locator': f'data_learn/{path.name}',
            'category': category,
            'destination_track': track,
            'target_collection': policy['collection'],
            'disposition': policy['disposition'],
            'target_formats': policy['formats'],
            'rationale': policy['rationale'],
            'animation_candidate': policy['animation_candidate'],
            'source_metrics': {
                'file_mb': measure.get('mb'),
                'image_count': measure.get('images'),
                'image_mb_unpacked': measure.get('image_mb'),
                'paragraphs': measure.get('paragraphs'),
                'text_chars': measure.get('text_chars'),
            },
            'rights_and_freshness_review': 'required',
            'target_pages': [PUBLISHED_SAMPLES[seq]] if seq in PUBLISHED_SAMPLES else [],
            'status': 'sample-published' if seq in PUBLISHED_SAMPLES else 'catalogued',
        })
    summary = {
        'source_root': '/Users/gq/Projects/data_learn',
        'document_count': len(rows),
        'policy': '不发布原始 DOCX 与大图；按知识语义重写为课程、案例、题库或原生 HTML 动画。',
        'counts_by_category': dict(Counter(r['category'] for r in rows)),
        'counts_by_disposition': dict(Counter(r['disposition'] for r in rows)),
        'animation_candidates': sum(r['animation_candidate'] for r in rows),
        'ledger_status': '第一轮自动编目完成；内容制作时逐项更新目标页面与审校状态。',
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({'summary': summary, 'documents': rows}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote {len(rows)} documents to {OUT}')

if __name__ == '__main__':
    main()

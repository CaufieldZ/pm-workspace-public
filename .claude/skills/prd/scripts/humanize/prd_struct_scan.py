"""PRD 文档结构扫描：章节完整性（与上一版比对）+ 渲染卫生。

拦两类「写坏但内容扫描全绿」的坏法：
  ① 文档被脚本写残（整段章节丢失）——按与上一版的章节数比对判定，行数缩水逾两成另行提醒
  ② 渲染卫生——标题前缺空行（紧跟 HTML 块会被吞进块内、不再当标题渲染）、表格单元格内空行
     （Confluence 截断 HTML 块 → 表格花屏）

调用方：check_prd_md.sh 的「1.7 文档结构」维（bash heredoc 内 import）。
"""
import re
import subprocess
from pathlib import Path

_FENCE_RE = re.compile(r'^\s*```')
_HEADING_RE = re.compile(r'^#{1,5} ')
_CHAPTER_RE = re.compile(r'^# ', re.M)
_ROW_SPAN_RE = re.compile(r'<td>.*?</td>', re.S)


def count_chapters(text):
    """顶级章节数（`# ` 行）。"""
    return len(_CHAPTER_RE.findall(text))


def scan_hygiene(text):
    """渲染卫生两类：标题前缺空行 / <td> 内空行。返回问题清单。"""
    problems = []
    lines = text.splitlines(keepends=True)
    # 标题前缺空行（代码块内跳过）
    fence = False
    for i, line in enumerate(lines, 1):
        if _FENCE_RE.match(line):
            fence = not fence
            continue
        if fence:
            continue
        if _HEADING_RE.match(line) and i > 1 and lines[i - 2].strip() != '':
            problems.append(f'L{i}：标题前缺空行（紧跟 HTML 块会被吞掉、不再当标题渲染）')
    # <td> 内空行（按字符偏移定位，不跳代码块：代码块里落进单元格同样会被截断）
    spans = [(m.start(), m.end()) for m in _ROW_SPAN_RE.finditer(text)]
    pos = 0
    for i, line in enumerate(lines, 1):
        if line.strip() == '' and any(s <= pos < e for s, e in spans):
            problems.append(f'L{i}：表格单元格（<td>）内空行（渲染时截断 HTML 块→花屏）')
        pos += len(line)
    return problems


def compare_prev(text, prev_text):
    """与上一版文本比对。返回 (problems, warns)。不做固定章号 / 标题匹配：
    各产品线 delta 的章号体系不同（如某线 §7 是排期），固定章号会误判。"""
    problems, warns = [], []
    if not prev_text:
        return problems, warns
    now_ch, head_ch = count_chapters(text), count_chapters(prev_text)
    if now_ch < head_ch:
        problems.append(
            f'章节数 {now_ch} 少于上一版的 {head_ch}（文档可能被脚本写残，'
            '与上一版比对恢复；确属有意删章则提交后自然消警）')
    elif len(text.splitlines()) < len(prev_text.splitlines()) * 0.8:
        warns.append(
            f'行数 {len(text.splitlines())} 较上一版的 {len(prev_text.splitlines())} 缩水逾两成，核对是否漏段')
    return problems, warns


def previous_version(repo_root, prd_path):
    """取该文件在 git HEAD 的版本；不在仓库内 / 无 HEAD 版本 / git 不可用时返回 None。"""
    try:
        rel = Path(prd_path).resolve().relative_to(Path(repo_root).resolve()).as_posix()
        r = subprocess.run(['git', '-C', str(repo_root), 'show', f'HEAD:{rel}'],
                           capture_output=True, text=True, timeout=15)
        return r.stdout if r.returncode == 0 and r.stdout else None
    except (ValueError, subprocess.SubprocessError, OSError):
        return None


def scan_structure(text, prev_text=None):
    """返回 (problems, warns)：渲染卫生恒查，章节完整性有上一版才查。"""
    problems = scan_hygiene(text)
    p2, warns = compare_prev(text, prev_text)
    return problems + p2, warns

#!/usr/bin/env python3
"""launch-* 宣发 md → Platform C Square(WordPress)草稿/发布.

用法:
  python3 wp_publish.py <launch-*-wp.md>... [--publish] [--dry-run]
      单发一个,或多文件批量(三语组:wp_publish.py launch-x-wp-zh.md launch-x-wp-en.md launch-x-wp-ru.md,
      或直接 shell 通配 launch-x-wp-*.md);批量时每篇间隔 8s,429 节流自动等 45s 重试一次
  python3 wp_publish.py <content.md> [--title 标题] [--category 分类名]... [--tags a,b]
                        [--lang zh|en|ru|ur] [--cover 图.png] [--publish] [--dry-run]
  python3 wp_publish.py --delete <post_id>

-wp.md 带 frontmatter(title / lang / category / tags / cover / excerpt),发布元信息以
frontmatter 为准,命令行同名参数仅作覆盖;无 frontmatter 的裸 md 也可用 CLI 参数发。

链路:md → Gutenberg 块标记 → POST /wp/v2/posts。默认 status=draft(合规审校先行),
--publish 才直接发布。凭据读 .env(WP_SITE / WP_USER / WP_APP_PASSWORD),代理按
scripts/proxy_env.sh 判定(square.example.com 直连不通,走 Clash 7897)。站内匿名 REST
全关,所有请求带 Basic 鉴权。站点画像(语言/分类/块结构)见 references/wp-square-api.md。
"""
import argparse
import base64
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import markdown as md_lib

REPO_ROOT = Path(__file__).resolve().parents[4]

MIME = {
    'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
    'gif': 'image/gif', 'webp': 'image/webp', 'svg': 'image/svg+xml',
}

# 站内正式文风 9/9 零 emoji(含 ✅🚀),检出即告警
EMOJI = re.compile(r'[\U0001F000-\U0001FAFF☀-➿⬀-⯿️]')


def parse_frontmatter(text):
    """解析 --- 包裹的简单 key: value 头;返回 (meta, 正文)。

    仅当首行 --- 有成对闭合且块内解析出非空 meta 才视为 frontmatter,
    否则原样返回——防裸 md 以 --- 分隔线开头时误吞两线之间的正文。"""
    if not text.startswith('---'):
        return {}, text
    parts = text.split('\n---', 1)
    if len(parts) != 2:
        return {}, text
    meta = {}
    for line in parts[0][3:].splitlines():
        line = line.strip()
        if not line or line.startswith('#') or ':' not in line:
            continue
        k, v = line.split(':', 1)
        meta[k.strip()] = v.strip().strip('"').strip("'")
    if not meta:
        return {}, text
    return meta, parts[1].lstrip('\n')


def die(msg):
    print(f'✗ {msg}', file=sys.stderr)
    sys.exit(1)


def load_env():
    """凭据优先级:进程环境变量 > .env 文件。"""
    creds = {}
    env_file = REPO_ROOT / '.env'
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            creds[k.strip()] = v.strip().strip('"').strip("'")
    def get(key):
        return os.environ.get(key) or creds.get(key)
    site, user, pw = get('WP_SITE'), get('WP_USER'), get('WP_APP_PASSWORD')
    if not (site and user and pw):
        die('缺凭据:.env 需配 WP_SITE / WP_USER / WP_APP_PASSWORD(应用密码值含空格,必须加双引号)')
    return site.rstrip('/'), user, pw


def build_opener():
    """代理按 scripts/proxy_env.sh 判定;direct 模式则显式清空代理。"""
    proxy = None
    try:
        out = subprocess.run(
            ['bash', str(REPO_ROOT / 'scripts' / 'proxy_env.sh'), '--print'],
            capture_output=True, text=True, timeout=30,
        ).stdout
        m = re.search(r'proxy=(\S+)', out)
        if m and m.group(1) not in ('', '-'):
            proxy = m.group(1)
    except Exception:
        proxy = None
    proxies = {'http': proxy, 'https': proxy} if proxy else {}
    return urllib.request.build_opener(urllib.request.ProxyHandler(proxies))


def req(opener, site, auth, method, path, body=None, raw=False, extra_headers=None):
    """全站匿名 REST 已关,一律带 Basic 鉴权。返回 (status, json_or_{})。429 自动重试一次。"""
    headers = {'Authorization': 'Basic ' + auth, 'User-Agent': 'pm-workspace/promo-kit'}
    data = None
    if body is not None:
        if raw:
            data = body
        else:
            data = json.dumps(body).encode()
            headers['Content-Type'] = 'application/json; charset=utf-8'
    headers.update(extra_headers or {})
    r = urllib.request.Request(f'{site}/wp-json{path}', data=data, method=method, headers=headers)
    for attempt in (1, 2):
        try:
            with opener.open(r, timeout=40) as resp:
                return resp.status, json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            raw_body = e.read().decode(errors='replace')
            if e.code == 429 and attempt == 1:
                print('⏳ HTTP 429(WordPress.com 节流),45s 后自动重试…')
                time.sleep(45)
                continue
            try:
                return e.code, json.loads(raw_body)
            except Exception:
                return e.code, {}
        except urllib.error.URLError as e:
            die(f'网络不通({e.reason})。排查:1) 沙箱内先禁沙箱重试 2) Clash 7897 是否在线 — 见 runbooks/proxy-fallback.md')


def make_auth(user, pw):
    return base64.b64encode(f'{user}:{pw}'.encode()).decode()


def upload_media(opener, site, auth, path, alt=''):
    p = Path(path)
    if not p.exists():
        die(f'图片不存在:{path}')
    ext = p.suffix.lower().lstrip('.') or 'png'
    st, data = req(
        opener, site, auth, 'POST', '/wp/v2/media', body=p.read_bytes(), raw=True,
        extra_headers={
            'Content-Type': MIME.get(ext, 'application/octet-stream'),
            'Content-Disposition': f'attachment; filename="{p.name}"',
        },
    )
    if st != 201:
        die(f'图片上传失败 {p.name}:HTTP {st} {data.get("message", "")}')
    if alt:
        req(opener, site, auth, 'POST', f'/wp/v2/media/{data["id"]}', body={'alt_text': alt})
    return data['id'], data['source_url']


def inline_local_images(opener, site, auth, text, dry):
    """把 md 里指向本地文件的 ![](path) 先传媒体库再替换为远端 URL。"""
    def repl(m):
        alt, src = m.group(1), m.group(2)
        if re.match(r'^https?://', src) or not (Path(src).exists() or (Path.cwd() / src).exists()):
            return m.group(0)
        local = src if Path(src).exists() else str(Path.cwd() / src)
        if dry:
            return m.group(0)
        _, url = upload_media(opener, site, auth, local, alt)
        return f'![{alt}]({url})'
    return re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', repl, text)


def md_to_blocks(text):
    """python-markdown 转 HTML 后按顶层元素包 Gutenberg 块标记。"""
    html_text = md_lib.markdown(text, extensions=['tables', 'fenced_code'])
    parts = re.split(
        r'(?=<h[1-6][ >]|<p>|<ul[ >]|<ol[ >]|<table[ >]|<blockquote[ >]|<hr|<figure[ >]|<pre[ >])',
        html_text,
    )
    blocks = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        m = re.match(r'<(h[1-6]|p|ul|ol|table|blockquote|figure|pre|hr)\b', part)
        tag = m.group(1) if m else None
        img = re.match(r'^<p>(<img[^>]*/?>)</p>$', part)
        if img:
            blocks.append(f'<!-- wp:image -->\n<figure class="wp-block-image">{img.group(1)}</figure>\n<!-- /wp:image -->')
        elif tag == 'p':
            blocks.append(f'<!-- wp:paragraph -->\n{part}\n<!-- /wp:paragraph -->')
        elif tag and tag.startswith('h'):
            blocks.append(f'<!-- wp:heading {{"level":{tag[1]}}} -->\n{part}\n<!-- /wp:heading -->')
        elif tag in ('ul', 'ol'):
            blocks.append(f'<!-- wp:list -->\n{part}\n<!-- /wp:list -->')
        elif tag == 'hr':
            blocks.append('<!-- wp:separator -->\n<hr class="wp-block-separator"/>\n<!-- /wp:separator -->')
        elif tag == 'figure':
            blocks.append(f'<!-- wp:image -->\n{part}\n<!-- /wp:image -->')
        else:
            blocks.append(f'<!-- wp:html -->\n{part}\n<!-- /wp:html -->')
    return '\n\n'.join(blocks)


def resolve_terms(opener, site, auth, taxonomy, names, create_missing=False):
    """按名精确解析 term ID。分类不自建(站点是三语分类体系,防脏);标签缺失可自建。"""
    ids = []
    for name in names:
        q = urllib.parse.quote(name)
        st, items = req(opener, site, auth, 'GET', f'/wp/v2/{taxonomy}?search={q}&per_page=100')
        # WP 可能存 HTML 实体名(如 Deposits &amp; Withdrawals),比较前先还原
        hit = next((t for t in items if html.unescape(t.get('name', '')) == name), None) if isinstance(items, list) else None
        if not hit and create_missing:
            st, hit = req(opener, site, auth, 'POST', f'/wp/v2/{taxonomy}', body={'name': name})
            if st not in (200, 201) or not hit:
                die(f'标签创建失败:{name}(HTTP {st})')
        if not hit:
            die(f'{taxonomy} 不存在:「{name}」。不自建 — 请用站内已有名称(三语分类体系,如 产品更新 / Product Updates / -ru 系列)')
        ids.append(hit['id'])
    return ids


def publish_file(md_file, args):
    """发布单个 md 文件,返回创建的 post JSON;失败 die()(批量层捕获继续下一篇)。"""
    src = Path(md_file)
    if not src.exists():
        die(f'文件不存在:{src}')

    fm, text = parse_frontmatter(src.read_text(encoding="utf-8"))
    title = args.title or fm.get('title')
    if not title:
        m = re.search(r'(?m)^#\s+(.+)$', text)
        if m:
            title = m.group(1).strip()
            text = text.replace(m.group(0), '', 1)  # 标题已入 title 字段,正文不重复
        else:
            title = src.stem
    if len(title) > 80:
        print(f'⚠ 标题 {len(title)} 字,超常见展示阈值 80,建议人工确认')

    lang = args.lang or fm.get('lang')
    categories = args.category or [c.strip() for c in fm.get('category', '').split(',') if c.strip()]
    tags = [t.strip() for t in (args.tags or fm.get('tags', '')).split(',') if t.strip()]
    cover = args.cover or fm.get('cover')
    excerpt = fm.get('excerpt')
    if cover and not re.match(r'^https?://', cover):
        # 正文首行若就是头图引用则剔除,避免与 hero 块重复
        text = re.sub(r'(?m)^\s*!\[[^\]]*\]\(' + re.escape(cover) + r'\)\s*\n+', '', text, count=1)

    opener = None
    if not args.dry_run:
        site, user, pw = load_env()
        opener = build_opener()
        auth = make_auth(user, pw)
        text = inline_local_images(opener, site, auth, text, dry=False)

    content = md_to_blocks(text)
    cover_id = None
    if cover:
        if args.dry_run:
            print(f'[dry-run] 头图(未上传):{cover}')
        else:
            cover_id, cover_url = upload_media(opener, site, auth, cover, alt=title)
            hero = (f'<!-- wp:image {{"id":{cover_id},"sizeSlug":"large","linkDestination":"none"}} -->\n'
                    f'<figure class="wp-block-image size-large"><img src="{cover_url}"/></figure>\n'
                    f'<!-- /wp:image -->')
            content = hero + '\n\n' + content

    status = 'publish' if args.publish else 'draft'
    emojis = set(EMOJI.findall(title)) | set(EMOJI.findall(content))
    if emojis:
        print(f'⚠ 检出 emoji {"".join(sorted(emojis))} — 站内正式文风零 emoji,建议移除(不拦截)')
    print(f'── 转换完成:{title}')
    print(f'   正文 {len(content)} 字符,Gutenberg 块 {content.count("<!-- wp:")} 处,'
          f'status={status},lang={lang or "(站点默认 en,非英文分类会被重映射!)"}')

    if args.dry_run:
        print('── content 预览(前 600 字符)')
        print(content[:600])
        return {'id': '(dry-run)', 'link': ''}

    payload = {'title': title, 'content': content, 'status': status}
    if excerpt:
        payload['excerpt'] = excerpt
    if categories:
        payload['categories'] = resolve_terms(opener, site, auth, 'categories', categories)
    if tags:
        payload['tags'] = resolve_terms(opener, site, auth, 'tags', tags, create_missing=True)
    if cover_id:
        payload['featured_media'] = cover_id

    # lang 走 query 参数:Polylang 据此定帖语言,否则 term 被按站点默认语(en)重映射
    create_path = f'/wp/v2/posts?lang={lang}' if lang else '/wp/v2/posts'
    st, data = req(opener, site, auth, 'POST', create_path, body=payload)
    if st != 201:
        die(f'发布失败:HTTP {st} {data.get("message", "")}')
    print(f'✅ {"已发布" if args.publish else "草稿已建"} #{data["id"]}')
    print(f'   编辑:{site}/wp-admin/post.php?post={data["id"]}&action=edit')
    print(f'   前台:{data.get("link", "")}{"(草稿需登录预览)" if not args.publish else ""}')
    print(f'   分类:{payload.get("categories") or "无"} | 标签:{tags or "无"} | '
          f'头图:{"#" + str(cover_id) if cover_id else "无"} | lang:{lang or "默认(en)"}')
    return data


def main():
    ap = argparse.ArgumentParser(description='launch-* 宣发 md → Platform C Square(WordPress)发布')
    ap.add_argument('md_files', nargs='*', metavar='md_file',
                    help='待发布的 .md 文件;三语组可一次传多个或用通配 launch-x-wp-*.md')
    ap.add_argument('--title', help='文章标题;缺省取 md 首个 # 一级标题')
    ap.add_argument('--category', action='append', default=[], metavar='名', help='分类名,可重复;按站内已有名称精确匹配')
    ap.add_argument('--tags', default='', help='标签,逗号分隔;缺失时自动创建')
    ap.add_argument('--cover', help='头图路径:上传后设 featured_media 并按站内风格在正文顶部插图')
    ap.add_argument('--lang', help='Polylang 语言 slug(zh/en/ru/ur)。必须给:不带则站点按默认语 en 落库,'
                                   '中文/俄文分类会被服务端重映射成英文')
    ap.add_argument('--publish', action='store_true', help='直接发布;缺省建草稿(合规审校先行)')
    ap.add_argument('--dry-run', action='store_true', help='只打印转换结果与 payload,不联网')
    ap.add_argument('--delete', type=int, metavar='POST_ID', help='把指定文章移入回收站')
    args = ap.parse_args()

    if args.delete:
        site, user, pw = load_env()
        st, data = req(build_opener(), site, make_auth(user, pw), 'DELETE', f'/wp/v2/posts/{args.delete}')
        if st not in (200, 201):
            die(f'删除失败 #{args.delete}:HTTP {st} {data.get("message", "")}')
        print(f'✅ #{args.delete} 已移入回收站(30 天内 wp-admin 可恢复)')
        return

    if not args.md_files:
        die('缺 md 文件参数;用法见 wp_publish.py --help')

    results, failures = [], 0
    for i, md_file in enumerate(args.md_files):
        if i:
            time.sleep(8)  # WordPress.com 连续建帖节流,篇间留间隔
        try:
            results.append(publish_file(md_file, args))
        except SystemExit:
            failures += 1
            results.append(None)
    if len(args.md_files) > 1:
        print('\n══ 批量汇总 ══')
        for md_file, r in zip(args.md_files, results, strict=True):
            mark = f"✅ #{r['id']} {r.get('link', '')}" if r else '✗ 失败(见上)'
            print(f'  {mark} ← {Path(md_file).name}')
    if failures:
        sys.exit(1)


if __name__ == '__main__':
    main()

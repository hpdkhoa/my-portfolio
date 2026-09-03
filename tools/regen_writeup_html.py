#!/usr/bin/env python3
"""
regen_writeup_html.py: rebuild the styled .html twins of the writeups from their .md sources.

Run this AFTER tools/fill_portfolio.py, so the twins carry the injected measured tables.
index.html links to the .html twins, so they must exist and must match the markdown.

Stdlib only. It keeps each twin's existing <head>, styles, nav, and page script untouched and
replaces only the <article class="doc" id="doc"> body and the <title>. The page script rebuilds
its table of contents from the new headings.

Covers the markdown the writeups use: ATX headings, paragraphs, blockquotes, bold, italic,
inline code, links, tables, ordered and unordered lists, horizontal rules, fenced code blocks,
and raw HTML comment lines (the <!--measured:...--> markers pass through untouched).

Usage:  python3 tools/regen_writeup_html.py          (from anywhere; root inferred from this file)
"""
import io, re, html as H, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTICLE_OPEN = '<article class="doc" id="doc">'

def slug(t):
    t = re.sub(r'<[^>]+>', '', t)
    t = re.sub(r'[^\w\s-]', '', t.lower())
    return re.sub(r'[\s_]+', '-', t).strip('-')

def inline(t):
    t = H.escape(t, quote=False)
    t = re.sub(r'`([^`]+)`', lambda m: '<code>' + m.group(1) + '</code>', t)
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', t)
    return t

def convert(md):
    out, lines, i, para = [], md.split('\n'), 0, []
    def flush():
        if para:
            out.append('<p>' + inline(' '.join(x.strip() for x in para)) + '</p>')
            para.clear()
    while i < len(lines):
        ln = lines[i]; s = ln.strip()
        if s.startswith('```'):
            flush(); code = []; i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code.append(lines[i]); i += 1
            out.append('<pre><code>' + H.escape('\n'.join(code)) + '</code></pre>'); i += 1; continue
        if s.startswith('<!--'):
            flush(); out.append(s); i += 1; continue
        if not s:
            flush(); i += 1; continue
        if re.fullmatch(r'-{3,}', s):
            flush(); out.append('<hr>'); i += 1; continue
        m = re.match(r'^(#{1,6})\s+(.*)$', s)
        if m:
            flush(); lvl, txt = len(m.group(1)), m.group(2)
            out.append(f'<h{lvl} id="{slug(txt)}">{inline(txt)}</h{lvl}>'); i += 1; continue
        if s.startswith('>'):
            flush(); q = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                q.append(lines[i].strip()[1:].strip()); i += 1
            out.append('<blockquote>' + convert('\n'.join(q)) + '</blockquote>'); continue
        if s.startswith('|') and i + 1 < len(lines) and re.fullmatch(r'\|[\s|:-]*\|?', lines[i + 1].strip()):
            flush()
            hdr = [c.strip() for c in s.strip('|').split('|')]
            rows, i = [], i + 2
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i += 1
            t = ['<table>', '<thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in hdr) + '</tr></thead>', '<tbody>']
            for r in rows:
                t.append('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>')
            t += ['</tbody>', '</table>']; out.append('\n'.join(t)); continue
        m = re.match(r'^(\s*)([-*]|\d+\.)\s+(.*)$', ln)
        if m:
            flush(); ordered = m.group(2)[0].isdigit(); items = []
            while i < len(lines):
                mm = re.match(r'^(\s*)([-*]|\d+\.)\s+(.*)$', lines[i])
                if mm and (mm.group(2)[0].isdigit() == ordered):
                    items.append(mm.group(3)); i += 1
                    while i < len(lines) and lines[i].strip() and lines[i].startswith(' ') \
                            and not re.match(r'^\s*([-*]|\d+\.)\s+', lines[i]):
                        items[-1] += ' ' + lines[i].strip(); i += 1
                else:
                    break
            tag = 'ol' if ordered else 'ul'
            out.append(f'<{tag}>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + f'</{tag}>'); continue
        para.append(ln); i += 1
    flush()
    return '\n'.join(out)

def main():
    done = 0
    for md_path in sorted((ROOT / 'writeups').glob('*.md')):
        if md_path.name == 'README.md':
            continue
        html_path = md_path.with_suffix('.html')
        if not html_path.exists():
            print(f'  skip {md_path.name}: no .html twin to update')
            continue
        md = io.open(md_path, encoding='utf-8').read()
        s = io.open(html_path, encoding='utf-8').read()
        a = s.find(ARTICLE_OPEN); b = s.find('</article>')
        if a < 0 or b < a:
            print(f'  !! {html_path.name}: article slot not found, left untouched'); continue
        a += len(ARTICLE_OPEN)
        s = s[:a] + '\n' + convert(md) + '\n' + s[b:]
        m = re.search(r'^#\s+(.+)$', md, re.M)
        if m:
            s = re.sub(r'<title>.*?</title>', '<title>' + H.escape(m.group(1), quote=False) + '</title>',
                       s, count=1, flags=re.S)
        io.open(html_path, 'w', encoding='utf-8', newline='\n').write(s)
        print(f'  regenerated {html_path.name}')
        done += 1
    print(f'{done} twin(s) regenerated')
    return 0

if __name__ == '__main__':
    sys.exit(main())

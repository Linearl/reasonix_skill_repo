# -*- coding: utf-8 -*-
"""OneNote GetPageContent XML -> Markdown（含图片提取）。
用法: python parse_onenote_xml.py <export_dir> [输出md目录]
图片: piBinaryData 模式导出的 <one:Data> base64 -> md/img/NNNN_k.ext，md 相对引用。
"""
import base64
import io
import os
import re
import sys
import html
import xml.etree.ElementTree as ET

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

NS = 'http://schemas.microsoft.com/office/onenote/2013/onenote'
SPAN_OR_HTML = re.compile(r'<[^>]+>')

MAGIC = {
    b'\x89PNG': '.png', b'\xff\xd8\xff': '.jpg', b'GIF8': '.gif',
    b'BM': '.bmp', b'\x49I\x2a\x00': '.tif', b'\x4d\x4d\x00\x2a': '.tif',
    b'RIFF': '.webp',
}


def sniff_ext(data):
    for magic, ext in MAGIC.items():
        if data.startswith(magic):
            return ext
    return '.bin'


def strip_html(text):
    text = SPAN_OR_HTML.sub('', text or '')
    text = text.replace('&#xA;', '\n').replace('&#x202F;', ' ').replace('&nbsp;', ' ')
    return html.unescape(text)


def extract_oe_text(oe):
    parts = [t.text or '' for t in oe.findall('{%s}T' % NS)]
    has_img = oe.find('{%s}Image' % NS) is not None
    indicator = None
    tag = oe.find('{%s}Tag' % NS)
    if tag is not None:
        indicator = tag.get('indicator')
    return strip_html(''.join(parts)), has_img, indicator


def save_images(oe, img_dir, counter):
    """提取 OE 内所有 Image 的 base64 数据，返回 [(相对路径, alt)]"""
    out = []
    for img in oe.iter('{%s}Image' % NS):
        data_el = img.find('{%s}Data' % NS)
        if data_el is None or not data_el.text:
            continue
        try:
            raw = base64.b64decode(data_el.text)
        except Exception:
            continue
        if not raw:
            continue
        counter[0] += 1
        ext = sniff_ext(raw)
        fname = '%s_%d%s' % (os.path.basename(img_dir.rstrip('/')), counter[0], ext)
        with open(os.path.join(img_dir, fname), 'wb') as f:
            f.write(raw)
        out.append((fname, img.get('alt') or '图片'))
    return out


def oe_to_lines(oe, level=0, img_dir=None, counter=None):
    lines = []
    text, has_img, indicator = extract_oe_text(oe)
    indent = '  ' * level
    imgs = save_images(oe, img_dir, counter) if (img_dir and counter) else []
    if has_img and not text.strip() and imgs:
        for fname, alt in imgs:
            lines.append('%s![%s](img/%s)' % (indent, alt, fname))
    elif text.strip():
        for seg in text.split('\n'):
            seg = seg.rstrip()
            if not seg:
                continue
            if indicator is not None and indicator.isdigit() and 1 <= int(indicator) <= 18:
                checked = 'x' if int(indicator) >= 10 else ' '
                lines.append('%s- [%s] %s' % (indent, checked, seg))
            else:
                lines.append(indent + seg)
        for fname, alt in imgs:
            lines.append('%s![%s](img/%s)' % (indent, alt, fname))
    for child in oe.findall('{%s}OEChildren' % NS):
        for sub in child.findall('{%s}OE' % NS):
            lines.extend(oe_to_lines(sub, level + 1, img_dir, counter))
    return lines


def page_to_md(xml_text, page_name, img_dir=None, counter=None):
    root = ET.fromstring(xml_text)
    lines = []
    title = root.find('{%s}Title' % NS)
    title_text = ''
    if title is not None:
        t, _, _ = extract_oe_text(title)
        title_text = t.strip()
    if not title_text:
        title_text = page_name or '未命名页面'
    lines.append('# %s\n' % title_text)

    for outline in root.iter('{%s}Outline' % NS):
        for oec in outline.findall('{%s}OEChildren' % NS):
            for oe in oec.findall('{%s}OE' % NS):
                lines.extend(oe_to_lines(oe, img_dir=img_dir, counter=counter))
        lines.append('')
    return '\n'.join(lines)


def main():
    export_dir = sys.argv[1] if len(sys.argv) > 1 else r'<local-home>\AppData\Roaming\reasonix\global-workspace\onenote_export'
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(export_dir, 'md')
    os.makedirs(out_dir, exist_ok=True)
    img_dir = os.path.join(out_dir, 'img')
    os.makedirs(img_dir, exist_ok=True)
    pages_dir = os.path.join(export_dir, 'pages')
    index_path = os.path.join(export_dir, 'index.tsv')
    if not os.path.exists(index_path):
        print('index.tsv 不存在，导出未完成？')
        return
    entries = []
    for raw_line in open(index_path, encoding='utf-8'):
        line = raw_line.lstrip('\ufeff').rstrip('\n')
        if '\tERROR' in line:
            entries.append((line.split('\t')[0], None, line.split('\t')[2], True))
            continue
        parts = line.split('\t')
        if len(parts) >= 3:
            entries.append((parts[0], parts[1], parts[2], False))
    ok = 0
    img_counter = [0]
    for num, page_id, name, err in entries:
        if err:
            print('跳过(导出失败): %s %s' % (num, name))
            continue
        xml_path = os.path.join(pages_dir, num + '.xml')
        if not os.path.exists(xml_path):
            continue
        xml_text = open(xml_path, encoding='utf-8-sig').read()
        try:
            md = page_to_md(xml_text, name, img_dir, img_counter)
        except Exception as e:
            print('解析失败 %s (%s): %s' % (num, name, e))
            continue
        safe = re.sub(r'[\\/:*?"<>|\r\n]+', '_', name or num)
        safe = safe.strip().strip('.')[:80] or num
        with open(os.path.join(out_dir, '%s_%s.md' % (num, safe)), 'w', encoding='utf-8') as f:
            f.write(md)
        ok += 1
    print('完成: %d/%d 页转 md, 图片 %d 张' % (ok, len(entries), img_counter[0]))


if __name__ == '__main__':
    main()

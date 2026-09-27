"""Parse the sector deep-dive Markdown files into a category/process tree.

Each file uses: ## category, optional ### group, and ###/#### process headings.
A process heading is followed by a description line, a ```mermaid block and a
*Pain point: ...* line. A trailing *(Tag)* on a heading marks a cross-sector overlap.
"""
import re

HEADER_RE = re.compile(r'^(#{1,4})\s+(.*)$')
TAG_RE = re.compile(r'^(.*?)\s*\*\(([^)]+)\)\*\s*$')

def parse_title_tag(raw):
    m = TAG_RE.match(raw.strip())
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return raw.strip(), None

def parse_leaf_content(content):
    m = re.search(r'```mermaid\s*\n(.*?)```', content, re.S)
    if not m:
        desc = content.strip()
        return desc, None, None
    desc = content[:m.start()].strip()
    mermaid = m.group(1).strip()
    after = content[m.end():].strip()
    pain = after.strip().strip('*').strip()
    pain = re.sub(r'^Pain point:\s*', '', pain, flags=re.I)
    return desc, mermaid, pain

def parse_file(path):
    with open(path, encoding='utf-8') as f:
        text = f.read()
    lines = text.split('\n')
    # find header line indices
    headers = []  # (level, title, tag, line_start_char_idx, header_line_text_len)
    char_pos = 0
    positions = []
    running = 0
    for line in lines:
        m = HEADER_RE.match(line)
        if m:
            level = len(m.group(1))
            raw_title = m.group(2)
            title, tag = parse_title_tag(raw_title)
            positions.append({
                'level': level,
                'title': title,
                'tag': tag,
                'line_char_start': running,
                'line_len': len(line) + 1,  # +1 for newline
            })
        running += len(line) + 1

    # doc title = first level-1 header
    doc_title = None
    for p in positions:
        if p['level'] == 1:
            doc_title = p['title']
            break

    # build content slices: for each header (except H1), content = text between end of its line and start of next header (any level)
    n = len(positions)
    for i, p in enumerate(positions):
        start = p['line_char_start'] + p['line_len']
        end = positions[i+1]['line_char_start'] if i+1 < n else len(text)
        p['content'] = text[start:end]

    # Now build tree: iterate positions (excluding H1), track current H2, current H3(if group)
    categories = []  # list of {name, children: [...]}
    current_cat = None
    current_group = None  # dict when H3 is a group (has H4 children)

    for p in positions:
        if p['level'] == 1:
            continue
        content_stripped = p['content'].strip()
        is_leaf = '```mermaid' in p['content']
        if p['level'] == 2:
            current_cat = {'name': p['title'], 'tag': p['tag'], 'children': []}
            categories.append(current_cat)
            current_group = None
        elif p['level'] == 3:
            if is_leaf:
                desc, mermaid, pain = parse_leaf_content(p['content'])
                current_cat['children'].append({
                    'kind': 'leaf', 'name': p['title'], 'tag': p['tag'],
                    'desc': desc, 'mermaid': mermaid, 'pain': pain
                })
                current_group = None
            else:
                current_group = {'kind': 'group', 'name': p['title'], 'tag': p['tag'], 'children': []}
                current_cat['children'].append(current_group)
        elif p['level'] == 4:
            desc, mermaid, pain = parse_leaf_content(p['content'])
            leaf = {
                'kind': 'leaf', 'name': p['title'], 'tag': p['tag'],
                'desc': desc, 'mermaid': mermaid, 'pain': pain
            }
            if current_group is not None:
                current_group['children'].append(leaf)
            else:
                current_cat['children'].append(leaf)

    return doc_title, categories

def count_leaves(children):
    total = 0
    for c in children:
        if c['kind'] == 'leaf':
            total += 1
        else:
            total += count_leaves(c['children'])
    return total

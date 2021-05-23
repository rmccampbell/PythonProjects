#!/usr/bin/env python3
import sys, re, bs4, argparse, urllib.request

def _parse_columns(columns):
    if isinstance(columns, (list, tuple, range)):
        return columns
    if isinstance(columns, int):
        return [columns]
    column_list = []
    for s in columns.split(','):
        if '-' in s:
            start, stop = map(int, s.split('-', 1))
            column_list.extend(range(start, stop+1))
        else:
            column_list.append(int(s))
    return column_list

def parse_table(html='-', selector=None, number=None, columns=None,
                startrow=None, endrow=None, tbody=False, duplicate_cells=False,
                parser=None):
    if html == '-':
        html = sys.stdin
    elif re.match(r'\s*<', html):
        pass
    elif re.match(r'\w{2,}://', html):
        html = urllib.request.urlopen(html)
    else:
        html = open(html)
    if parser is None:
        for parser in ['lxml', 'html5lib', 'html.parser']:
            if bs4.builder_registry.lookup(parser):
                break
    doc = bs4.BeautifulSoup(html, parser)

    if selector:
        table = doc.select_one(selector)
        if not table:
            raise ValueError("selector '{}' not found.".format(selector))
        if table.name != 'table':
            table = table.table or table
    elif number is not None:
        table = doc.find_all('table', limit=number+1)[number]
    else:
        table = doc.table or doc.body or doc

    if tbody:
        table = table.tbody or table
    else:
        for tname in 'thead', 'tbody', 'tfoot':
            tag = table.find(tname)
            if tag:
                tag.unwrap()

    columns = columns and _parse_columns(columns)

    results = []
    for tr in table.find_all('tr', recursive=False)[startrow : endrow]:
        cells = []
        for td in tr.find_all(('td', 'th'), recursive=False):
            text = re.sub(r'[^\S\xa0]+', ' ', td.text).replace('\xa0', ' ')
            cells.append(text)
            if td.has_attr('colspan'):
                repeat = int(td['colspan']) - 1
                cells.extend([text if duplicate_cells else ''] * repeat)
        if columns:
            cells = [cells[col] for col in columns if col < len(cells)]
        results.append(cells)
    return results

def print_delimited(arr, delimiter='\t'):
    enc = sys.stdout.encoding
    for row in arr:
        print(delimiter.join(row).encode(enc, 'replace').decode(enc))

def pretty_print(arr, pad=2):
    widths = [max((len(r[i]) for r in arr if i < len(r)), default=0)
              for i in range(max(map(len, arr), default=0))]
    enc = sys.stdout.encoding
    for r in arr:
        l = (' '*pad).join(s.ljust(widths[i]) for i, s in enumerate(r))
        print(l.encode(enc, 'replace').decode(enc))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('html', nargs='?', default='-')
    parser.add_argument('-S', '--selector')
    parser.add_argument('-n', '--number', type=int)
    parser.add_argument('-c', '--columns', type=_parse_columns)
    parser.add_argument('-s', '--startrow', type=int)
    parser.add_argument('-e', '--endrow', type=int)
    parser.add_argument('-b', '--tbody', action='store_true')
    parser.add_argument('-D', '--duplicate-cells', action='store_true')
    parser.add_argument('-d', '--delimiter')
    parser.add_argument('-t', '--tabs', dest='delimiter', const='\t',
                        action='store_const')
    parser.add_argument('-P', '--pad', type=int, default=2)
    parser.add_argument('-p', '--parser')
    kwargs = vars(parser.parse_args())
    delimiter = kwargs.pop('delimiter')
    pad = kwargs.pop('pad')
    try:
        table = parse_table(**kwargs)
    except Exception as e:
        sys.exit('{}: {}'.format(type(e).__name__, e))
    if delimiter:
        print_delimited(table, delimiter)
    else:
        pretty_print(table, pad)

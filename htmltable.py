#!/usr/bin/env python3
import sys, re, bs4, argparse, urllib.request

def parse_table(html='-', id=None, number=None, columns=None, startrow=None,
                endrow=None, tbody=False):
    if html == '-':
        html = sys.stdin
    elif re.match(r'\s*<', html):
        pass
    elif re.match(r'\w{2,}://', html):
        html = urllib.request.urlopen(html)
    else:
        html = open(html)
    doc = bs4.BeautifulSoup(html, 'html5lib')

    if id:
        table = doc.find(id=id)
        if not table:
            raise ValueError("id '{}' not found.".format(id))
        if table.name != 'table':
            table = table.table or table
    elif number is not None:
        table = doc.find_all('table')[number]
    else:
        table = doc.table or doc.body or doc
    if tbody:
        table = table.tbody or table
    else:
        for tname in 'thead', 'tbody', 'tfoot':
            tag = table.find(tname)
            tag and tag.unwrap()

    results = []
    for tr in table.find_all('tr', recursive=False)[startrow : endrow]:
        tds = tr.find_all(('td', 'th'), recursive=False)
        if columns:
            tds = [tds[col] for col in columns if col < len(tds)]
        results.append([re.sub(r'\s', ' ', td.text) for td in tds])
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
    parser.add_argument('-i', '--id')
    parser.add_argument('-n', '--number', type=int)
    parser.add_argument('-c', '--columns', type=int, nargs='+')
    parser.add_argument('-s', '--startrow', type=int)
    parser.add_argument('-e', '--endrow', type=int)
    parser.add_argument('-b', '--tbody', action='store_true')
    parser.add_argument('-d', '--delimiter')
    parser.add_argument('-t', '--tabs', dest='delimiter', const='\t',
                        action='store_const')
    kwargs = vars(parser.parse_args())
    delimiter = kwargs.pop('delimiter')
    try:
        table = parse_table(**kwargs)
    except Exception as e:
        sys.exit('{}: {}'.format(type(e).__name__, e))
    if delimiter:
        print_delimited(table, delimiter)
    else:
        pretty_print(table)

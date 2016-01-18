#!/usr/bin/env python3
import sys, bs4, argparse, urllib.request

def parse_table(html='-', id=None, number=None, columns=None, startrow=None,
                endrow=None):
    if html == '-':
        html = sys.stdin
    else:
        try:
            html = open(html)
        except OSError:
            try:
                html = urllib.request.urlopen(html)
            except (ValueError, urllib.error.URLError):
                pass
    doc = bs4.BeautifulSoup(html, 'html.parser')

    if id:
        table = doc.find(id=id)
        if not table: sys.exit("Id '{}' not found.".format(id))
    elif number is not None:
        table = doc.find_all('table')[number]
    else:
        table = doc.table or doc.body or doc
    table = table.tbody or table
    results = []
    for tr in table.find_all('tr', recursive=False)[startrow : endrow]:
        tds = tr.find_all(('td', 'th'), recursive=False)
        if columns:
            tds = [tds[col] for col in columns if col < len(tds)]
        results.append([td.get_text(' ', True) for td in tds])
    return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('html', nargs='?', default='-')
    parser.add_argument('-i', '--id')
    parser.add_argument('-n', '--number', type=int)
    parser.add_argument('-c', '--columns', type=int, nargs='+')
    parser.add_argument('-s', '--startrow', type=int)
    parser.add_argument('-e', '--endrow', type=int)
    args = parser.parse_args()
    enc = sys.stdout.encoding
    for row in parse_table(**vars(args)):
        print('\t'.join(row).encode(enc, 'replace').decode(enc))

from itertools import zip_longest

_justs = {'left': str.ljust, 'right': str.rjust, 'center': str.center}

def barplot(data, labels=None, char='x', colons=True, border=' ', just='left',
            pad=0):
    just = _justs[just]
    if labels:
        labels = list(map(str, labels))
        if colons:
            labels = [l + ':' if l else '' for l in labels]
        lw = max(map(len, labels))
        sep = (' '*lw + border + '\n')*pad
        past_first = False
        for l, x in zip_longest(labels, data, fillvalue=0):
            print(sep*past_first + just(l or '', lw) + border + char*x)
            past_first = True
    else:
        for x in data:
            print(char * x + '\n'*pad)

def vbarplot(data, labels=None, flipped=False, char='x', border='',
             just='center', pad=1):
    just = _justs[just]
    w = 1
    if labels:
        labels = list(map(str, labels))
        w = max(map(len, labels))
        header = (' '*pad).join(just(l, w) for l in labels)
        if not flipped:
            print(header)
            if border:
                print(border*len(header))
    for i in range(max(data, default=0))[::-1 if flipped else 1]:
        print((' '*pad).join(just(char if x > i else ' ', w) for x in data))
    if labels and flipped:
        if border:
            print(border*len(header))
        print(header)

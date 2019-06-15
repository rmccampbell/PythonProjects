from itertools import zip_longest

_justs = {'left': str.ljust, 'right': str.rjust, 'center': str.center}

def barplot(data, labels=None, char='x', just='left', pad=0):
    just = _justs[just]
    if labels:
        labels = list(map(str, labels))
        lw = max(map(len, labels))
        for l, x in zip_longest(labels, data, fillvalue=0):
            print(just(l + ': ' if l else '', lw + 2) + char * x + '\n'*pad)
    else:
        for x in data:
            print(char * x + '\n'*pad)

def vbarplot(data, labels=None, flipped=False, char='x', just='center', pad=1):
    just = _justs[just]
    w = 1
    if labels:
        labels = list(map(str, labels))
        w = max(map(len, labels))
        header = (' '*pad).join(just(l, w) for l in labels)
        if not flipped:
            print(header)
    for i in range(max(data, default=0))[::-1 if flipped else 1]:
        print((' '*pad).join(just(char if x > i else ' ', w) for x in data))
    if labels and flipped:
        print(header)

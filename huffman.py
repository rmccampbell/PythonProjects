#!/usr/bin/env python3
import sys, argparse, heapq

freqs = {
    ' ': 18.23,
    'A': 6.22,
    'B': 1.32,
    'C': 3.11,
    'D': 2.97,
    'E': 10.53,
    'F': 1.68,
    'G': 1.65,
    'H': 3.63,
    'I': 6.14,
    'J': 0.07,
    'K': 0.31,
    'L': 3.07,
    'M': 2.48,
    'N': 5.73,
    'O': 6.06,
    'P': 1.87,
    'Q': 0.1,
    'R': 5.87,
    'S': 5.81,
    'T': 7.68,
    'U': 2.27,
    'V': 0.7,
    'W': 1.13,
    'X': 0.25,
    'Y': 1.07,
    'Z': 0.05
}

def count_freqs(text):
    freqs = {}
    for c in text:
        freqs[c] = freqs.get(c, 0) + 1
    return freqs

def build_tree(freqs):
    heap = [(f, i, v) for i, (v, f) in enumerate(freqs.items())]
    heapq.heapify(heap)
    i = len(heap)
    while len(heap) > 1:
        freq1, _, node1 = heapq.heappop(heap)
        freq2, _, node2 = heapq.heappop(heap)
        heapq.heappush(heap, ((freq1 + freq2), i, (node1, node2)))
        i += 1
    return heap[0][2]

def make_table(tree, pre='', dct=None):
    if dct is None: dct = {}
    for i, node in enumerate(tree):
        if not isinstance(node, tuple):
            dct[node] = pre + str(i)
        else:
            make_table(node, pre + str(i), dct)
    return dct


def huffman(freqs):
    tree = build_tree(freqs)
    return make_table(tree)

tree = build_tree(freqs)
entable = make_table(tree)
detable = {v: k for k, v in entable.items()}

def encode(text, table=entable):
    return ''.join(table.get(c.upper(), '') for c in text)

def decode(msg, table=detable):
    out, nxt = '', ''
    for c in msg:
        if c.isspace():
            continue
        nxt += c
        if nxt in table:
            out += table[nxt]
            nxt = ''
    return out

def decode2(msg, tree=tree):
    out = ''
    node = tree
    for c in msg:
        if c == '0':
            node = node[0]
        elif c == '1':
            node = node[1]
        else:
            continue
        if isinstance(node, str):
            out += node
            node = tree
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--table', action='store_true')
    parser.add_argument('-e', '--encode', action='store_true', default=True,
                        help='(default)')
    parser.add_argument('-d', '--decode', action='store_true')
    parser.add_argument('file', nargs='?', type=argparse.FileType(),
                        default=sys.stdin)
    args = parser.parse_args()

    if args.table:
        for k, v in sorted(entable.items()):
            print('{}: {}'.format(k, v))
    elif args.decode:
        print(decode(args.file.read()))
    else:
        print(encode(args.file.read()))

from collections import deque

_word_list = None

def word_list(size=0):
    global _word_list
    if not _word_list:
        file = open('data\\wordlist.txt')
        _word_list = [w.strip() for w in file]
    if size:
        return [w for w in _word_list if len(w) == size]
    return _word_list

def hamming(s1, s2):
    return sum(c1 != c2 for c1, c2 in zip(s1, s2))

def word_path(start, end, words=None):
    size = len(start)
    if len(end) != size:
        raise ValueError('mismatching lengths')
    words = words or word_list()
    words = [w for w in words if len(w) == size]
    q = deque([(start,)])
    while q:
        path = q.popleft()
        w1 = path[-1]
        for w2 in match_words(w1, path, words, False):
            path2 = path + (w2,)
            if w2 == end:
                return list(path2)
            q.append(path2)

def match_words(w, exclude=(), words=None, filter=True):
    if not words:
        words = word_list()
    if filter:
        size = len(w)
        words = [w2 for w2 in words if len(w2) == size]
    for w2 in words:
        if w2 not in exclude and hamming(w, w2) == 1:
            yield w2

def all_matches(size, words=None):
    words = words or word_list()
    words = [w2 for w2 in words if len(w2) == size]
    d = {}
    s = set(lst)
    for w in lst:
        for w2 in s:
            if hamming(w, w2) == 1:
                d.setdefault(w, set()).add(w2)
                d.setdefault(w2, set()).add(w)
        s.remove(w)
    return d

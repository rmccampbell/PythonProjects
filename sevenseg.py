PATTERN = '''\
 _ 
|_|
|_|
'''
TEMPLATE = '''\
 0
561
432
'''
ZERO = '''\
 _ 
| |
|_|
'''
ONE = '''\

  |
  |
'''
TWO = '''\
 _ 
 _|
|_ 
'''
THREE = '''\
 _ 
 _|
 _|
'''
FOUR = '''\
   
|_|
  |
'''
FIVE = '''\
 _ 
|_ 
 _|
'''
SIX = '''\
 _ 
|_ 
|_|
'''
SEVEN = '''\
 _ 
  |
  |
'''
EIGHT = '''\
 _ 
|_|
|_|
'''
NINE = '''\
 _ 
|_|
 _|
'''
DIGS = [ZERO, ONE, TWO, THREE, FOUR, FIVE, SIX, SEVEN, EIGHT, NINE]

def hsplit(string, *inds):
    return list(map('\n'.join,
                    zip(*(spartition(s, *inds) for s in string.splitlines()))))

def hconcat(*strings):
    line_lists = [s.splitlines() for s in strings]
    widths = [max(map(len, lines)) for lines in line_lists]
    return '\n'.join(
        ''.join(line.ljust(w) for line, w in zip(row, widths))
        for row in zip_longest(*line_lists, fillvalue='')
    )

def decode(n):
    pass

ones = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
        'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen',
        'sixteen', 'seventeen', 'eighteen', 'nineteen']

tens = ['twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty',
        'ninety']

thousands = ['thousand', 'million', 'billion', 'trillion', 'quadrillion',
             'quintillion', 'sextillion', 'septillion', 'octillion',
             'nonillion', 'decillion', 'undecillion', 'duodecillion',
             'tredecillion', 'quattuordecillion', 'quindecillion',
             'sexdecillion', 'septendecillion', 'octodecillion',
             'novemdecillion', 'vigintillion']

thousands = ['thousand', 'million', 'billion', 'trillion', 'quadrillion',
             'quintillion', 'sextillion', 'septillion', 'octillion',
             'nonillion', 'decillion', 'undecillion', 'duodecillion',
             'tredecillion', 'quattuordecillion', 'quinquadecillion',
             'sedecillion', 'septendecillion', 'octodecillion',
             'novendecillion', 'vigintillion', 'unvigintillion',
             'duovigintillion', 'tresvigintillion', 'quattuorvigintillion',
             'quinquavigintillion', 'sesvigintillion', 'septemvigintillion',
             'octovigintillion', 'novemvigintillion', 'trigintillion',
             'untrigintillion', 'duotrigintillion', 'trestrigintillion',
             'quattuortrigintillion', 'quinquatrigintillion',
             'sestrigintillion', 'septentrigintillion', 'octotrigintillion',
             'noventrigintillion', 'quadragintillion']

ones_map = {n: i for i, n in enumerate(ones)}
tens_map = {n: i for i, n in enumerate(tens, 2)}
thousands_map = {n: i for i, n in enumerate(thousands, 1)}

def smalln2words(n):
    if n < 0 or n > 999:
        raise ValueError('n must be between 0 and 999')
    h, n = divmod(n, 100)
    s = ones[h] + ' hundred ' if h else ''
    if n < 20:
        s += ones[n] if n or not h else ''
    else:
        t, n = divmod(n, 10)
        s += tens[t-2] + ' ' if t else ''
        s += ones[n] if n else ''
    return s.strip()

def num2words(n, e=0):
    sgn = 'negative ' if n < 0 else ''
    n, r = divmod(abs(n), 1000)
    s = smalln2words(r) + (' ' + thousands[e-1] if e else '')
    if n:
        s = num2words(n, e+1) + (' ' + s if r else '')
    return sgn + s


def words2num(s):
    l = s.lower().split()
    n = 0
    last_type = ''
    last_thousand = 0
    x = 0
    try:
        return int(s.replace(',', ''))
    except ValueError:
        pass
    for w in l:
        if w in ones_map:
            if last_type == 'ones' or x % 10:
                raise ValueError('two ones in a row')
            x += ones_map[w]
            last_type = 'ones'
        elif w in tens_map:
            if last_type == 'ones' or x % 10:
                raise ValueError('tens after ones')
            if last_type == 'tens' or x % 100:
                raise ValueError('two tens in a row')
            x += tens_map[w] * 10
            last_type = 'tens'
        elif w == 'hundred':
            if last_type != 'ones' or x > 9:
                raise ValueError('"hundred" not preceded by ones')
            x *= 100
            last_type = 'hundreds'
        elif w in thousands_map:
            if last_type == 'thousands':
                raise ValueError('two thousands in a row')
            thousand = thousands_map[w]
##            if n % 1000**(thousand + 1):
            if last_thousand and thousand >= last_thousand:
                raise ValueError('thousands not in order')
            n += x * 1000**thousand
            last_type = 'thousands'
            last_thousand = thousand
            x = 0
        else:
            try:
                m = float(w)
            except ValueError:
                raise ValueError('invalid number')
            if m > 999:
                raise ValueError('numeric literal greater than 999')
            if m > 99 and last_type == 'hundreds':
                raise ValueError('two hundreds in a row')
            if m > 9 and (last_type == 'tens' or x % 100):
                raise ValueError('two tens in a row')
            if last_type == 'ones' or x % 10:
                raise ValueError('two ones in a row')
            x += m
            last_type = 'ones'
    n += x
    return int(n)

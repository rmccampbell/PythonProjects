#!/usr/bin/env python3
import random

prompts = {2: 'Binary: ', 10: 'Decimal: ', 16: 'Hex: '}
fmts = {2: '#06b', 10: 'd', 16: '#x'}

def getnum(prompt='', base=0):
    try:
        return int(input(prompt), base)
    except ValueError:
        return None

def game():
    while True:
        i = random.randrange(16)
        obase, ibase = random.sample([2, 10, 16], 2)
        print(prompts[obase] + format(i, fmts[obase]))
        j = getnum(prompts[ibase], ibase)
        while i != j:
            print("Try again")
            j = getnum(prompts[ibase], ibase)
        print("Correct!")

if __name__ == '__main__':
    try:
        game()
    except KeyboardInterrupt:
        pass

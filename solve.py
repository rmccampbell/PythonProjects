#!/usr/bin/env python3
import sys, sympy

def solve(*eqs):
    eqs = list(eqs)
    for i, eq in enumerate(eqs):
        if isinstance(eq, str) and '==' in eq:
            eqs[i] = sympy.Eq(*map(sympy.sympify, eq.split('==')))
    if len(eqs) == 1:
        return sympy.solve(eqs[0])
    return sympy.solve(eqs)

if __name__ == '__main__':
    res = solve(*sys.argv[1:])

    if isinstance(res, list):
        for expr in res:
            if isinstance(expr, dict):
                items = sorted(expr.items(), key=lambda i: i[0].name)
                for var, expr in items:
                    sympy.pprint(sympy.Eq(var, expr))
                print()
            else:
                sympy.pprint(expr)

    elif isinstance(res, dict):
        items = sorted(res.items(), key=lambda i: i[0].name)
        for var, expr in items:
            sympy.pprint(sympy.Eq(var, expr))

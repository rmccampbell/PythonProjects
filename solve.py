#!/usr/bin/env python3
import sys, sympy

def solve(*eqs):
    exprs = []
    vars = []
    for eq in eqs:
        if isinstance(eq, str) and '==' in eq:
            exprs.append(sympy.Eq(*map(sympy.sympify, eq.split('=='))))
        else:
            eq = sympy.sympify(eq)
            if isinstance(eq, sympy.Symbol):
                vars.append(eq)
            else:
                exprs.append(eq)
    if len(eqs) == 1:
        return sympy.solve(exprs[0], *vars)
    return sympy.solve(exprs, *vars)

if __name__ == '__main__':
    res = solve(*sys.argv[1:])

    if isinstance(res, list):
        for expr in res:
            if isinstance(expr, dict):
                items = sorted(expr.items(), key=lambda i: i[0].name)
                for var, expr in items:
                    sympy.pprint(sympy.Eq(var, expr))
                print()
            elif isinstance(expr, tuple):
                for expr in expr:
                    sympy.pprint(expr)
                print()
            else:
                sympy.pprint(expr)

    elif isinstance(res, dict):
        items = sorted(res.items(), key=lambda i: i[0].name)
        for var, expr in items:
            sympy.pprint(sympy.Eq(var, expr))

    else:
        sympy.pprint(res)

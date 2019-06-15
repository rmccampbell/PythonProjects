import cmath, random
import sympy

def test_equal(e1, e2, samples=100, tol=1e-8, acc=.95, positive=False):
    e1 = sympy.sympify(e1)
    e2 = sympy.sympify(e2)
    syms = e1.free_symbols | e2.free_symbols
    eq = 0
    for i in range(samples):
        subs = {}
        for s in syms:
            if positive or s.is_positive:
                subs[s] = random.lognormvariate(0, 8)
            else:
                subs[s] = random.gauss(0, 10) / random.gauss(0, 1)
        n1, n2 = e1.n(subs=subs), e2.n(subs=subs)
        if cmath.isclose(n1, n2, rel_tol=tol):
            eq += 1
    return eq >= acc*samples

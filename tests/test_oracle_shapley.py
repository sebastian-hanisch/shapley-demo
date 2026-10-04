"""Unabhängiges Orakel für den Shapley-Wert und die Kern-Kennzahlen: beliebige (nicht-TSP-)Spiele mit Gleichständen, exakte Bruchrechnung über alle Reihenfolgen,
Koalitionsungleichungen per Schleife, Tourwerte per rekursiver Top-down-Rechnung (anderer Rechenweg als das Bottom-up-Held-Karp der Demo)."""

import itertools
import math
import random
from fractions import Fraction
from functools import lru_cache

import numpy as np

import sh_game as G
import sh_scenario as S


def shapley_fractions(c, n):
    total = [Fraction(0)] * n
    for order in itertools.permutations(range(n)):
        mask = 0
        for i in order:
            total[i] += Fraction(c[mask | 1 << i]) - Fraction(c[mask])
            mask |= 1 << i
    return [float(t / math.factorial(n)) for t in total]


def tsp_topdown(d, stops):
    @lru_cache(None)
    def f(last, rest):
        if not rest:
            return d[last + 1, 0]
        return min(d[last + 1, k + 1] + f(k, tuple(r for r in rest if r != k)) for k in rest)
    if not stops:
        return 0.0
    return min(d[0, k + 1] + f(k, tuple(r for r in stops if r != k)) for k in stops)


def test_shapley_and_core_measures_on_200_random_games_with_ties():
    rng = random.Random(7)
    for t in range(200):
        n = rng.randint(1, 6)
        kind = t % 4
        c = np.zeros(1 << n)
        for m in range(1, 1 << n):
            c[m] = (rng.random() * 10, rng.randint(0, 4), 5.0, sum(((m >> i) & 1) * (i + 1) for i in range(n)))[kind]
        phi = G.shapley(c, n)
        assert np.allclose(phi, shapley_fractions(c, n), atol=1e-9)
        assert abs(phi.sum() - c[-1]) < 1e-9
        x = phi if t % 2 else np.array([rng.random() * c[-1] for _ in range(n)])
        excess = [sum(x[i] for i in range(n) if m >> i & 1) - c[m] for m in range(1, 1 << n)]
        assert abs(G.core_excess(x, c, n)[0] - max(excess)) < 1e-9
        assert G.blocking_count(x, c, n) == sum(e > 1e-9 for e in excess)
        assert G.in_core(x, c, n) == (abs(x.sum() - c[-1]) <= 1e-7 and max(excess) <= 1e-9)


def test_tour_values_agree_with_an_independent_top_down_recursion():
    rng = random.Random(3)
    for _ in range(12):
        n = rng.randint(2, 6)
        d = S.generate(n, rng.choice(("uniform", "clustered")), rng.randrange(10 ** 6)).dist()
        c, _, _ = G.tsp_values(d)
        for m in range(1 << n):
            assert abs(c[m] - tsp_topdown(d, tuple(i for i in range(n) if m >> i & 1))) < 1e-9

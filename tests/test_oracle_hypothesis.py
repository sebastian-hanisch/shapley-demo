"""Property-basierte Ergänzung zum festen Orakeltest (test_oracle_shapley.py): dasselbe Orakel (exakte Bruchrechnung über alle Reihenfolgen, Koalitionsungleichungen per Schleife, rekursive
Top-down-Tourwerte), aber mit Hypothesis erzeugten Spielen (1-6 Spieler, ganzzahlige und Gleitkommawerte, viele Gleichstände) und automatisch verkleinerten Gegenbeispielen.
Deterministisch für die CI (derandomize, keine Beispieldatenbank)."""

import itertools
import math
from fractions import Fraction
from functools import lru_cache

import numpy as np
import pytest

pytest.importorskip("hypothesis")

from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

import sh_game as G  # noqa: E402

CI = settings(max_examples=100, deadline=None, derandomize=True, database=None, suppress_health_check=[HealthCheck.too_slow])


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
            return d[last + 1][0]
        return min(d[last + 1][k + 1] + f(k, tuple(r for r in rest if r != k)) for k in rest)
    if not stops:
        return 0.0
    return min(d[0][k + 1] + f(k, tuple(r for r in stops if r != k)) for k in stops)


@st.composite
def games(draw):
    """(n, c): beliebiges Spiel mit c(leer) = 0; Werte ganzzahlig mit vielen Gleichständen, konstant, additiv oder Gleitkomma >= 0."""
    n = draw(st.integers(1, 6))
    kind = draw(st.sampled_from(("int", "tiny", "float", "constant", "additive")))
    full = 1 << n
    if kind == "int":
        values = draw(st.lists(st.integers(0, 10), min_size=full - 1, max_size=full - 1))
    elif kind == "tiny":
        values = draw(st.lists(st.integers(0, 2), min_size=full - 1, max_size=full - 1))
    elif kind == "float":
        values = draw(st.lists(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False), min_size=full - 1, max_size=full - 1))
    elif kind == "constant":
        values = [5.0] * (full - 1)
    else:
        w = draw(st.lists(st.integers(0, 9), min_size=n, max_size=n))
        values = [float(sum(w[i] for i in range(n) if m >> i & 1)) for m in range(1, full)]
    c = np.array([0.0] + [float(v) for v in values])
    return n, c


@CI
@given(game=games(), data=st.data())
def test_shapley_and_core_measures_match_exact_fractions_and_coalition_loops(game, data):
    n, c = game
    phi = G.shapley(c, n)
    assert np.allclose(phi, shapley_fractions(c, n), atol=1e-9, rtol=1e-9)
    assert abs(phi.sum() - c[-1]) <= 1e-9 * max(1.0, abs(c[-1]))
    if data.draw(st.booleans()):
        x = phi
    else:
        x = np.array(data.draw(st.lists(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False), min_size=n, max_size=n))) * c[-1]
    excess = [sum(x[i] for i in range(n) if m >> i & 1) - c[m] for m in range(1, 1 << n)]
    assert abs(G.core_excess(x, c, n)[0] - max(excess)) < 1e-9
    assert G.blocking_count(x, c, n) == sum(e > 1e-9 for e in excess)
    assert G.in_core(x, c, n) == (abs(x.sum() - c[-1]) <= 1e-7 and max(excess) <= 1e-9)


@st.composite
def distance_matrices(draw):
    """(n+1) x (n+1)-Entfernungsmatrix (Depot = Knoten 0), nicht notwendig symmetrisch, Diagonale 0."""
    n = draw(st.integers(2, 6))
    cost = draw(st.sampled_from((st.integers(0, 3).map(float), st.integers(1, 50).map(float), st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))))
    d = [[0.0 if i == j else draw(cost) for j in range(n + 1)] for i in range(n + 1)]
    return n, d


@CI
@given(inst=distance_matrices())
def test_tour_values_agree_with_an_independent_top_down_recursion(inst):
    n, d = inst
    c, _, _ = G.tsp_values(np.array(d))
    for m in range(1 << n):
        assert abs(c[m] - tsp_topdown(d, tuple(i for i in range(n) if m >> i & 1))) < 1e-9

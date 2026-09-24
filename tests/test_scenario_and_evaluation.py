"""Vehikel (Reproduzierbarkeit, Lage der Stopps) und Auswertung (Analyse, drei Experimente) - schnelle Parameter über Funktionsargumente."""

import numpy as np
import pytest

import sh_constants as C
import sh_evaluation as E
import sh_game as G
import sh_scenario as S


def test_generate_is_reproducible_and_shaped():
    a, b = S.generate(8, "uniform", 5), S.generate(8, "uniform", 5)
    assert np.array_equal(a.xy, b.xy) and a.xy.shape == (9, 2) and a.n == 8
    assert np.allclose(a.xy[0], [C.AREA / 2, C.AREA / 2]) and (a.xy >= 0).all() and (a.xy <= C.AREA).all()
    assert not np.array_equal(a.xy, S.generate(8, "uniform", 6).xy)


def test_clustered_stops_are_closer_together_than_uniform_ones():
    def mean_nn(inst):
        d = inst.dist()[1:, 1:] + np.eye(inst.n) * 1e9
        return d.min(axis=1).mean()
    uniform = np.mean([mean_nn(S.generate(10, "uniform", s)) for s in range(20)])
    clustered = np.mean([mean_nn(S.generate(10, "clustered", s)) for s in range(20)])
    assert clustered < uniform


def test_distance_matrix_is_a_metric():
    d = S.generate(7, "uniform", 3).dist()
    assert np.allclose(d, d.T) and np.allclose(np.diag(d), 0.0)
    for i in range(8):
        for j in range(8):
            for k in range(8):
                assert d[i, k] <= d[i, j] + d[j, k] + 1e-9
    with pytest.raises(ValueError):
        S.generate(4, "bogus", 0)


def test_analyse_default_is_consistent():
    a = E.analyse(E.Settings(n=6))
    assert a.n == 6 and a.grand == pytest.approx(a.c[-1]) and a.savings == pytest.approx(a.alone.sum() - a.grand) and a.savings > 0
    for k in E.METHODS:
        assert a.alloc[k].sum() == pytest.approx(a.grand)
        ex, mask, blocking, ok = a.stability[k]
        assert ok == (ex <= 1e-9) and (blocking == 0) == (ex <= 1e-9) and 1 <= mask < 64
    order = a.grand_tour()
    assert sorted(order) == list(range(6))


def test_settings_cache_and_large_n_run():
    a = E.analyse(E.Settings(n=C.N_MAX))
    assert a.n == C.N_MAX and len(a.grand_tour()) == C.N_MAX


def test_stability_experiment_shape_and_invariants():
    r = E.stability_experiment(n=5, seeds=range(900000, 900010))
    for layout in C.LAYOUTS:
        v = r[layout]
        assert v["n_inst"] == 10 and 0 < v["savings_mean"] < 1
        for k in E.METHODS:
            assert 0 <= v[k]["in_core"] <= 1 and v[k]["excess_rel"] >= 0 and v[k]["excess_rel_max"] >= v[k]["excess_rel"] and v[k]["blocking"] >= 0


def test_scaling_experiment_shape():
    rows = E.scaling_experiment(ns=(4, 5), seeds=range(910000, 910006))
    assert [(r["layout"], r["n"]) for r in rows] == [("uniform", 4), ("uniform", 5), ("clustered", 4), ("clustered", 5)]
    assert all(0 <= r["shapley_in_core"] <= 1 and r["savings"] > 0 for r in rows)


def test_sampling_experiment_shape_and_reproducibility():
    kw = dict(n=6, sample_sizes=(10, 100), seeds=range(920000, 920003), repeats=3)
    a, b = E.sampling_experiment(**kw), E.sampling_experiment(**kw)
    assert [r["samples"] for r in a] == [10, 100] and a == b and all(r["n_runs"] == 9 for r in a)
    assert a[1]["rel_error"] < a[0]["rel_error"] and all(0 <= r["verdict_flip"] <= 1 for r in a)


def test_game_cache_returns_the_same_values_as_direct_computation():
    inst, dist, c, parent, dp = E.game(6, "uniform", 4)
    c2, _, _ = G.tsp_values(S.generate(6, "uniform", 4).dist())
    assert np.array_equal(c, c2)

"""Jede im README/PRESET_HELP/App genannte Zahl wird hier nachgerechnet - keine Behauptung ohne Test.

Koalitionswerte, Shapley und Kern-Prüfung sind exakte Rechnungen fester Instanzen (kein Zufall): Einzelinstanzen mit Toleranz für Rundung, Mittel über Instanzen mit Bändern.
Nur die Stichprobe (Experiment 3) ist zufällig, mit festen Seeds und großzügigen Bändern (feedback_ci_platform_robust_tests / feedback_ci_unpinned_numeric_asserts)."""

import numpy as np
import pytest

import sh_evaluation as E
import sh_game as G
import sh_presets as P


def _preset(name):
    p = P.PRESETS[name]
    return E.analyse(E.Settings(p["n"], p["layout"], p["seed"]))


# --- PRESET_HELP: exakte Werte ---------------------------------------------------------------------------------------------------------------


def test_standardfall_numbers():
    a = _preset("Standardfall (8 Spediteure)")
    assert a.alone.sum() == pytest.approx(797.9, abs=0.06) and a.grand == pytest.approx(328.7, abs=0.06) and a.savings / a.alone.sum() == pytest.approx(0.588, abs=0.001)
    assert a.stability["shapley"][3] and a.stability["proportional"][3] and not a.stability["equal"][3]
    assert a.stability["equal"][0] == pytest.approx(30.0, abs=0.06)
    assert a.alloc["shapley"] == pytest.approx([11.5, 51.9, 53.8, 41.3, 34.3, 34.7, 38.4, 62.9], abs=0.06)


def test_ballung_numbers():
    a = _preset("Zwei Ballungszentren")
    assert a.grand == pytest.approx(152.0, abs=0.06) and a.alone.sum() == pytest.approx(338.4, abs=0.06)
    assert a.stability["shapley"][3] and not a.stability["proportional"][3] and a.stability["proportional"][0] == pytest.approx(26.2, abs=0.06)


def test_sechs_spediteure_numbers():
    a = _preset("Sechs Spediteure")
    assert a.grand == pytest.approx(311.2, abs=0.06) and a.alone.sum() == pytest.approx(562.7, abs=0.06) and a.savings / a.alone.sum() == pytest.approx(0.447, abs=0.001)
    assert a.stability["shapley"][3] and a.stability["proportional"][0] == pytest.approx(18.5, abs=0.06) and a.stability["equal"][0] == pytest.approx(30.8, abs=0.06)


def test_zehn_spediteure_numbers():
    a = _preset("Zehn Spediteure")
    assert a.n == 10 and (1 << a.n) - 1 == 1023
    assert a.grand == pytest.approx(362.4, abs=0.06) and a.alone.sum() == pytest.approx(974.5, abs=0.06) and a.savings / a.alone.sum() == pytest.approx(0.628, abs=0.001)
    assert a.stability["shapley"][3] and a.stability["proportional"][3] and not a.stability["equal"][3]


def test_shapley_nicht_im_kern_numbers():
    a = _preset("Shapley nicht im Kern")
    ex, mask, blocking, ok = a.stability["shapley"]
    assert not ok and ex == pytest.approx(2.95, abs=0.006) and mask == 0b1111111 and blocking == 1 and a.grand == pytest.approx(310.4, abs=0.06)


def test_drei_spediteure_numbers():
    a = _preset("Drei Spediteure (Handrechnung)")
    assert a.alloc["shapley"] == pytest.approx([17.9, 123.7, 113.7], abs=0.06) and a.grand == pytest.approx(255.4, abs=0.06) and a.alone.sum() == pytest.approx(286.5, abs=0.06)
    assert a.savings / a.alone.sum() == pytest.approx(0.109, abs=0.001)
    orders = __import__("itertools").permutations(range(3))
    avg = np.mean([[G.marginal_costs(a.c, o)[j] for j in range(3)] for o in orders], axis=0)
    assert avg == pytest.approx(a.alloc["shapley"])


# --- Experiment 1: Stabilität (60 Instanzen, 8 Spediteure) --------------------------------------------------------------------------------------


def test_stability_experiment_numbers():
    r = E.stability_experiment()
    u, c = r["uniform"], r["clustered"]
    assert u["n_inst"] == 60
    assert u["shapley"]["in_core"] == pytest.approx(0.85, abs=0.03) and c["shapley"]["in_core"] == pytest.approx(0.917, abs=0.03)
    assert u["proportional"]["in_core"] == pytest.approx(0.10, abs=0.03) and c["proportional"]["in_core"] == pytest.approx(0.267, abs=0.04)
    assert u["equal"]["in_core"] == 0.0 and c["equal"]["in_core"] == 0.0
    assert u["shapley"]["blocking"] == pytest.approx(0.167, abs=0.05) and u["proportional"]["blocking"] == pytest.approx(5.5, abs=0.3) and u["equal"]["blocking"] == pytest.approx(14.4, abs=0.5)
    assert c["shapley"]["blocking"] == pytest.approx(0.083, abs=0.05) and c["proportional"]["blocking"] == pytest.approx(3.6, abs=0.3) and c["equal"]["blocking"] == pytest.approx(17.9, abs=0.5)
    assert u["shapley"]["excess_rel"] < 0.003 and u["shapley"]["excess_rel_max"] == pytest.approx(0.022, abs=0.004)
    assert u["savings_mean"] == pytest.approx(0.555, abs=0.005) and c["savings_mean"] == pytest.approx(0.676, abs=0.005)


# --- Experiment 2: Skalierung ------------------------------------------------------------------------------------------------------------------


def test_scaling_experiment_numbers():
    rows = {(r["layout"], r["n"]): r for r in E.scaling_experiment()}
    assert rows[("uniform", 4)]["shapley_in_core"] == 1.0 and rows[("uniform", 10)]["shapley_in_core"] == pytest.approx(0.8, abs=0.05)
    assert rows[("uniform", 4)]["proportional_in_core"] == pytest.approx(0.425, abs=0.05) and rows[("uniform", 10)]["proportional_in_core"] == pytest.approx(0.05, abs=0.05)
    assert rows[("uniform", 10)]["equal_in_core"] == 0.0 and rows[("clustered", 10)]["shapley_in_core"] == pytest.approx(0.95, abs=0.05)
    assert rows[("uniform", 4)]["savings"] == pytest.approx(0.338, abs=0.005) and rows[("uniform", 10)]["savings"] == pytest.approx(0.612, abs=0.005)
    assert rows[("uniform", 10)]["shapley_in_core"] < rows[("uniform", 4)]["shapley_in_core"] and rows[("uniform", 10)]["savings"] > rows[("uniform", 4)]["savings"]


# --- Experiment 3: Stichprobe (zufällig, Bänder) -----------------------------------------------------------------------------------------------


def test_sampling_experiment_numbers():
    rows = {r["samples"]: r for r in E.sampling_experiment()}
    assert rows[10]["rel_error"] == pytest.approx(0.19, abs=0.04) and rows[100]["rel_error"] == pytest.approx(0.061, abs=0.015) and rows[1000]["rel_error"] == pytest.approx(0.020, abs=0.006)
    assert rows[10]["verdict_flip"] > rows[1000]["verdict_flip"] and rows[1000]["verdict_flip"] <= 0.03 and rows[10]["verdict_flip"] < 0.4
    errs = [rows[k]["rel_error"] for k in (10, 30, 100, 300, 1000)]
    assert all(y < x for x, y in zip(errs, errs[1:]))
    assert rows[10]["rel_error"] / rows[1000]["rel_error"] == pytest.approx(10.0, rel=0.35)          # etwa 1/sqrt(K): 100-facher Aufwand, 10-facher Gewinn
    assert rows[10]["n_runs"] == 100

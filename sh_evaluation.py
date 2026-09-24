"""Auswertung: eine Kooperations-Analyse je Instanz (Tourwerte, Shapley, Vergleichs-Aufteilungen, Stabilität) und drei Experimente."""

from dataclasses import dataclass
from functools import lru_cache

import numpy as np

import sh_constants as C
import sh_game as G
import sh_scenario as S


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    layout: str = "uniform"
    seed: int = C.DEFAULT_SEED


@lru_cache(maxsize=256)
def instance(n, layout, seed):
    return S.generate(n, layout, seed)


@lru_cache(maxsize=128)
def game(n, layout, seed):
    """(inst, dist, c, parent, dp) - Tourwerte aller Koalitionen."""
    inst = instance(n, layout, seed)
    dist = inst.dist()
    c, parent, dp = G.tsp_values(dist)
    return inst, dist, c, parent, dp


METHODS = ("shapley", "proportional", "equal")
METHOD_LABELS = {"shapley": "Shapley-Wert", "proportional": "Proportional zu den Alleinkosten", "equal": "Gleiche Ersparnis für alle"}


def allocations(c, n):
    return {"shapley": G.shapley(c, n), "proportional": G.proportional(c, n), "equal": G.equal_savings(c, n)}


@dataclass
class Analysis:
    settings: Settings
    inst: object
    dist: np.ndarray
    c: np.ndarray
    parent: np.ndarray
    dp: np.ndarray
    alloc: dict
    stability: dict          # je Verfahren: (Überschreitung, Maske der schlimmsten Koalition, Zahl blockierender Koalitionen, im Kern?)

    @property
    def n(self):
        return self.inst.n

    @property
    def alone(self):
        return G.stand_alone(self.c, self.n)

    @property
    def grand(self):
        return float(self.c[(1 << self.n) - 1])

    @property
    def savings(self):
        return float(self.alone.sum() - self.grand)

    def grand_tour(self):
        return G.tour(self.dist, self.parent, self.dp, (1 << self.n) - 1)


@lru_cache(maxsize=64)
def analyse(settings):
    inst, dist, c, parent, dp = game(settings.n, settings.layout, settings.seed)
    n = inst.n
    alloc = allocations(c, n)
    stab = {}
    for k, x in alloc.items():
        ex, mask = G.core_excess(x, c, n)
        stab[k] = (ex, mask, G.blocking_count(x, c, n), bool(G.in_core(x, c, n)))
    return Analysis(settings, inst, dist, c, parent, dp, alloc, stab)


# --- Experiment 1: Stabilität der Aufteilungen ------------------------------------------------------------------------------------------------


def stability_experiment(n=None, layouts=None, seeds=None):
    n = C.STAB_N if n is None else n
    layouts = C.LAYOUTS if layouts is None else layouts
    seeds = C.STAB_SEEDS if seeds is None else seeds
    out = {}
    for layout in layouts:
        rows = {k: {"in_core": [], "excess_rel": [], "blocking": []} for k in METHODS}
        savings = []
        for s in seeds:
            _, _, c, _, _ = game(n, layout, s)
            grand = c[(1 << n) - 1]
            savings.append(1.0 - grand / G.stand_alone(c, n).sum())
            for k, x in allocations(c, n).items():
                ex, _ = G.core_excess(x, c, n)
                rows[k]["in_core"].append(ex <= 1e-9 and abs(x.sum() - grand) <= 1e-7)
                rows[k]["excess_rel"].append(max(ex, 0.0) / grand)
                rows[k]["blocking"].append(G.blocking_count(x, c, n))
        out[layout] = {"savings_mean": float(np.mean(savings)), "n_inst": len(seeds),
                       **{k: {"in_core": float(np.mean(v["in_core"])), "excess_rel": float(np.mean(v["excess_rel"])), "excess_rel_max": float(np.max(v["excess_rel"])), "blocking": float(np.mean(v["blocking"]))}
                          for k, v in rows.items()}}
    return out


# --- Experiment 2: Wachsende Spediteurszahl ---------------------------------------------------------------------------------------------------


def scaling_experiment(ns=None, layouts=None, seeds=None):
    ns = C.SCALING_NS if ns is None else ns
    layouts = C.LAYOUTS if layouts is None else layouts
    seeds = C.SCALING_SEEDS if seeds is None else seeds
    rows = []
    for layout in layouts:
        for n in ns:
            r = stability_experiment(n, (layout,), seeds)[layout]
            rows.append({"layout": layout, "n": n, "savings": r["savings_mean"], "shapley_in_core": r["shapley"]["in_core"], "proportional_in_core": r["proportional"]["in_core"],
                         "equal_in_core": r["equal"]["in_core"], "shapley_excess_rel": r["shapley"]["excess_rel"], "shapley_blocking": r["shapley"]["blocking"]})
    return rows


# --- Experiment 3: Stichprobe statt Aufzählung -------------------------------------------------------------------------------------------------


def sampling_experiment(n=None, layout="uniform", sample_sizes=None, seeds=None, repeats=None):
    n = C.SAMPLING_N if n is None else n
    sample_sizes = C.SAMPLE_SIZES if sample_sizes is None else sample_sizes
    seeds = C.SAMPLING_SEEDS if seeds is None else seeds
    repeats = C.SAMPLING_REPEATS if repeats is None else repeats
    rows = []
    for K in sample_sizes:
        errs, flips = [], []
        for s in seeds:
            _, _, c, _, _ = game(n, layout, s)
            exact = G.shapley(c, n)
            exact_in = G.in_core(exact, c, n)
            for r in range(repeats):
                est = G.shapley_sampled(c, n, K, seed=1000 * s + r)
                errs.append(np.abs(est - exact).sum() / np.abs(exact).sum())
                est_fixed = est * (c[(1 << n) - 1] / est.sum())
                flips.append(G.in_core(est_fixed, c, n) != exact_in)
        rows.append({"samples": K, "rel_error": float(np.mean(errs)), "rel_error_max": float(np.max(errs)), "verdict_flip": float(np.mean(flips)), "n_runs": len(errs)})
    return rows

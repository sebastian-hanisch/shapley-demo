"""AppTest-Rauchtests: Voreinstellung, jedes Preset, Handrechnung-Auswahl, Würfel-Knopf, Permalink-Grenzen, Extremwerte, drei Experimente auf Abruf, Footer."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import sh_constants as C
import sh_presets as P

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _run(**state):
    at = AppTest.from_file(APP, default_timeout=300)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    return at


def _ok(at):
    assert not at.exception, [e.value for e in at.exception]


def test_default_run_has_no_exception_and_shows_the_stable_shapley_verdict():
    at = _run()
    _ok(at)
    assert at.metric and any("Der Shapley-Wert ist stabil" in s.value for s in at.success)


@pytest.mark.parametrize("name", list(P.PRESETS))
def test_every_preset_button_runs(name):
    at = _run()
    next(b for b in at.button if b.key == f"preset_{name}").click().run()
    _ok(at)
    p = P.PRESETS[name]
    assert at.session_state["n_slider"] == p["n"] and at.session_state["layout_select"] == p["layout"] and at.session_state["seed_input"] == p["seed"]
    assert at.metric


def test_unstable_shapley_warning_for_the_special_seed():
    at = _run(seed_input=12)
    _ok(at)
    assert any("Der Shapley-Wert ist hier nicht stabil" in w.value for w in at.warning)


def test_hand_calculation_needs_exactly_three_carriers():
    at = _run()
    _ok(at)
    assert not any("Bitte genau drei" in i.value for i in at.info)
    at.multiselect(key="hand_pick").set_value([1, 2]).run()
    _ok(at)
    assert any("Bitte genau drei" in i.value for i in at.info)
    at.multiselect(key="hand_pick").set_value([2, 4, 6]).run()
    _ok(at)


def test_dice_button_changes_the_seed():
    at = _run()
    old = at.session_state["seed_input"]
    next(b for b in at.button if b.label == "🎲 Neues Vehikel generieren").click().run()
    _ok(at)
    assert at.session_state["seed_input"] != old


def test_permalink_values_are_clamped():
    at = AppTest.from_file(APP, default_timeout=300)
    at.query_params["n"] = "9999"
    at.query_params["layout"] = "clustered"
    at.run()
    _ok(at)
    assert at.session_state["n_slider"] == C.N_MAX and at.session_state["layout_select"] == "clustered"


@pytest.mark.parametrize("kw", [dict(n_slider=C.N_MIN), dict(n_slider=C.N_MAX), dict(layout_select="clustered"), dict(n_slider=4, layout_select="clustered", seed_input=0)])
def test_extreme_settings_run(kw):
    _ok(_run(**kw))


def test_hand_calculation_with_three_carriers_only():
    at = _run(n_slider=3)
    _ok(at)
    assert any("Durchschnitt über die 6 Reihenfolgen" in c.value for c in at.caption)


def test_stability_experiment_runs_on_demand(monkeypatch):
    monkeypatch.setattr(C, "STAB_SEEDS", tuple(range(900000, 900004)))
    monkeypatch.setattr(C, "STAB_N", 5)
    at = _run()
    next(b for b in at.button if b.key == "stability_start").click().run()
    _ok(at)
    assert at.session_state["stability_on"] and at.get("plotly_chart")


def test_scaling_experiment_runs_on_demand(monkeypatch):
    monkeypatch.setattr(C, "SCALING_NS", (4, 5))
    monkeypatch.setattr(C, "SCALING_SEEDS", tuple(range(910000, 910004)))
    at = _run()
    next(b for b in at.button if b.key == "scaling_start").click().run()
    _ok(at)
    assert at.session_state["scaling_on"]


def test_sampling_experiment_runs_on_demand(monkeypatch):
    monkeypatch.setattr(C, "SAMPLING_N", 6)
    monkeypatch.setattr(C, "SAMPLING_SEEDS", tuple(range(920000, 920002)))
    monkeypatch.setattr(C, "SAMPLING_REPEATS", 2)
    monkeypatch.setattr(C, "SAMPLE_SIZES", (10, 100, 1000))
    at = _run()
    next(b for b in at.button if b.key == "sampling_start").click().run()
    _ok(at)
    assert at.session_state["sampling_on"]
    assert any("1.024 Koalitionen" in w.value or "64 Koalitionen" in w.value for w in at.warning)          # Tausenderpunkte im Text, keine Kommas


def test_footer_and_grenzen_are_present():
    at = _run()
    assert any("Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net)" in c.value for c in at.caption)
    assert any("Wo die Annahmen enden" in s.value for s in at.subheader)
    assert not any("{" in c.value and "(" in c.value and "de(" in c.value for c in at.caption)

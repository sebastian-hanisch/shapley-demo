"""SETTING_SPECS-Permalink-Muster, Presets und Zufalls-Seed-Button (Standardmuster des Portfolios, vgl. nash_presets.py)."""

import math
import random
from dataclasses import dataclass
from typing import Callable, Optional

import streamlit as st

import sh_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: Callable
    default: object
    lo: Optional[float] = None
    hi: Optional[float] = None


def _choice(options):
    def cast(value):
        value = str(value)
        if value not in options:
            raise ValueError(value)
        return value
    return cast


SETTING_SPECS = {
    "n_slider": SettingSpec("n", int, C.DEFAULT_N, C.N_MIN, C.N_MAX),
    "layout_select": SettingSpec("layout", _choice(C.LAYOUTS), "uniform"),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
}
PRESET_KEYS = {"n": "n_slider", "layout": "layout_select", "seed": "seed_input"}
STEPS = {"n_slider": C.N_STEP}

PRESETS = {
    "Standardfall (8 Spediteure)": {"n": 8, "layout": "uniform", "seed": 35},
    "Zwei Ballungszentren": {"n": 8, "layout": "clustered", "seed": 35},
    "Sechs Spediteure": {"n": 6, "layout": "uniform", "seed": 35},
    "Zehn Spediteure": {"n": 10, "layout": "uniform", "seed": 35},
    "Shapley nicht im Kern": {"n": 8, "layout": "uniform", "seed": 12},
    "Drei Spediteure (Handrechnung)": {"n": 3, "layout": "uniform", "seed": 35},
}


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def load_permalink_settings():
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
                if isinstance(value, float) and not math.isfinite(value):
                    continue
                if spec.lo is not None:
                    value = max(spec.lo, value)
                if spec.hi is not None:
                    value = min(spec.hi, value)
                st.session_state[state_key] = value
            except (ValueError, TypeError):
                pass
    for key, step in STEPS.items():
        if key in st.session_state:
            spec = SETTING_SPECS[key]
            snapped = spec.lo + round((st.session_state[key] - spec.lo) / step) * step
            st.session_state[key] = int(min(spec.hi, max(spec.lo, snapped)))
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    for key, state_key in PRESET_KEYS.items():
        st.session_state[state_key] = PRESETS[name][key]


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, C.SEED_MAX)


PRESET_HELP = {
    "Standardfall (8 Spediteure)": "8 Spediteure mit je einem Stopp, gemeinsames Depot in der Mitte: alle allein 797,9 km, gemeinsam 328,7 km (58,8 % Ersparnis). Der Shapley-Wert und die proportionale Aufteilung sind stabil, die gleiche Ersparnis für alle nicht (eine Koalition führe 30,0 km günstiger allein).",
    "Zwei Ballungszentren": "Stopps in zwei Ballungszentren: gemeinsam 152,0 statt 338,4 km. Hier ist nur der Shapley-Wert stabil, die proportionale Aufteilung überschreitet eine Koalition um 26,2 km.",
    "Sechs Spediteure": "6 Spediteure: 311,2 statt 562,7 km (44,7 % Ersparnis). Nur der Shapley-Wert liegt im Kern; proportional überschreitet eine Koalition um 18,5 km, gleiche Ersparnis um 30,8 km.",
    "Zehn Spediteure": "10 Spediteure: 362,4 statt 974,5 km (62,8 % Ersparnis), 1 023 Koalitionen. Shapley und proportional sind stabil, die gleiche Ersparnis nicht.",
    "Shapley nicht im Kern": "Ein Vehikel, in dem der Shapley-Wert eine Koalition benachteiligt: die Spediteure 1 bis 7 könnten allein 2,95 km günstiger fahren als mit der Shapley-Aufteilung. Der Shapley-Wert liegt hier außerhalb des Kerns; ob der Kern selbst leer ist, klärt das nächste Stück.",
    "Drei Spediteure (Handrechnung)": "Nur drei Spediteure: alle 7 Koalitionswerte und die 6 Reihenfolgen passen in eine Tabelle - der Shapley-Wert lässt sich von Hand nachrechnen (17,9 / 123,7 / 113,7 km).",
}

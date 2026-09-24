"""Konstanten der Shapley-Demo: Vehikel B "Spediteurs-Kooperation", Regler, Experimente (Presets nach den Messungen)."""

EPS = 1e-9
SEED_MAX = 999999

# --- Vehikel B --------------------------------------------------------------------------------------------------------------------------------

AREA = 100.0                       # Gebiet in km
CLUSTER_SIGMA = 8.0                # Streuung der Stopps um die Ballungszentren
N_CLUSTERS = 2
LAYOUTS = ("uniform", "clustered")
LAYOUT_LABELS = {"uniform": "Gleichmäßig verteilt", "clustered": "Zwei Ballungszentren"}

N_MIN, N_MAX, DEFAULT_N, N_STEP = 3, 12, 8, 1
DEFAULT_SEED = 35

# --- Experimente (feste Seeds) ---------------------------------------------------------------------------------------------------------------

STAB_N = 8
STAB_SEEDS = tuple(range(900000, 900060))
SCALING_NS = (4, 5, 6, 7, 8, 9, 10)
SCALING_SEEDS = tuple(range(910000, 910040))
SAMPLING_N = 10
SAMPLING_SEEDS = tuple(range(920000, 920010))
SAMPLING_REPEATS = 10
SAMPLE_SIZES = (10, 30, 100, 300, 1000)

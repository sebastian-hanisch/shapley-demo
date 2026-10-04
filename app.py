"""Shapley-Wert - wie Spediteure die Kosten einer gemeinsamen Tour fair teilen - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Siebtes Stück der Linie "Spieltheorie & Mechanism Design" der "Konzepte"-Reihe (Wurzel von Ast B, kooperative Spieltheorie): Spediteure bündeln ihre Touren; wie wird die Ersparnis gerecht verteilt?

Lauffähig mit: streamlit run app.py
"""

import itertools

import numpy as np
import streamlit as st

import sh_constants as C
import sh_evaluation as E
import sh_game as G
from sh_evaluation import Settings, analyse, sampling_experiment, scaling_experiment, stability_experiment
from sh_presets import PRESET_HELP, PRESETS, apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_seed, sync_query_params
from sh_visualization import build_allocation, build_map, build_sampling, build_scaling, build_stability

st.set_page_config(page_title="Shapley-Wert – Sebastian Hanisch", layout="wide")


def de(x, digits=1):
    """Deutsche Zahlenschreibweise: Punkt als Tausendertrenner, Komma als Dezimalzeichen."""
    return f"{x:,.{digits}f}".replace(",", "#").replace(".", ",").replace("#", ".")


def pct(x, digits=0):
    return f"{de(100 * x, digits)} %"


def names_of(mask, n):
    return "Spediteure " + ", ".join(str(i + 1) for i in G.coalition_members(mask, n)) if bin(mask).count("1") > 1 else f"Spediteur {G.coalition_members(mask, n)[0] + 1}"


@st.cache_data(show_spinner=False)
def _stability():
    return stability_experiment()


@st.cache_data(show_spinner=False)
def _scaling():
    return scaling_experiment()


@st.cache_data(show_spinner=False)
def _sampling():
    return sampling_experiment()


st.title("🤝 Shapley-Wert – wie Spediteure die Kosten einer gemeinsamen Tour fair teilen")
st.markdown(
    """
Mehrere Spediteure beliefern je einen Kunden ab demselben Depot. Fährt jeder allein, entstehen viele lange Touren; fahren sie **gemeinsam eine Tour**, sinkt die Gesamtstrecke erheblich. Die Frage der kooperativen Spieltheorie:
**wie wird die Gesamtstrecke fair auf die Spediteure verteilt?** Der **Shapley-Wert** (Shapley 1953) rechnet jedem Spediteur den Durchschnitt seiner Grenzkosten über alle Reihenfolgen an, in denen die Spediteure der
Kooperation beitreten. Die Demo berechnet ihn exakt (mit dem optimalen Tourwert jeder Koalition per Held-Karp), vergleicht ihn mit zwei naheliegenden Aufteilungen und prüft, ob eine Gruppe von Spediteuren sich
allein besser stellen würde.
"""
)
st.caption(
    "Siebtes Stück der Linie \"Spieltheorie & Mechanism Design\" der \"Konzepte\"-Reihe und Wurzel des zweiten Astes (kooperative Spieltheorie): die bisherigen Stücke betrachteten eigennützige Lkw, hier "
    "schließen sich Spediteure freiwillig zusammen. Die Kosten der gemeinsamen Tour sind der Tourwert einer Koalition; wer wie viel zahlt, ist die eigentliche Frage."
)

with st.expander("So funktioniert die Kostenaufteilung", expanded=True):
    st.markdown(
        """
1. **Koalitionswert.** Für jede Gruppe *S* von Spediteuren ist *c(S)* die Länge der kürzesten Rundtour ab Depot durch alle Stopps der Gruppe (exakt per Held-Karp; eine Rechnung liefert alle $2^n$ Werte).
   Die Kosten der Alleinfahrt sind *c({i})*.
2. **Shapley-Wert.** Jeder Spediteur zahlt den Durchschnitt seiner Grenzkosten *c(S ∪ {i}) − c(S)* über alle Reihenfolgen, in denen die Spediteure hinzukommen. Er ist die einzige Aufteilung mit vier Eigenschaften:
   **Effizienz** (die Anteile ergeben genau die Gesamtkosten), **Symmetrie** (gleiche Spediteure zahlen gleich), **Nullspieler** (wer nichts beiträgt, zahlt nichts) und **Additivität**.
3. **Stabilität (Kern).** Eine Aufteilung ist stabil, wenn keine Gruppe von Spediteuren allein günstiger führe, als sie zusammen zahlt: $\\sum_{i \\in S} x_i \\le c(S)$ für alle Gruppen *S*. Das ist eine zweite, andere Gerechtigkeit als die
   Shapley-Axiome; die Demo prüft sie für alle $2^n - 1$ Gruppen.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
preset_names = list(PRESETS.keys())
for row in (preset_names[:3], preset_names[3:]):
    cols = st.columns(len(row))
    for col, name in zip(cols, row):
        with col:
            st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=PRESET_HELP[name], key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    n_carriers = st.slider("Spediteure", *bounds("n_slider"), key="n_slider", step=C.N_STEP, help="Anzahl der Spediteure mit je einem Stopp. Die Rechnung wächst mit 2^n Koalitionen.")
    layout = st.selectbox("Lage der Stopps", C.LAYOUTS, key="layout_select", format_func=lambda k: C.LAYOUT_LABELS[k], help="Gleichmäßig im Gebiet verteilt oder um zwei Ballungszentren gruppiert.")
    seed = st.number_input("Zufalls-Seed des Vehikels", *bounds("seed_input"), key="seed_input", step=1, help="Legt die Lage der Stopps fest.")
    st.button("🎲 Neues Vehikel generieren", width="stretch", on_click=randomize_seed)

sync_query_params({"n_slider": int(n_carriers), "layout_select": layout, "seed_input": int(seed)})

settings = Settings(int(n_carriers), layout, int(seed))
with st.spinner("Rechne alle Koalitionen..."):
    a = analyse(settings)
inst, n = a.inst, a.n
phi = a.alloc["shapley"]

# --- Die gemeinsame Tour ----------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Die gemeinsame Tour")
m1, m2, m3 = st.columns(3)
m1.metric("Alle fahren allein", f"{de(a.alone.sum())} km", help="Summe der Alleinfahrten Depot - Stopp - Depot.")
m2.metric("Gemeinsame Tour", f"{de(a.grand)} km", help="Kürzeste Rundtour ab Depot durch alle Stopps (Held-Karp, exakt).")
m3.metric("Ersparnis", f"{de(a.savings)} km", delta=f"{pct(a.savings / a.alone.sum(), 1)} der Alleinfahrten", delta_color="off")
st.plotly_chart(build_map(inst, a.grand_tour(), phi), width="stretch", key="map_chart")
st.caption("Blau: die gemeinsame Tour. Grau gepunktet: die Alleinfahrten. Die Größe eines Stopps zeigt seinen Kostenanteil nach Shapley.")

st.markdown("---")

# --- Kostenaufteilung -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Wer zahlt wie viel?")
st.dataframe(
    {"Spediteur": [f"Spediteur {i + 1}" for i in range(n)], "Alleinfahrt (km)": [de(x) for x in a.alone],
     "Shapley-Wert (km)": [de(x) for x in phi], "Ersparnis nach Shapley": [pct(1 - phi[i] / a.alone[i]) for i in range(n)],
     "Proportional (km)": [de(x) for x in a.alloc["proportional"]], "Gleiche Ersparnis (km)": [de(x) for x in a.alloc["equal"]]},
    hide_index=True,
)
st.caption(f"Summe jeder Spalte außer der Alleinfahrt: {de(a.grand)} km (Effizienz). \"Proportional\" verteilt die Gesamtstrecke im Verhältnis der Alleinfahrten, \"Gleiche Ersparnis\" gibt jedem denselben Ersparnisbetrag "
           f"({de(a.savings / n)} km).")
st.plotly_chart(build_allocation(a), width="stretch", key="allocation_chart")

st.markdown("**Ist die Aufteilung stabil?** (keine Gruppe von Spediteuren fährt allein günstiger)")
stab_rows = []
for k in E.METHODS:
    ex, mask, blocking, ok = a.stability[k]
    stab_rows.append({"Verfahren": E.METHOD_LABELS[k], "Im Kern": "ja" if ok else "nein", "Größte Überschreitung (km)": de(max(ex, 0.0), 2), "Schlimmste Koalition": names_of(mask, n) if ex > 1e-9 else "-", "Blockierende Koalitionen": blocking})
st.dataframe(stab_rows, hide_index=True)
ex_s, mask_s, block_s, ok_s = a.stability["shapley"]
if ok_s:
    st.success(f"✅ Der Shapley-Wert ist stabil: keine der {2 ** n - 1} Koalitionen käme allein günstiger. Er erfüllt die Shapley-Axiome und liegt im Kern.")
else:
    st.warning(f"⚠️ Der Shapley-Wert ist hier nicht stabil: {names_of(mask_s, n)} zahlen zusammen {de(ex_s, 2)} km mehr, als sie allein führen ({block_s} blockierende "
               f"Koalition{'en' if block_s != 1 else ''}). Der Shapley-Wert ist fair im Sinne seiner Axiome, aber nicht immer im Sinne des Kerns - das behandelt das achte Stück der Linie, kern-demo.")

st.markdown("---")

# --- Shapley von Hand -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Shapley von Hand: drei Spediteure")
st.caption("Wählen Sie drei Spediteure. Ihr Teilspiel hat nur 7 Koalitionen und 6 Reihenfolgen - der Shapley-Wert lässt sich nachrechnen. Die Werte sind die Tourlängen der Koalition allein (ohne die übrigen Spediteure).")
pick = st.multiselect("Spediteure", list(range(1, n + 1)), default=[1, 2, 3][:n], max_selections=3, format_func=lambda i: f"Spediteur {i}", key="hand_pick")
if len(pick) != 3:
    st.info("Bitte genau drei Spediteure wählen.")
else:
    ids = [p - 1 for p in pick]
    sub_c = np.zeros(8)
    for m_local in range(1, 8):
        mask = sum(1 << ids[j] for j in range(3) if (m_local >> j) & 1)
        sub_c[m_local] = a.c[mask]
    st.markdown("**Koalitionswerte** (Tourlänge in km)")
    st.dataframe({"Koalition": [", ".join(str(ids[j] + 1) for j in range(3) if (m >> j) & 1) for m in range(1, 8)], "Tourlänge (km)": [de(sub_c[m], 2) for m in range(1, 8)]}, hide_index=True)
    orders = list(itertools.permutations(range(3)))
    rows_o = []
    for order in orders:
        mc = G.marginal_costs(sub_c, order)
        rows_o.append({"Reihenfolge": " → ".join(str(ids[j] + 1) for j in order), **{f"Spediteur {ids[j] + 1}": de(mc[j], 2) for j in range(3)}})
    avg = np.mean([[G.marginal_costs(sub_c, o)[j] for j in range(3)] for o in orders], axis=0)
    rows_o.append({"Reihenfolge": "Durchschnitt = Shapley-Wert", **{f"Spediteur {ids[j] + 1}": de(avg[j], 2) for j in range(3)}})
    st.markdown("**Grenzkosten bei jeder Reihenfolge**")
    st.dataframe(rows_o, hide_index=True)
    formula = G.shapley(sub_c, 3)
    st.caption(f"Der Durchschnitt über die 6 Reihenfolgen stimmt mit der Formel überein (Summe {de(avg.sum(), 2)} km = Tourlänge der drei zusammen {de(sub_c[7], 2)} km). "
               f"Achtung: Das ist der Shapley-Wert des Teilspiels mit nur diesen drei Spediteuren, nicht der Anteil im {n}-Spediteure-Spiel oben. Abweichung Formel gegen Durchschnitt: {'unter 0,000001' if float(np.abs(avg - formula).max()) < 1e-6 else de(float(np.abs(avg - formula).max()), 6)} km.")

st.markdown("---")

# --- Experiment 1: Stabilität -----------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Welche Aufteilung ist stabil?")
st.caption(f"{C.STAB_N} Spediteure, {len(C.STAB_SEEDS)} feste Instanzen je Lage der Stopps; für jede Aufteilung werden alle {2 ** C.STAB_N - 1} Koalitionen geprüft.")
if st.button("Stabilität messen (dauert etwa 5 Sekunden)", key="stability_start"):
    st.session_state["stability_on"] = True
if st.session_state.get("stability_on"):
    with st.spinner("Rechne 120 Instanzen..."):
        res_s = _stability()
    st.plotly_chart(build_stability(res_s), width="stretch", key="stability_chart")
    u, c = res_s["uniform"], res_s["clustered"]
    st.warning(
        f"**Befund:** Der Shapley-Wert liegt bei gleichmäßig verteilten Stopps in {pct(u['shapley']['in_core'])} der Instanzen im Kern, bei geballten in {pct(c['shapley']['in_core'])}; die proportionale Aufteilung nur in "
        f"{pct(u['proportional']['in_core'])} bzw. {pct(c['proportional']['in_core'])}, die gleiche Ersparnis in {pct(u['equal']['in_core'])} bzw. {pct(c['equal']['in_core'])}. Blockierende Koalitionen gibt es im Mittel "
        f"{de(u['shapley']['blocking'], 1)} (Shapley), {de(u['proportional']['blocking'], 1)} (proportional) und {de(u['equal']['blocking'], 1)} (gleiche Ersparnis) je Instanz. Wo der Shapley-Wert nicht stabil ist, ist die Überschreitung klein: über alle Instanzen gemittelt "
        f"{pct(u['shapley']['excess_rel'], 1)} der Gesamtstrecke, im Einzelfall höchstens {pct(u['shapley']['excess_rel_max'], 1)}. Die naheliegenden Aufteilungen sind dagegen meist instabil, obwohl die Ersparnis mit im Mittel {pct(u['savings_mean'])} (gleichmäßig) bzw. {pct(c['savings_mean'])} (geballt) der Alleinfahrten groß ist."
    )

st.markdown("---")

# --- Experiment 2: Skalierung -----------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Bleibt der Shapley-Wert stabil, wenn mehr Spediteure mitmachen?")
st.caption(f"{len(C.SCALING_SEEDS)} feste Instanzen je Spediteurszahl von {C.SCALING_NS[0]} bis {C.SCALING_NS[-1]} und je Lage der Stopps.")
if st.button("Skalierung messen (dauert etwa 15 Sekunden)", key="scaling_start"):
    st.session_state["scaling_on"] = True
if st.session_state.get("scaling_on"):
    with st.spinner("Rechne..."):
        rows_sc = _scaling()
    st.plotly_chart(build_scaling(rows_sc), width="stretch", key="scaling_chart")
    u4 = next(r for r in rows_sc if r["layout"] == "uniform" and r["n"] == C.SCALING_NS[0])
    u10 = next(r for r in rows_sc if r["layout"] == "uniform" and r["n"] == C.SCALING_NS[-1])
    st.warning(
        f"**Befund:** Bei gleichmäßig verteilten Stopps liegt der Shapley-Wert bei {u4['n']} Spediteuren in {pct(u4['shapley_in_core'])} der Instanzen im Kern, bei {u10['n']} in {pct(u10['shapley_in_core'])}; die proportionale Aufteilung fällt von "
        f"{pct(u4['proportional_in_core'])} auf {pct(u10['proportional_in_core'])}. Je mehr Spediteure, desto mehr Gruppen können sich abspalten - und desto häufiger reicht keine einfache Regel. Die Ersparnis wächst dabei von "
        f"{pct(u4['savings'])} auf {pct(u10['savings'])} der Alleinfahrten."
    )

st.markdown("---")

# --- Experiment 3: Stichprobe -----------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Geht es auch ohne alle Reihenfolgen? Stichprobe statt Aufzählung")
st.caption(f"Der exakte Shapley-Wert braucht alle $2^n$ Koalitionen (oder $n!$ Reihenfolgen). Hier {C.SAMPLING_N} Spediteure, {len(C.SAMPLING_SEEDS)} Instanzen, je {C.SAMPLING_REPEATS} Wiederholungen: Schätzung als Mittel der Grenzkosten "
           "über K zufällige Reihenfolgen, verglichen mit dem exakten Wert.")
if st.button("Stichprobe messen (dauert etwa 5 Sekunden)", key="sampling_start"):
    st.session_state["sampling_on"] = True
if st.session_state.get("sampling_on"):
    with st.spinner("Rechne..."):
        rows_sa = _sampling()
    st.plotly_chart(build_sampling(rows_sa), width="stretch", key="sampling_chart")
    r100 = next(r for r in rows_sa if r["samples"] == 100)
    r1000 = next(r for r in rows_sa if r["samples"] == 1000)
    r10 = next(r for r in rows_sa if r["samples"] == 10)
    st.warning(
        f"**Befund:** Mit {r10['samples']} zufälligen Reihenfolgen liegt der relative Fehler im Mittel bei {pct(r10['rel_error'], 0)}, mit {r100['samples']} bei {pct(r100['rel_error'], 1)}, mit {r1000['samples']} bei {pct(r1000['rel_error'], 1)} - er sinkt etwa mit 1/√K. "
        f"Die Stabilitätsaussage (im Kern oder nicht) kippt bei {r10['samples']} Reihenfolgen in {pct(r10['verdict_flip'])} der Läufe, bei {r100['samples']} in {pct(r100['verdict_flip'], 1)}. Bei {C.SAMPLING_N} Spediteuren gibt es {de(2 ** C.SAMPLING_N, 0)} Koalitionen "
        f"gegenüber {de(int(np.prod(range(1, C.SAMPLING_N + 1))), 0)} Reihenfolgen - ab einer gewissen Größe ist die Stichprobe der einzige Weg."
    )

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Jeder Spediteur hat genau einen Stopp und es gibt keine Kapazität** | Mit Kapazitäten und mehreren Stopps je Spediteur ist der Koalitionswert ein Tourenplanungsproblem (VRP) und die Subadditivität der Kosten (Kooperation lohnt) gilt nicht mehr automatisch. | [VRP-Demos](https://sebastianhanisch.net/demos.html) |
| **Die Kosten einer Koalition sind die kürzeste Rundtour** | In der Praxis kommen Zeitfenster, Beladung und Fahrerzeiten dazu; jeder Koalitionswert wird zu einem schweren Optimierungsproblem. Held-Karp trägt nur bis etwa 15 Stopps. | Stichprobe (siehe Experiment) |
| **Shapley ist die gerechte Aufteilung** | Shapley erfüllt vier Axiome, aber nicht immer die Stabilitätsbedingung des Kerns (Experiment oben). Wer beides verlangt, braucht den Kern und ggf. den Nukleolus. | **Kern und Nukleolus** (kern-demo, achtes Stück) |
| **Alle Spediteure wollen kooperieren** | Der Wert der Kooperation hängt von den Koalitionen ab, die sich stattdessen bilden könnten; Verhandlung und Vertrauen liegen außerhalb dieses Modells. | - |
| **Die Kostenaufteilung wird von außen gesetzt** | Ob Spediteure ihre Kosten ehrlich melden, ist eine Frage des Mechanism Designs. | Kostenteilung mit Anreizen (Moulin-Shenker) |
"""
)
st.caption(
    "Verwandt: [maut-demo](https://sebastianhanisch-maut-demo.streamlit.app/) (Preise, die Externalitäten einpreisen - der Zwilling der Kostenteilung), "
    "[stackelberg-demo](https://sebastianhanisch-stackelberg-demo.streamlit.app/) (Ast A der Linie: eigennützige Lkw)."
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Kostenspiel.** Spediteure $N = \{1,\dots,n\}$, Koalitionswert $c(S)$ = Länge der kürzesten Rundtour ab Depot durch alle Stopps in $S$, $c(\emptyset) = 0$ (Traveling-Salesman-Spiel, Potters/Curiel/Tijs 1992).
Wegen der Dreiecksungleichung gilt $c(S \cup T) \le c(S) + c(T)$: Kooperation lohnt.

**Held-Karp.** $d(S, j)$ = kürzester Weg vom Depot durch genau die Stopps in $S$ mit Ende bei $j$: $d(S, j) = \min_{k \in S \setminus \{j\}} d(S \setminus \{j\}, k) + \text{dist}(k, j)$, und
$c(S) = \min_{j \in S} d(S, j) + \text{dist}(j, \text{Depot})$. Eine Rechnung über alle Teilmengen liefert alle $2^n - 1$ Koalitionswerte in $O(2^n n^2)$.

**Shapley-Wert** (Shapley 1953). $\displaystyle \phi_i = \sum_{S \subseteq N \setminus \{i\}} \frac{|S|!\,(n - |S| - 1)!}{n!}\,\big[c(S \cup \{i\}) - c(S)\big]$ - der Durchschnitt der Grenzkosten von $i$ über alle $n!$
Reihenfolgen. Er ist effizient ($\sum_i \phi_i = c(N)$), symmetrisch, gibt Nullspielern nichts und ist additiv - und durch diese vier Eigenschaften eindeutig bestimmt.

**Kern.** $\{x : \sum_i x_i = c(N),\ \sum_{i \in S} x_i \le c(S)\ \forall S \subseteq N\}$. Der Kern eines Traveling-Salesman-Spiels kann leer sein, auch bei Dreiecksungleichung (Potters/Curiel/Tijs 1992);
die Demo prüft nur, ob der Shapley-Wert und die beiden Vergleichs-Aufteilungen im Kern liegen.

**Vergleichs-Aufteilungen.** Proportional: $x_i = c(N)\,c(\{i\}) / \sum_j c(\{j\})$. Gleiche Ersparnis: $x_i = c(\{i\}) - \big(\sum_j c(\{j\}) - c(N)\big)/n$.

**Stichprobe.** $\hat\phi_i = \frac1K \sum_{k=1}^K \big[c(P_i^k \cup \{i\}) - c(P_i^k)\big]$ mit $P_i^k$ = die Vorgänger von $i$ in der $k$-ten zufälligen Reihenfolge; unverzerrt, Fehler $\sim 1/\sqrt K$.

Implementiert in `sh_game.py` (Held-Karp, Shapley, Kern-Prüfung, Vergleichs-Aufteilungen, Stichprobe), `sh_scenario.py` (Vehikel), `sh_evaluation.py` (Analyse, Experimente).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Spieltheorie: von Nash bis Myerson-Satterthwaite](https://sebastianhanisch.net/konzepte-spieltheorie.html)."
)

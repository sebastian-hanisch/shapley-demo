"""Plotly-Abbildungen der Shapley-Demo. Achsen sind gesperrt (fixedrange)."""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import sh_constants as C
import sh_evaluation as E

LINE_COLOR = "#4c78a8"
REF_COLOR = "#7f7f7f"
GOOD = "#54a24b"
BAD = "#e45756"
WARN = "#f58518"
METHOD_COLORS = {"shapley": GOOD, "proportional": LINE_COLOR, "equal": WARN}


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_map(inst, order, shares=None):
    """Depot, Stopps und die optimale gemeinsame Tour (durchgezogen); die Alleinfahrten dünn gepunktet. Markergröße = Kostenanteil nach Shapley."""
    xy = inst.xy
    fig = go.Figure()
    for i in range(inst.n):
        fig.add_trace(go.Scatter(x=[xy[0, 0], xy[i + 1, 0], xy[0, 0]], y=[xy[0, 1], xy[i + 1, 1], xy[0, 1]], mode="lines", line=dict(color="#c9c9c9", width=1, dash="dot"), hoverinfo="skip", showlegend=False))
    path = [0] + [j + 1 for j in order] + [0]
    fig.add_trace(go.Scatter(x=xy[path, 0], y=xy[path, 1], mode="lines", line=dict(color=LINE_COLOR, width=3), name="Gemeinsame Tour", hoverinfo="skip"))
    sizes = [16] * inst.n if shares is None else list(10 + 30 * np.asarray(shares) / max(shares))
    fig.add_trace(go.Scatter(x=xy[1:, 0], y=xy[1:, 1], mode="markers+text", text=[str(i + 1) for i in range(inst.n)], textposition="middle center", textfont=dict(color="white", size=11),
                             marker=dict(size=sizes, color=GOOD, line=dict(color="white", width=1)), name="Spediteure (Größe = Kostenanteil nach Shapley)",
                             hovertemplate="Spediteur %{text}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[xy[0, 0]], y=[xy[0, 1]], mode="markers", marker=dict(size=16, symbol="square", color="#14233B"), name="Depot", hoverinfo="skip"))
    fig.update_xaxes(range=[-5, C.AREA + 5], visible=False)
    fig.update_yaxes(range=[-5, C.AREA + 5], visible=False, scaleanchor="x", scaleratio=1)
    return _base(fig, 420)


def build_allocation(analysis):
    """Kosten je Spediteur: Alleinfahrt und die Kostenanteile nach den drei Aufteilungsverfahren."""
    names = [f"Spediteur {i + 1}" for i in range(analysis.n)]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=names, y=analysis.alone, name="Alleinfahrt", marker_color="#c9c9c9"))
    for k in E.METHODS:
        fig.add_trace(go.Bar(x=names, y=analysis.alloc[k], name=E.METHOD_LABELS[k], marker_color=METHOD_COLORS[k]))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Kosten (km Tourlänge)")
    return _base(fig, 340)


def build_stability(res):
    """Anteil der Instanzen, in denen die Aufteilung im Kern liegt (links), und mittlere Zahl blockierender Koalitionen (rechts), je Verfahren und Standortverteilung."""
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Aufteilung im Kern (% der Instanzen)", "Blockierende Koalitionen je Instanz (Mittel)"), horizontal_spacing=0.12)
    for layout, dash in zip(C.LAYOUTS, (1.0, 0.55)):
        vals = res[layout]
        names = [E.METHOD_LABELS[k] for k in E.METHODS]
        fig.add_trace(go.Bar(x=names, y=[100 * vals[k]["in_core"] for k in E.METHODS], name=C.LAYOUT_LABELS[layout], marker_color=[METHOD_COLORS[k] for k in E.METHODS], opacity=dash,
                             text=[f"{100 * vals[k]['in_core']:.0f}" for k in E.METHODS], textposition="outside"), row=1, col=1)
        fig.add_trace(go.Bar(x=names, y=[vals[k]["blocking"] for k in E.METHODS], name=C.LAYOUT_LABELS[layout], marker_color=[METHOD_COLORS[k] for k in E.METHODS], opacity=dash, showlegend=False,
                             text=[f"{vals[k]['blocking']:.1f}" for k in E.METHODS], textposition="outside"), row=1, col=2)
    fig.update_layout(barmode="group", height=360, margin=dict(l=10, r=10, t=40, b=10), plot_bgcolor="rgba(0,0,0,0)")
    fig.update_yaxes(range=[0, 115], row=1, col=1)
    return lock_axes(fig)


def build_scaling(rows):
    """Anteil der Instanzen mit Aufteilung im Kern über der Spediteurszahl, je Verfahren; links gleichmäßig verteilte, rechts geballte Stopps."""
    fig = make_subplots(rows=1, cols=2, subplot_titles=[C.LAYOUT_LABELS[lay] for lay in C.LAYOUTS], horizontal_spacing=0.1, shared_yaxes=True)
    for col, layout in enumerate(C.LAYOUTS, start=1):
        sel = [r for r in rows if r["layout"] == layout]
        for k, key in (("shapley", "shapley_in_core"), ("proportional", "proportional_in_core"), ("equal", "equal_in_core")):
            fig.add_trace(go.Scatter(x=[r["n"] for r in sel], y=[100 * r[key] for r in sel], mode="lines+markers", name=E.METHOD_LABELS[k], line=dict(color=METHOD_COLORS[k], width=2.5),
                                     showlegend=col == 1), row=1, col=col)
    fig.update_xaxes(title_text="Spediteure", dtick=1)
    fig.update_yaxes(title_text="Aufteilung im Kern (%)", row=1, col=1)
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h", y=-0.3), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_sampling(rows):
    """Relativer Fehler der Stichproben-Schätzung des Shapley-Werts über der Zahl der Reihenfolgen (beide Achsen logarithmisch), dazu 1/√K."""
    ks = [r["samples"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ks, y=[r["rel_error"] for r in rows], mode="lines+markers", name="Mittlerer Fehler", line=dict(color=GOOD, width=2.5)))
    fig.add_trace(go.Scatter(x=ks, y=[r["rel_error_max"] for r in rows], mode="lines+markers", name="Größter Fehler", line=dict(color=BAD, width=2, dash="dash")))
    ref = rows[0]["rel_error"] * np.sqrt(ks[0] / np.asarray(ks))
    fig.add_trace(go.Scatter(x=ks, y=ref, mode="lines", name="1/√K (Vergleich)", line=dict(color=REF_COLOR, dash="dot")))
    fig.update_xaxes(title_text="Zufällige Reihenfolgen K", type="log")
    fig.update_yaxes(title_text="Relativer Fehler (Summe der Abweichungen / Summe der Anteile)", type="log")
    return _base(fig, 320)

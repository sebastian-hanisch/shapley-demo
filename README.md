# 🤝 Shapley-Wert – wie Spediteure die Kosten einer gemeinsamen Tour fair teilen

**[→ Demo live ausprobieren](https://sebastianhanisch-shapley-demo.streamlit.app/)**

Siebtes Stück der **Spieltheorie-&-Mechanism-Design-Linie** der "Konzepte"-Reihe im Portfolio von
[Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning, und **Wurzel des zweiten Astes (kooperative Spieltheorie)**. Die bisherigen Stücke
([nash-demo](https://sebastianhanisch-nash-demo.streamlit.app/) bis [stackelberg-demo](https://sebastianhanisch-stackelberg-demo.streamlit.app/)) betrachteten eigennützige Lkw;
hier schließen sich Spediteure freiwillig zusammen und teilen die Kosten ihrer gemeinsamen Tour.

## Warum dieses Problem

Mehrere Spediteure beliefern je einen Kunden ab demselben Depot. Fährt jeder allein, entstehen viele lange Touren; fahren sie **gemeinsam eine Tour**, sinkt die Gesamtstrecke erheblich. Die Frage der kooperativen
Spieltheorie: **wie wird die Gesamtstrecke fair auf die Spediteure verteilt?** Der **Shapley-Wert** (Shapley 1953) rechnet jedem Spediteur den Durchschnitt seiner Grenzkosten über alle Reihenfolgen an,
in denen die Spediteure der Kooperation beitreten.

## Modell

**Vehikel B "Spediteurs-Kooperation"** (`sh_scenario.py`): $n$ Spediteure mit je einem Kunden-Stopp in einem 100 × 100 km großen Gebiet (gleichmäßig verteilt oder um zwei Ballungszentren), gemeinsames Depot
in der Mitte, euklidische Entfernungen, keine Kapazitäten.

**Kostenspiel** (`sh_game.py`): Koalitionswert $c(S)$ = Länge der kürzesten Rundtour ab Depot durch alle Stopps der Koalition $S$ (Traveling-Salesman-Spiel, Potters/Curiel/Tijs 1992). **Held-Karp** liefert
alle $2^n$ Werte in einer Rechnung. Aufteilungen: **Shapley-Wert** $\phi_i = \sum_{S \subseteq N \setminus \{i\}} \frac{|S|!\,(n-|S|-1)!}{n!}\,[c(S \cup \{i\}) - c(S)]$, zum Vergleich **proportional** zu den Kosten der
Alleinfahrt und **gleiche Ersparnis** für alle.

**Stabilität (Kern):** eine Aufteilung ist stabil, wenn keine Gruppe von Spediteuren allein günstiger führe, als sie zusammen zahlt ($\sum_{i \in S} x_i \le c(S)$ für alle $2^n - 1$ Gruppen).

## Methodik

- Alles ist exakt: Held-Karp gegen Brute-Force über alle Permutationen (jede Koalition bei 6 Stopps), Shapley-Wert gegen die Permutations-Definition, Kern-Prüfung gegen eine Schleife über alle Koalitionen.
- Die **vier Axiome** sind einzeln getestet: Effizienz, Symmetrie (zwei Spediteure am selben Ort zahlen gleich), Nullspieler (ein Stopp im Depot zahlt nichts), Additivität.
- **Handrechnung** im 3-Spieler-Spiel (Koalitionswerte 4, 6, 8, 9, 10, 11, 12): 2,5 / 4,0 / 5,5.
- **Stichprobe** (Experiment 3): Schätzung des Shapley-Werts als Mittel über zufällige Reihenfolgen (Castro/Gómez/Tejada 2009), mit festen Seeds.
- **Literatur** (per Recherche geprüft, nicht nachgebaut): Shapley 1953 ("A value for n-person games"), Potters/Curiel/Tijs 1992 ("Traveling salesman games": der Kern kann leer sein, auch bei Dreiecksungleichung).

## Befunde (gemessen, keine Behauptungen)

| Frage | Befund | Test |
|---|---|---|
| Wie viel spart die gemeinsame Tour? | Standardinstanz (8 Spediteure, Seed 35): alle allein 797,9 km, gemeinsam 328,7 km – 58,8 % Ersparnis. Im Mittel 55 % (gleichmäßig verteilte Stopps) bzw. 68 % (zwei Ballungszentren) bei 8 Spediteuren. | `test_standardfall_numbers`, `test_stability_experiment_numbers` |
| Ist der Shapley-Wert stabil? | Meist: bei 8 Spediteuren liegt er in 85 % (gleichmäßig) bzw. 92 % (Ballung) von je 60 Instanzen im Kern. Wo er es nicht ist, ist die Überschreitung klein: im Mittel über alle Instanzen 0,1 % der Gesamtstrecke, im Einzelfall höchstens 2,2 %. Blockierende Koalitionen: im Mittel 0,2 je Instanz. | `test_stability_experiment_numbers` |
| Sind die naheliegenden Aufteilungen stabil? | Kaum: die proportionale Aufteilung liegt nur in 10 % (gleichmäßig) bzw. 27 % (Ballung) der Instanzen im Kern, die gleiche Ersparnis für alle in keiner. Blockierende Koalitionen im Mittel 5,5 bzw. 14,4 je Instanz (gleichmäßig). Das sagt nur etwas über diese Vehikelfamilie. | dito |
| Ein Beispiel, in dem Shapley nicht im Kern liegt | Vehikel Seed 12 (8 Spediteure): die Spediteure 1 bis 7 zahlen zusammen 2,95 km mehr, als sie allein führen; gemeinsam sind es 310,4 km. Ob der Kern selbst leer ist, klärt das nächste Stück. | `test_shapley_nicht_im_kern_numbers` |
| Bleibt das bei mehr Spediteuren so? | Nein: bei 4 Spediteuren ist der Shapley-Wert in 100 % der (gleichmäßig verteilten) Instanzen stabil, bei 10 in 80 %; die proportionale Aufteilung fällt von 42 % auf 5 %. Die Ersparnis wächst von 34 % auf 61 %. | `test_scaling_experiment_numbers` |
| Geht es ohne alle Reihenfolgen? | Stichprobe bei 10 Spediteuren (1 024 Koalitionen gegen 3 628 800 Reihenfolgen): mit 10 zufälligen Reihenfolgen liegt der relative Fehler im Mittel bei 19 %, mit 100 bei 6,1 %, mit 1000 bei 2,0 % (etwa $1/\sqrt K$). Die Stabilitätsaussage kippt bei 10 Reihenfolgen in 14 % der Läufe, bei 100 in 1,0 %, bei 1000 in keinem. | `test_sampling_experiment_numbers` |
| Handrechnung | Drei Spediteure der Standardinstanz (Seed 35): Shapley-Anteile 17,9 / 123,7 / 113,7 km von zusammen 255,4 km (10,9 % Ersparnis), alle 6 Reihenfolgen und Koalitionswerte in einer Tabelle. | `test_drei_spediteure_numbers` |

## Ehrliche Grenzen

| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Jeder Spediteur hat genau einen Stopp und es gibt keine Kapazität** | Mit Kapazitäten und mehreren Stopps je Spediteur ist der Koalitionswert ein Tourenplanungsproblem (VRP) und die Superadditivität gilt nicht mehr automatisch. | [VRP-Demos](https://sebastianhanisch.net/demos.html) |
| **Die Kosten einer Koalition sind die kürzeste Rundtour** | In der Praxis kommen Zeitfenster, Beladung und Fahrerzeiten dazu; jeder Koalitionswert wird ein schweres Optimierungsproblem. Held-Karp trägt nur bis etwa 15 Stopps. | Stichprobe (siehe oben) |
| **Shapley ist die gerechte Aufteilung** | Shapley erfüllt vier Axiome, aber nicht immer die Stabilitätsbedingung des Kerns. | Kern und Nukleolus (nächstes Stück) |
| **Alle Spediteure wollen kooperieren** | Der Wert der Kooperation hängt von den Koalitionen ab, die sich stattdessen bilden könnten; Verhandlung und Vertrauen liegen außerhalb dieses Modells. | – |
| **Die Kostenaufteilung wird von außen gesetzt** | Ob Spediteure ihre Kosten ehrlich melden, ist eine Frage des Mechanism Designs. | Kostenteilung mit Anreizen |

Die Messreihen gelten für diese Vehikelfamilie (ein Stopp je Spediteur, euklidisch, ohne Kapazität) und die genannten Instanzgrößen (bis 10 Spediteure); die Stichprobe hat feste Seeds. Die Stopps sind in der Größe des Kostenanteils gezeichnet, nicht maßstäblich.

Verwandt: [maut-demo](https://sebastianhanisch-maut-demo.streamlit.app/) (Preise, die Externalitäten einpreisen – der Zwilling der Kostenteilung), [stackelberg-demo](https://sebastianhanisch-stackelberg-demo.streamlit.app/) (Ast A).

## Tests

Pytest-Suite (`pytest tests/ -v`): Held-Karp gegen Brute-Force (jede Koalition), rekonstruierte Tour hat die optimale Länge, Superadditivität, Shapley per Handrechnung (3 Spieler) und gegen die Permutations-Definition,
alle vier Axiome, Kern-Prüfung und blockierende Koalitionen gegen eine Schleife, Kern per Handrechnung, Vergleichs-Aufteilungen per Handrechnung, Stichprobe (reproduzierbar, konvergent), Vehikel
(Reproduzierbarkeit, Metrik, Ballung), AppTest-Rauchtests (jedes Preset, Handrechnung-Auswahl, Permalink-Grenzen, drei Experimente auf Abruf) und `test_claims.py` (jede Zahl aus diesem README).

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Einstiegspunkt |
| `sh_constants.py` | Vehikel-Konstanten, Regler-Grenzen, Experiment-Seeds |
| `sh_presets.py` | Permalink/Presets-Mechanik |
| `sh_scenario.py` | Vehikel B (Depot, Stopps, Entfernungen) |
| `sh_game.py` | Held-Karp, Shapley, Kern-Prüfung, Vergleichs-Aufteilungen, Stichprobe |
| `sh_evaluation.py` | Analyse einer Instanz, drei Experimente |
| `sh_visualization.py` | Plotly-Abbildungen |

## Bewusst nicht umgesetzt

- Der Kern selbst (LP), seine Leere und der Nukleolus: nächstes Stück der Linie.
- Mehr als 12 Spediteure (Held-Karp in Python) und Kapazitäten/Mehr-Stopp-Spediteure.
- Ein PDF-Export – wie bei den anderen Konzepte-Demos dieses Portfolios nicht Teil der Linie.

## Lokal ausführen

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt
streamlit run app.py
```

Gebaut mit Streamlit, Plotly und numpy.

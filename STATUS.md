# Status og plan videre – SaR-Robot

**Dato:** 2026-11-05  
**Utgangspunkt:** Rapporten bygger på koden på `main` (commit `b9412bb`, 3. november). «Ferdig» betyr at det er kodet. Repoet har ingen logg fra kjøring av hele systemet, så det som ikke er merket som testet, må regnes som utestet i Gazebo. Fordelingen følger ukeplanen (`message.txt`):

| Person | Ansvar |
|---|---|
| **A** | Bevegelse |
| **B** | Kart og planlegging |
| **C** | Markører og koordinering |
| **D** | Integrasjon og test |

---

## 1. Kort oppsummert

- ✅ Hele kjeden er kodet: `/map` → `map_node` → `coverage_node` → `robot_controller` (A* og stifølging) → `cmd_vel`. Markørene går fra `marker_reporter` til scoring og `coordinator`.
- ❌ Storbrann-logikken er ikke laget. Uten den stopper ikke klokka, og maks poeng er 500 (se «Hvordan poeng gis»).
- ❌ `README.MD` er tom (krav for innlevering), og `testlogg.md` finnes ikke.
- ❓ Hele systemet er ikke dokumentert kjørt i w1–w5.

Tidligere branches er merget. `CONTRACT.md` er oppdatert til v0.3.

---

## 2. Per person

Tegnforklaring: ✅ ferdig · 🟡 delvis · ❌ ikke gjort · ❓ må sjekkes

### A – Bevegelse

**Gjort**
- ✅ `WallFollower` som egen klasse uten ROS, med parameter `follow_left` og timeout på `SVING_MOT`
- ✅ `PathFollower` som egen klasse uten ROS
- ✅ `robot_controller`: `FOLLOW_PATH` etter `coverage_path`, med A* mellom hvert punkt
- ✅ Veggfølging til ruta kommer, når ruta er blokkert og når den er ferdig. Et punkt hoppes over etter `max_blocked` blokkeringer.
- ✅ `RobotState` på `/robot_states`, med posisjon i `map` via tf2

**Neste, i denne rekkefølgen**
1. ❓ Kjøre w1 og w2 i 10 minutter og skrive ned hvor robotene setter seg fast
2. ❌ En måte å gi roboten et mål på, så C kan sende den til storbrannen. Målet må avbryte dekningsruta. **C trenger svar:** C foreslår `/tb3_0/goal` og `/tb3_1/goal` med `geometry_msgs/PoseStamped`.
3. ❌ Se seg rundt ved hvert punkt (issue #14), hvis testene viser at kameraet går glipp av markører

**Ferdig når:** begge robotene kjører hele dekningsruta i w1 uten å treffe vegger eller stå fast, og kan sendes til et mål.  
**Avhengig av:** B (rute og kart), C (avtale om måltopic).

---

### B – Kart og planlegging

**Gjort**
- ✅ `MapGrid` med `inflate()` og `downsample()`
- ✅ `map_node` publiserer `/inflated_map`
- ✅ A* i `planner.py`, med `planner_test_node` for `/clicked_point` → `/planned_path` i RViz
- ✅ `coverage.py` og `coverage_node`: punkter fordelt på de to robotene, publisert på `/tb3_X/coverage_path`

**Neste**
1. ❓ Sjekke at dekningspunktene dekker kartet i alle fem verdener
2. ❓ Sjekke at `spacing` (1,5 m) er tett nok til at kameraet ser alle markørene

**Ferdig når:** utforskingsmålene dekker kartet i w1–w5.  
**Leverer til:** A (kart og rute).

---

### C – Markører og koordinering

**Gjort**
- ✅ `marker_reporter` (én per robot): regner om posisjonen til `map` med bildets tidspunkt, sender til scoring og publiserer `MarkerFound`
- ✅ Hopper over markører som allerede er godkjent, venter 5 s før nytt forsøk og ignorerer markører over 3 m unna
- ✅ `coordinator` (global node): logger `/markers_found` og `/robot_states`, publiserer `/known_markers` hvert sekund
- ✅ Testet ifølge forrige versjon av denne rapporten (uten dato): tb3_1 fikk markør 0 godkjent (600 → 700), coordinatoren logget det, og tb3_0 sendte ikke samme markør på nytt

**Neste**
1. ❌ Storbrann (markør 4): når den er godkjent, avbryter coordinatoren søket og sender **begge** robotene dit (gir +300 når begge er innenfor 2 m)
2. ❌ Logge tid fra start til hver markør, så D kan føre det i testloggen

**Testtips:** scoring godkjenner hver markør bare én gang, så start scoring på nytt mellom hver test.

**Ferdig når:** storbrann-bonusen kommer i minst 4 av 5 verdener.  
**Avhengig av:** A (måltopic).

---

### D – Integrasjon og test

**Gjort**
- ✅ `MarkerFound.msg`, `RobotState.msg`, `KnownMarkers.msg`
- ✅ Avhengigheter i `sar_robot/package.xml`, og `__pycache__`/`.pyc` er fjernet fra git
- ✅ `sar.launch.py` med `world:=1..5`: starter verden, `coordinator`, `map_node`, `coverage_node`, og `marker_reporter` og `robot_controller` for hver robot
- ✅ `CONTRACT.md` v0.3

**Neste**
1. ❌ Kjøre w1–w5 og lage `testlogg.md` med dato, commit, verden, poeng, markører funnet, storbrann ja/nei og kommentar
2. ❌ Skrive README med oppsett og kjøring
3. ❌ Bestemme om `sar.launch.py` skal starte scoring. I dag må den startes for seg, med `ros2 run scoring scoring`. `robot_controller` begynner å kjøre med en gang, altså før scoring er i gang, så rekkefølgen må avklares før dere tar tiden.
4. ❌ Slå på branch protection på main. Sjekket 2026-11-05: main er ikke beskyttet, og de to siste kodecommitene (`3c338b9`, `b9412bb`) ser ut til å være pushet rett dit.
5. ❌ Rydde i issues: alle 29 åpne er fra 6. oktober, og flere ser ferdige ut (for eksempel #8 og #12)
6. ❓ Få svar på spørsmålene til faglærer (issue #4)
7. ❌ Fylle ut `description` og `license` i `sar_robot/setup.py` (står som TODO)

**Ferdig når:** `ros2 launch sar_robot sar.launch.py world:=3` starter alt, og testloggen viser forbedring fra første kjøring.

---

## 3. Tester

Sjekket 2026-11-05 uten ROS, i et eget Python-miljø med numpy og scipy:

- ✅ `test_wall_follower.py`, `test_path_follower.py`, `test_map_grid.py`, `test_planner.py` og `test_coverage.py`: alle 24 består
- ❓ `test_flake8.py`, `test_pep257.py` og `test_copyright.py`: ikke kjørt. Kjør dem med `colcon test` i ROS-miljøet.
- ❓ Nodene er ikke kjørt, fordi ROS ikke var installert på maskinen.

---

## 4. Forslag til rekkefølge

| Rekkefølge | Hvem | Hva |
|---|---|---|
| 1 | A + D | Full kjøring på w1, første tall i testloggen |
| 2 | A + B | Rette det som dukker opp: fastkjøring, punkter uten rute, markører som ikke blir sett |
| 3 | A + C | Avtale måltopic, og lage det i `robot_controller` og `coordinator` |
| 4 | C | Teste storbrann i alle verdener |
| 5 | D | README, og kjøre w1–w5 etter hver merge til main |
| 6 | Alle | Forberede presentasjon og demo-video (issue #27, #28, #30). Hver person forklarer koden sin. |

### Hvordan poeng gis (fra `scoring.py`)

- Start på 600, minus 1 per sekund
- +100 per godkjent markør (ID 0–4)
- +300 når markør 4 er rapportert og begge robotene er innenfor 2 m av den
- Klokka stopper først når begge robotene har vært ved markør 4 og alle fem markørene er rapportert. Ellers går den til 600 s, og sluttpoengsummen blir bare markørpoengene (maks 500).

Det viktigste er derfor å samle begge robotene ved storbrannen (A + C), og å finne alle markørene raskt (A + B). Uten samlingen teller ikke tiden.

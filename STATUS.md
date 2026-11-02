# Status og plan videre – SaR-Robot

**Dato:** 2026-10-19  
**Utgangspunkt:** Rapporten forutsetter at alt som ligger på branchene er tatt inn i `main`. Fordelingen følger ukeplanen (`message.txt`):

| Person | Ansvar |
|---|---|
| **A** | Bevegelse |
| **B** | Kart og planlegging |
| **C** | Markører og koordinering |
| **D** | Integrasjon og test |

---

## 1. Dette må merges til main

| Rekkefølge | Hva | Eier | Merknad |
|---|---|---|---|
| 1 | `origin/meldingstyper` | D | **main bygger ikke uten denne.** `coordinator.py` og `marker_reporter.py` bruker meldingstypene. |
| 2 | `origin/feature/map-grid` | B | Rett først `python3-numphy` → `python3-numpy` i `sar_robot/package.xml`. |
| 3 | Lokal endring i `coordinator.py` | C | Fjerner bare en kommentar. Bør forkastes (`git restore`). |
| 4 | Fjern committede `__pycache__`/`.pyc` | D | `git rm -r --cached` etter at `.gitignore` fra punkt 2 er inne. |

Begge branchene merger uten konflikter mot main. Merges via pull request, og en annen person godkjenner (som avtalt).

---

## 2. Per person

Tegnforklaring: ✅ ferdig · 🟡 delvis · ❌ ikke gjort

### A – Bevegelse

**Gjort**
- ✅ Veggfølgeren er ferdig (`wall_follower.py`)
  - Tilstandsmaskin og P-regulator, parameter `follow_left`
  - Relative topicnavn (`scan`, `odom`, `cmd_vel`), så noden virker i namespace
  - Timeout på `SVING_MOT`, så roboten ikke går i ring

**Neste, i denne rekkefølgen**
1. ❌ Publisere `RobotState` på `/robot_states`, med posisjon i `map` via tf2 (`lookup_transform('map', 'tb3_X/base_footprint')`)
2. ❌ Skille ut en ren `WallFollower`-klasse (uten ROS) og lage noden `robot_controller.py`
3. ❌ Modus `FOLLOW_PATH` i `robot_controller`: tar inn `nav_msgs/Path` fra B og kjører etter punktene. Fall tilbake til veggfølging hvis ruta er blokkert.

**Også igjen**
- ❌ Kjøre 10 min på w1 og w2 og skrive ned hvor robotene setter seg fast
- ❌ En måte å gi roboten et mål på, så C kan sende den til storbrannen. **C trenger svar:** C foreslår `/tb3_0/goal` og `/tb3_1/goal` med `geometry_msgs/PoseStamped`.

**Husk:** noder i namespace som bruker TF må ha `remappings=[('tf', '/tf'), ('tf_static', '/tf_static')]` i launch-fila (se C).

**Ferdig når:** du klikker et punkt i RViz, og roboten kjører dit uten å treffe vegger.  
**Avhengig av:** B (rute), D (meldingstyper merget).

---

### B – Kart og planlegging

**Gjort** (på `feature/map-grid`)
- ✅ `MapGrid` med `world_to_grid`, `grid_to_world`, `is_free`
- ✅ `inflate()`: buffer rundt veggene, ukjent regnes som vegg
- ✅ 4 enhetstester

**Gjenstår fra uke 1**
- ❌ Rette numpy-skrivefeilen og åpne PR (se del 1)
- ❌ Node som leser `/map` (QoS TRANSIENT_LOCAL) og publiserer `/inflated_map`
- ❌ Vise kartet med buffer i RViz

**Neste (uke 2)**
1. A*: `plan(start, mål) → [(x, y), ...]`, med enhetstester som for `MapGrid`
2. Test med `/clicked_point` → `/planned_path` i RViz
3. Utforskingsmål: lag en liste med punkter hver robot skal innom, så hele kartet blir dekket. Del kartet mellom de to robotene. (`coverage_node` deler allerede labyrinten i to områder, ifølge C.)

**Ferdig når:** `/planned_path` vises i RViz for et klikket punkt, og utforskingsmålene dekker kartet i w1–w5.  
**Leverer til:** A (rute), C (utforskingsmål).

---

### C – Markører og koordinering

**Gjort** (markørdelen er ferdig og ligger i main)
- ✅ `marker_reporter` (én per robot): regner om posisjonen til `map` med en gang markøren sees, sender til scoring (`/set_marker_position`) og publiserer `MarkerFound` på `/markers_found`
- ✅ Hopper over markører som allerede er godkjent (fra `/known_markers`)
- ✅ Venter 5 s etter en avvisning før neste forsøk, og sender ikke markører som er over 3 m unna
- ✅ `coordinator` (global node): logger `/markers_found` og `/robot_states`, publiserer `/known_markers` hvert sekund
- ✅ TF-remapping i `sar.launch.py`: `remappings=[('tf', '/tf'), ('tf_static', '/tf_static')]`. Uten dette finner ikke noder i namespace TF i Foxy.
- ✅ Testet: tb3_1 fikk markør 0 godkjent (600 → 700), coordinatoren logget det, og tb3_0 sendte ikke samme markør på nytt

**Fortsatt i koden på `origin/main`** (sjekket 2026-11-02)
- ❌ `lookup_transform` bruker `Time()` i stedet for `msg.header.stamp`
- ❌ `clbk_known` overskriver `self.known` (`self.known = set(...)` i stedet for `|=`)
- ❌ `future.result()` sjekkes ikke for `None` i `on_response`

**Neste**
1. ❌ Storbrann (markør 4): når den er godkjent, avbryter coordinatoren søket og sender **begge** robotene dit (gir +300 når begge er innenfor 2 m)
2. ❌ Logge tid fra start til hver markør, så D kan føre det i testloggen

Å fordele hvor robotene leter er dekket av B sin `coverage_node`.

**Testtips:** scoring godkjenner hver markør bare én gang, så start scoring på nytt mellom hver test.

**Ferdig når:** storbrann-bonusen kommer i minst 4 av 5 verdener.  
**Avhengig av:** A (måltopic og `RobotState`).

---

### D – Integrasjon og test

**Gjort** (på `meldingstyper`)
- ✅ `MarkerFound.msg`, `RobotState.msg`, `KnownMarkers.msg`, `rosidl_generate_interfaces`, slettet `test.*`

**Gjenstår fra uke 1** (dette er det viktigste i hele prosjektet nå)
1. ❌ Merge `meldingstyper` og rydde `__pycache__` (se del 1)
2. ❌ Legge inn avhengighetene som mangler i `sar_robot/package.xml`: `geometry_msgs`, `sensor_msgs`, `std_srvs`, `tf2_ros`, `tf2_geometry_msgs`, `ros2_aruco_interfaces`, `scoring_interfaces`
3. ❌ `sar.launch.py` med `world:=1..5`: inkluderer `rescue_robots_w{N}.launch.py` og starter `wall_follower` og `marker_reporter` i `tb3_0` (`follow_left:=false`) og `tb3_1` (`follow_left:=true`), samt `coordinator`
4. ❌ `testlogg.md` med første poengtall fra w1–w5 (bare veggfølging)
5. ❌ README (`README.MD` er tom, og det er et krav for innlevering)
6. ❌ `CONTRACT.md` v0.2. Den beskriver fortsatt den gamle arkitekturen (`mission_manager`, `Victim.msg` osv.) og må skrives om til de faktiske nodene og topicene.
7. ❓ Branch protection på main. Sjekk på GitHub: de to siste commitene ser ut til å være pushet rett til main.

**Neste (uke 2)**
- Oppdatere `sar.launch.py` når nye noder kommer (`robot_controller`, kartnoden), med parametre i en YAML-fil
- Kjøre w1–w5 etter hver merge til main og føre resultatet i testloggen

**Ferdig når:** `ros2 launch sar_robot sar.launch.py world:=3` starter alt, og testloggen viser forbedring fra første kjøring.

---

## 3. Rekkefølge og møtepunkter

| Når | Hvem | Hva |
|---|---|---|
| Nå | D | Merger `meldingstyper`, rydder, legger inn avhengigheter |
| Nå | B | Retter numpy, åpner PR for `feature/map-grid` |
| Nå | C | Storbrann i coordinatoren, retter de tre feilene i `marker_reporter` |
| Nå | A | Publiserer `RobotState`, deretter deler opp i klasse og node |
| Etter 1–2 dager | D | `sar.launch.py` virker, første testlogg på w1–w5 |
| Midt i uke 2 | A + B | Kobler A* til `FOLLOW_PATH` |
| Midt i uke 2 | C | Tester storbrann med teleop |
| Slutten av uke 2 | Alle | Full kjøring på w1–w5. Hver person forklarer koden sin (trening til muntlig). D viser testloggen. |

### Hvordan poeng gis (fra `scoring.py`)

- Start på 600, minus 1 per sekund
- +100 per godkjent markør (ID 0–4)
- +300 når markør 4 er rapportert og begge robotene er innenfor 2 m av den

Det viktigste er derfor å finne alle markørene raskt (A + B) og samle begge robotene ved storbrannen (C).

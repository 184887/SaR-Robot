# Disposisjon for rapporten – SaR-Robot

**Dato:** 2026-11-10  
**Merk:** Jeg fant ingen mal eller krav til rapporten i repoet. Sjekk struktur og lengde mot kurssiden, og endre disposisjonen etter det.

Tegnforklaring: ✍️ kan skrives nå · ⏳ venter på testkjøringer

Ansvar følger rollene: **A** Bevegelse · **B** Kart og planlegging · **C** Markører og koordinering · **D** Integrasjon og test

---

## 1. Innledning ✍️ (alle)
- Søk og redning med to TurtleBot3 i Gazebo
- Mål: finne fem ArUco-markører raskt og samle begge robotene ved storbrannen (markør 4)
- Kort om hva rapporten inneholder

## 2. Oppgave og poengsystem ✍️ (D)
- Verdenene w1–w5, to roboter (`tb3_0`, `tb3_1`), kartet er gitt på `/map`
- Hvordan poeng gis (fra `scoring.py`):
  - start på 600, minus 1 per sekund
  - +100 per godkjent markør
  - +300 når begge robotene er innenfor 2 m av markør 4
  - klokka stopper bare når alt er gjort, ellers er maks 500
- Hva dette betyr for strategien: storbrannen er viktigst, deretter fart

## 3. Systemarkitektur ✍️ (D)
- Figur over nodene og topicene:
  - `/map` → `map_node` → `/inflated_map` → `coverage_node` → `/tb3_X/coverage_path` → `robot_controller` → `cmd_vel`
  - `aruco_node` → `marker_reporter` → scoring og `/markers_found` → `coordinator` → `/known_markers` og `/tb3_X/goal`
- Hvilke noder som går per robot (namespace), og hvilke som er globale
- Meldingstypene `MarkerFound`, `RobotState` og `KnownMarkers` (fra `CONTRACT.md`)
- Designvalg: logikken ligger i klasser uten ROS (`WallFollower`, `PathFollower`, `MapGrid`, A*, `coverage`), så den kan enhetstestes
- Oppstart med `sar.launch.py world:=N`

## 4. Kart og planlegging ✍️ (B)
### 4.1 Kartbehandling
- `MapGrid`: `/map` med QoS TRANSIENT_LOCAL til numpy, `world_to_grid` og `grid_to_world`
- Buffer rundt veggene (`inflate`, robotradius pluss margin) og nedskalering (`downsample`, 5 cm-ruter)
### 4.2 A*
- Heuristikk, nabolag og hvordan ruta gjøres om til punkter i `map`
- Figur: rute i RViz fra `planner_test_node`
### 4.3 Dekningspunkter
- Hvordan punktene legges ut (`spacing` 1,5 m) og fordeles på de to robotene
- Begrunnelse for avstanden: kameraets rekkevidde, og at markører over 3 m ignoreres

## 5. Bevegelse ✍️ (A)
### 5.1 Veggfølger
- Lidaren delt i soner, minste gyldige verdi per sone
- Tilstandsmaskin med figur: `FINN_VEGG`, `SVING_BORT`, `FOLLOW_WALL`, `SVING_MOT`, og når den bytter
- Timeout på `SVING_MOT`, og hvorfor den trengs
- `follow_left`: tb3_0 følger høyre vegg og tb3_1 venstre
- Utgangspunkt: Bug2-labben
### 5.2 Stifølger
- P-regulator på vinkelfeil, `v_max`, `Kp` og `tolerance`
### 5.3 robot_controller
- Modusene, med figur: følge dekningsruta, veggfølging, gå til mål, `AT_GOAL`
- A* mellom hvert dekningspunkt
- Blokkert rute: `blocked_dist`, `blocked_time`, og `max_blocked` før et punkt hoppes over
- Mål på `/tb3_X/goal` avbryter dekningsruta, med `goal_tolerance` 1 m (scoring krever 2 m)
- Posisjon i `map` via tf2, fordi odom starter i null for hver robot
- `RobotState` på `/robot_states`

## 6. Markører og koordinering ✍️ (C)
### 6.1 marker_reporter
- Posisjonen regnes om til `map` med bildets tidspunkt
- Unngå dobbel rapportering: hopper over godkjente ID-er, venter 5 s før nytt forsøk, ignorerer markører over 3 m unna
- Problemet med gammel posisjon fra `marker_pose`, og hvordan det ble løst
### 6.2 coordinator
- Logger markører og robotstatus, publiserer `/known_markers`
- Storbrann: når markør 4 er godkjent, sendes begge robotene dit

## 7. Testing ✍️ / ⏳ (D, alle)
- ✍️ Enhetstester: hva de dekker (24 tester for veggfølger, stifølger, kart, A* og dekning)
- ✍️ Testmetode: start scoring på nytt mellom hver kjøring, kolonnene i `testlogg.md`
- ⏳ Integrasjonstester i w1–w5

## 8. Resultater ⏳ (D)
- Tabell fra `testlogg.md`: verden, poeng, markører funnet, storbrann ja/nei, tid
- Første kjøring mot siste, for å vise forbedring
- Skjermbilder fra RViz og Gazebo

## 9. Diskusjon ⏳ (alle)
- Hvor robotene satte seg fast, og hva som ble gjort med det (A)
- Om dekningspunktene var tette nok til å se alle markørene (B)
- Avviste rapporter og nøyaktighet på markørposisjon (C)
- Hva som begrenset poengsummen mest
- Hva dere ville gjort med mer tid: se seg rundt ved hvert punkt (issue #14), fartsoptimalisering (#26), tredje robot (#25)

## 10. Samarbeid og arbeidsmåte ✍️ (alle)
- Rollefordeling A–D
- Git: branches, pull requests, `CONTRACT.md` som avtale mellom delene
- Hva som fungerte, og hva som ikke gjorde det (for eksempel at main ikke var beskyttet)

## 11. Konklusjon ⏳ (alle)

## Vedlegg
- Hvordan systemet bygges og kjøres (kan hentes fra README)
- `CONTRACT.md`
- Full testlogg

---

## Figurer å lage
| Figur | Hvem | Når |
|---|---|---|
| Node- og topicoversikt | D | nå |
| Tilstandsmaskin for veggfølgeren | A | nå |
| Modusene i `robot_controller` | A | nå |
| Kart med buffer og A*-rute i RViz | B | nå |
| Dekningspunkter for hver robot | B | nå |
| Skjermbilder fra kjøring i Gazebo | alle | etter testing |

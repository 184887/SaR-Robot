# SaR-Robot

Søk og redning med to TurtleBot3-roboter (tb3_0 og tb3_1) i Gazebo. Semesterprosjekt i DAT160 Intelligente roboter, HVL, høsten 2026.

Robotene leter etter fem ArUco-markører, rapporterer posisjonen deres til scoring og møtes ved storbrannen (markør 4). Navigasjonen er laget av oss selv: A* på kartet, en stifølger og en veggfølger. Vi bruker ikke Nav2.

Video: [legg inn lenke]


## Innhold

| Mappe | Hva |
|---|---|
| sar_robot | Vår kode: nodene, launch-fila og enhetstester |
| sar_robot_interface | Våre meldingstyper: MarkerFound, RobotState og KnownMarkers |
| kurs | Pakker fra kurset og andre, se «Kode fra andre» under |
| figurer | Figurer til rapporten |
| CONTRACT.md | Hvilke topics, services og meldingstyper nodene bruker |
| testlogg.md | Resultater fra kjøringer i w1–w5 |


## Oppsett

Krever Ubuntu med ROS 2 og Gazebo, satt opp som i kurset.

1. Lag et workspace og klon repoet inn i src:

   ```bash
   mkdir -p ~/ros2_ws/src
   cd ~/ros2_ws/src
   git clone https://github.com/184887/SaR-Robot.git
   ```

2. Installer Python-pakkene:

   ```bash
   sudo apt install python3-numpy python3-scipy
   ```

3. Gazebo må finne modellene til verdenene. Kopier de som mangler i ~/.gazebo/models:

   ```bash
   mkdir -p ~/.gazebo/models
   cp -r ~/ros2_ws/src/SaR-Robot/kurs/multi_robot_challenge_23/models/* ~/.gazebo/models/
   ```

4. Bygg:

   ```bash
   cd ~/ros2_ws
   colcon build
   source install/setup.bash
   ```

   Kjør `source install/setup.bash` i hver ny terminal.


## Kjøring

Scoring er ikke med i launch-fila og må startes for seg. Start den først, så poengene telles fra robotene begynner å kjøre.

Terminal 1:

```bash
ros2 run scoring scoring
```

Terminal 2 (world kan være 1 til 5):

```bash
ros2 launch sar_robot sar.launch.py world:=1
```

Launch-fila starter verdenen fra multi_robot_challenge_23 (Gazebo, kart, aruco_node og marker_recognition for begge robotene) og disse nodene våre:

| Node | Antall | Hva den gjør |
|---|---|---|
| map_node | 1 | Gjør veggene i kartet 0,25 m tykkere og publiserer /inflated_map |
| coverage_node | 1 | Lager en rute med punkter som dekker kartet, og deler den mellom robotene |
| robot_controller | 1 per robot | Kjører ruta med A* mellom punktene, følger veggen når ruta er blokkert |
| marker_reporter | 1 per robot | Rapporterer nye markører til scoring |
| coordinator | 1 | Holder oversikt over markørene og sender begge robotene til storbrannen |

Sluttpoengene står på siste linje i terminal 1. Start scoring på nytt før hver kjøring, ellers blir ikke markørene godkjent igjen.

Mer om hvordan nodene snakker sammen står i CONTRACT.md.


## Tester

Enhetstestene dekker veggfølgeren, stifølgeren, kartet, A* og dekningsruta. Klassene har ikke ROS-kode, så testene kan også kjøres uten ROS:

```bash
cd sar_robot
python3 -m pytest test/test_wall_follower.py test/test_path_follower.py test/test_map_grid.py test/test_planner.py test/test_coverage.py
```

Med ROS kjører `colcon test --packages-select sar_robot` alle testene, også flake8 og pep257.


## Kode fra andre

All kode i sar_robot og sar_robot_interface er skrevet av gruppa, med unntak av det som står her.

| Hva | Hvor | Fra | Lisens |
|---|---|---|---|
| multi_robot_challenge_23: verdener, kart, robotmodell, launch-filer og marker_pose.py | kurs/multi_robot_challenge_23 | Kurset (hvlrobotics) | Ikke oppgitt |
| scoring og scoring_interfaces | kurs/multi_robot_scoring | Kurset (hvlrobotics) | Ikke oppgitt |
| ros2_aruco: finner ArUco-markører i kamerabildet | kurs/ros2_aruco | JMU-ROBOTICS-VIVA, versjonen fra github.com/LauEls/ros2_aruco | MIT |
| turtlebot3_manipulation: robotmodell og oppsett | kurs/turtlebot3_manipulation | ROBOTIS | Apache 2.0 |

Dette i vår egen kode bygger på kursmateriell:

- wall_follower.py bygger på veggfølgeren vi laget i Bug2-labben (wallfollower_controller.py). Sonene i lidaren, tilstandene og P-regulatoren er de samme. Nytt er at den er en klasse uten ROS, at den kan følge venstre eller høyre vegg, hysterese på grensene og timeout på SVING_MOT.
- QoS-en for /map (TRANSIENT_LOCAL) i map_node.py er satt opp etter eksempelet på kurssiden om occupancy grid.
- Oppslaget av robotens posisjon i map med tf2 i robot_controller.py er gjort på samme måte som i marker_pose.py fra kurset.
- marker_reporter.py bruker topicene marker_map_pose og marker_id fra marker_pose.py i kurset, og servicen /set_marker_position fra scoring.


## Gruppa

| Rolle | Ansvar | Hvem |
|---|---|---|
| A | Bevegelse: robot_controller, path_follower, wall_follower | Magnus Fondenes |
| B | Kart og planlegging: map_grid, map_node, planner, coverage | Andreas Rindli |
| C | Markører og koordinering: marker_reporter, coordinator | Matias Wolden |
| D | Integrasjon og test: meldingstyper, launch, testlogg | Emil Loynab |

# Kontrakt for SaR-Robot

Versjon 0.3, 5 november 2026.

Her står hvordan nodene våre snakker sammen. Koden ligger i sar_robot og meldingstypene i sar_robot_interface.


## 1. Noder

- coordinator (global): holder oversikt over hvilke markører som er funnet
- marker_reporter (en per robot): rapporterer markører roboten ser til scoring
- robot_controller (en per robot): kjører roboten mellom punktene i ruta, med A* mellom hvert punkt, og sender posisjonen. Følger veggen til ruta kommer, når ruta er blokkert og når den er ferdig
- map_node (global): gjør veggene i kartet tykkere
- coverage_node (global): lager en rute med punkter til hver robot
- planner_test_node (global): bare for å teste A* i RViz, er ikke med i launch-fila

Disse filene er ikke noder, bare klasser som nodene bruker: wall_follower.py, path_follower.py, map_grid.py, planner.py (A*) og coverage.py.

Fra kurset bruker vi scoring (gir poeng), aruco_node (finner markører) og map_server (sender ut kartet). aruco_node og map_server startes av launch-filene til verdenene. scoring er ikke med i sar.launch.py og må startes for seg.

Vi bruker ikke Nav2, navigasjonen lager vi selv.


## 2. Topics

Felles for begge robotene:
- /markers_found (MarkerFound): marker_reporter sender, coordinator leser
- /known_markers (KnownMarkers): coordinator sender hvert sekund, marker_reporter leser
- /robot_states (RobotState): robot_controller sender, coordinator leser
- /map (OccupancyGrid): map_server sender, map_node leser
- /inflated_map (OccupancyGrid): map_node sender, coverage_node og robot_controller leser

For hver robot (tb3_0 og tb3_1):
- coverage_path (Path): coverage_node sender, robot_controller leser
- aruco_markers (ArucoMarkers): aruco_node sender, marker_reporter leser
- scan (LaserScan): roboten sender, robot_controller leser
- cmd_vel (Twist): robot_controller sender, roboten leser

Kartet og rutene sendes bare en gang. Derfor må de leses med samme QoS som de sendes med (MAP_QOS i map_node.py).


## 3. Services

- /set_marker_position (SetMarkerPosition fra scoring_interfaces): scoring er server og marker_reporter er klient. Vi sender marker_id og posisjonen, og får tilbake om den ble godkjent.
- wallfollower_switch (SetBool), en per robot: robot_controller er server. True starter kjøringen og false stopper roboten. Ingen bruker den ennå.


## 4. Meldingstyper

MarkerFound:
- robot_id (string)
- marker_id (int8)
- position (Point)
- accepted (bool)

RobotState:
- robot_id (string)
- x, y og theta (float64)
- state (string), hva roboten holder på med: FOLLOW_PATH når den følger ruta, ellers det veggfølgeren gjør: FINN_VEGG, SVING_BORT, FOLLOW_WALL eller SVING_MOT

KnownMarkers:
- marker_ids (liste med int8)


## 5. Regler vi følger

- Alle posisjoner er i map og i meter.
- robot_id er det samme som namespace, altså tb3_0 eller tb3_1.
- Topics for en robot skrives uten skråstrek foran, så namespace legges på av seg selv. Felles topics skrives med skråstrek foran.
- Noder i namespace som bruker TF må ha remapping av tf og tf_static i launch-fila.


## 6. Parametre

- follow_left i robot_controller: hvilken vegg roboten følger. tb3_0 følger høyre og tb3_1 venstre.
- sving_mot_timeout i robot_controller: sekunder før den gir opp å svinge mot veggen. Standard 7.
- cell_factor i robot_controller: hvor mye kartet skaleres ned før A*. Standard 5, som i coverage_node.
- blocked_dist i robot_controller: er noe nærmere enn dette foran roboten, er ruta blokkert. Standard 0.3 m.
- blocked_time i robot_controller: sekunder den følger veggen før den prøver ruta igjen. Standard 3.
- max_blocked i robot_controller: ganger et punkt kan blokkere før det hoppes over. Standard 2.
- inflation_radius i map_node: hvor mye tykkere veggene blir. Standard 0.25 m.
- spacing i coverage_node: avstand mellom punktene i ruta. Standard 1.5 m.
- cell_factor i coverage_node: hvor mye kartet skaleres ned før A*. Standard 5.


## 7. Endringer

Hvis du endrer et topic, en service eller en meldingstype, oppdater denne fila i samme pull request og skriv det her.

- 0.1 (8 oktober): første utkast
- 0.2 (2 november): skrevet om etter nodene vi faktisk har
- 0.3 (5 november): robot_controller følger coverage_path og leser /inflated_map, state kan være FOLLOW_PATH, nye parametre i robot_controller

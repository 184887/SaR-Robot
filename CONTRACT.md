# Grensesnittkontrakt – SaR-Robot

| | |
|---|---|
| **Versjon** | 0.1 (utkast) |
| **Dato** | 2026-10-08 |
| **Eier** | TODO: navn |
| **Status** | Til diskusjon i gruppa |

Dette dokumentet beskriver hvordan nodene i systemet kommuniserer: topics, services,
actions, meldingstyper og konvensjoner. Alle som lager eller endrer en node skal
følge kontrakten. Selve definisjonene av egne typer ligger i `sar_robot_interface/`,
mens koden ligger i `sar_robot/`.

> Punkter merket **TODO** er antakelser eller plassholdere som må avklares.

---

## 1. Noder og ansvar

| Node | Pakke | Ansvar |
|---|---|---|
| `mission_manager` | `sar_robot` | Styrer oppdraget og tilstandsmaskinen, bestemmer hva roboten gjør |
| `navigation` | `sar_robot` | Kjører roboten til mål og unngår hindringer |
| `victim_detector` | `sar_robot` | Finner mulige personer i kamerabildet og publiserer funn |
| `base_driver` | TODO | Snakker med motorene, tar imot `/cmd_vel` og publiserer odometri |
| `operator_ui` | TODO | Lar operatøren starte, stoppe og følge med på oppdraget |

TODO: Avklar om vi bruker Nav2 til navigasjon eller lager vår egen.

---

## 2. Topics

| Topic | Type | Publiserer | Abonnerer | Frekvens | QoS |
|---|---|---|---|---|---|
| `/scan` | `sensor_msgs/msg/LaserScan` | lidar-driver | `navigation` | 10 Hz | sensor data (best effort) |
| `/camera/image_raw` | `sensor_msgs/msg/Image` | kamera-driver | `victim_detector` | 15 Hz | sensor data (best effort) |
| `/odom` | `nav_msgs/msg/Odometry` | `base_driver` | `navigation`, `mission_manager` | 20 Hz | reliable |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | `navigation` | `base_driver` | 10 Hz | reliable |
| `/victim_detected` | `sar_robot_interface/msg/Victim` | `victim_detector` | `mission_manager`, `operator_ui` | ved funn | reliable |
| `/robot_status` | `sar_robot_interface/msg/RobotStatus` | `mission_manager` | `operator_ui` | 1 Hz | reliable, transient local |
| `/emergency_stop` | `std_msgs/msg/Bool` | `operator_ui` | `base_driver`, `mission_manager` | ved hendelse | reliable, transient local |

Regler:
- Bare `navigation` publiserer på `/cmd_vel`. Andre noder som vil flytte roboten må gå via `navigation`.
- `base_driver` stopper motorene hvis den ikke har fått `/cmd_vel` på 0,5 s (watchdog).

---

## 3. Services

### `/start_search`
- **Type:** `sar_robot_interface/srv/StartSearch`
- **Server:** `mission_manager`
- **Klient:** `operator_ui`
- **Request:** `area_id` (string) – ID for området som skal gjennomsøkes
- **Response:** `success` (bool), `message` (string)
- **Feil:** Returnerer `success=false` hvis roboten ikke er i `IDLE`, eller hvis `area_id` er ukjent.

### `/stop_mission`
- **Type:** `std_srvs/srv/Trigger`
- **Server:** `mission_manager`
- **Klient:** `operator_ui`
- **Oppførsel:** Avbryter pågående oppdrag, stopper roboten og går til `IDLE`.
- **Merk:** Dette er en vanlig stopp. Nødstopp går via `/emergency_stop`, se seksjon 7.

---

## 4. Actions

### `/navigate_to_point`
- **Type:** `sar_robot_interface/action/NavigateToPoint`
- **Server:** `navigation`
- **Klient:** `mission_manager`
- **Goal:** `target` (`geometry_msgs/PoseStamped`), mål i `map`-frame
- **Feedback:** `distance_remaining` (float32, meter)
- **Result:** `success` (bool), `message` (string)
- **Avbrytelse:** Klienten kan avbryte (cancel). Da stopper roboten.
- **Timeout:** TODO: f.eks. 120 s, deretter `success=false`

TODO: Bytt til `nav2_msgs/action/NavigateToPose` hvis vi bruker Nav2.

---

## 5. Egne meldingstyper (`sar_robot_interface`)

### `msg/Victim.msg`
```
std_msgs/Header header        # stamp = tidspunkt for bildet, frame_id = "map"
geometry_msgs/Point position  # estimert posisjon, meter
float32 confidence            # 0.0–1.0
string id                     # unik ID, slik at samme person ikke rapporteres flere ganger
```

### `msg/RobotStatus.msg`
```
std_msgs/Header header
uint8 IDLE=0
uint8 SEARCHING=1
uint8 VICTIM_FOUND=2
uint8 RETURNING=3
uint8 ERROR=4
uint8 state
float32 battery_percent       # 0.0–100.0
uint16 victims_found
string message                # fritekst for operatøren, kan være tom
```

### `srv/StartSearch.srv`
```
string area_id
---
bool success
string message
```

### `action/NavigateToPoint.action`
```
geometry_msgs/PoseStamped target
---
bool success
string message
---
float32 distance_remaining
```

---

## 6. Konvensjoner

- **Enheter:** SI (meter, sekunder, radianer, m/s) i henhold til REP 103.
- **Koordinatsystem:** x fremover, y til venstre, z opp.
- **TF-frames (REP 105):** `map` → `odom` → `base_link` → sensorframes (`laser_link`, `camera_link`).
- **Tidsstempel:** Alle målinger og funn har `header.stamp` satt til tidspunktet målingen ble gjort, ikke tidspunktet meldingen ble sendt.
- **Navngiving:** snake_case for noder, topics, services og parametre, og PascalCase for meldingstyper.
- **Python-kode:** Følger flake8 og pep257 (testene i `sar_robot/test/` må passere).

---

## 7. Tilstander

```
          /start_search
  IDLE ─────────────────► SEARCHING
   ▲                       │      ▲
   │                Victim │      │ funn registrert
   │                       ▼      │
   │                    VICTIM_FOUND
   │                       │
   │   ferdig / /stop_mission
   └──── RETURNING ◄───────┘

  Alle tilstander ──(/emergency_stop eller kritisk feil)──► ERROR
  ERROR ──(manuell reset)──► IDLE
```

| Fra | Til | Utløses av |
|---|---|---|
| `IDLE` | `SEARCHING` | `/start_search` med gyldig område |
| `SEARCHING` | `VICTIM_FOUND` | ny `Victim` med `confidence` ≥ TODO (f.eks. 0.7) |
| `VICTIM_FOUND` | `SEARCHING` | funnet er registrert og rapportert til operatøren |
| `SEARCHING` | `RETURNING` | området er ferdig søkt, `/stop_mission`, eller batteri < TODO % |
| `RETURNING` | `IDLE` | roboten er tilbake ved start |
| alle | `ERROR` | `/emergency_stop = true` eller kritisk feil |

---

## 8. Sikkerhet og feilhåndtering

- **Nødstopp:** Når `/emergency_stop` er `true`, skal `base_driver` stoppe motorene umiddelbart, uansett hva andre noder sender. Roboten står stille til en manuell reset.
- **Watchdog:** `base_driver` stopper hvis `/cmd_vel` uteblir i mer enn 0,5 s.
- **Node faller ut:** Hvis `mission_manager` ikke mottar data fra en påkrevd node (`/odom`, `/scan`) på TODO s, går den til `ERROR`.
- **Lavt batteri:** Under TODO % går roboten til `RETURNING`.

---

## 9. Parametre

| Parameter | Node | Type | Standard | Beskrivelse |
|---|---|---|---|---|
| `max_linear_speed` | `navigation` | double | 0.3 | m/s |
| `max_angular_speed` | `navigation` | double | 1.0 | rad/s |
| `detection_threshold` | `victim_detector` | double | 0.7 | min. `confidence` for å publisere funn |
| `cmd_vel_timeout` | `base_driver` | double | 0.5 | s før watchdog stopper roboten |
| `low_battery_percent` | `mission_manager` | double | TODO | grense for å returnere |

---

## 10. Endringsregler

1. Endringer i kontrakten foreslås og avtales i gruppa **før** koden endres.
2. Når et topic, service, en action eller en meldingstype endres, økes versjonsnummeret øverst, og endringen føres i loggen under.
3. Endringer som brekker eksisterende kode (nye navn, fjernede felt) gir nytt hovednummer (0.x → 1.0).
4. Endringer i `sar_robot_interface` og `CONTRACT.md` committes sammen.

### Endringslogg

| Versjon | Dato | Endring | Av |
|---|---|---|---|
| 0.1 | 2026-10-08 | Første utkast | TODO |

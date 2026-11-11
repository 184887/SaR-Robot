# Testlogg

Her skriver vi ned resultatet hver gang vi kjører hele systemet, så vi ser om det blir bedre.


## Slik kjører vi en test

1. Terminal 1: ros2 run scoring scoring
2. Terminal 2: ros2 launch sar_robot sar.launch.py world:=1 (bytt tallet for andre verdener)
3. La det gå i 10 minutter. Sluttpoengene står på siste linje i terminal 1 (Final Score).
4. Stopp begge med Ctrl+C og start scoring på nytt før neste test. Ellers blir ikke markørene godkjent igjen.

Commit finner du med git log --oneline -1.


## Hvordan poengene blir

- 100 poeng per markør som blir godkjent.
- 300 ekstra hvis begge robotene er innen 2 m fra storbrannen (markør 4) etter at den er rapportert.
- Tidspoeng (600 minus sekundene som er brukt) får vi bare hvis alle markørene er funnet og storbrannbonusen er tatt. Ellers er sluttpoengene bare markørpoengene.
- Posisjonen vi rapporterer må være innen 0.5 m fra riktig sted.


## Kjøringer

Lag en ny overskrift for hver kjøring og fyll inn de samme punktene.
- Kjøring 1

- Dato: 11.11
- Commit: 8cfc3ce
- Verden: w1
- Poeng: 500
- Markører funnet: 0 og 4 (begge av tb3_1)
- Storbrann: ja
- Kommentar:
  - Begge marker_reporter krasjet, tb3_0 etter ca 290 s og tb3_1 etter ca 526 s.
  - Grunn: aruco så en id over 127, og den passer ikke i marker_id (int8).
  - tb3_1 sendte også id 88 hvert 5. sekund.

- Kjøring 2

- Dato: 11.11
- Commit: 8cfc3ce
- Verden: w1
- Poeng: 200
- Markører funnet: 0 (tb3_1) og 3 (tb3_0)
- Storbrann: nei
- Kommentar:
  - Ingen krasj denne gangen. id 88 kom én gang.
  - tb3_0 så markør 4 sju ganger, men alle ble avvist. Posisjonene var 1.4 til 7 m feil.
  - tb3_0 så markør 2 tre ganger før tiden var ute, også 1.7 til 9.6 m feil.
  - Etter tiden var ute kom markør 2 nesten riktig (0.07 m feil), men da var det for sent.
  - Posisjonen til markørene blir ofte regnet veldig feil. Bør sjekkes i marker_reporter.

## Mulig endringer som kan gjøres basert på kjøringene (oppdateres og fjernes etter behov):
- marker_recognition fra kurset husker siste markør for alltid. Når roboten har kjørt videre, legger den den gamle målingen på der roboten er nå. Markøren flytter seg altså med roboten, og blir sendt når roboten står stille i 1 sekund. Derfor ble markør 4 avvist i kjøring 2.
- Forslag: les også aruco_markers, og rapporter bare hvis det kom en melding der for under ca 0.3 s siden. Den gamle versjonen (3be6b56) leste 	  aruco_markers direkte.
- Hopp over id-er som ikke er 0-4. Id over 127 krasjet noden i kjøring 1, og id 88 blir alltid avvist.
- Kanskje sette z til 0 før vi sender. Scoring måler i 3D og markørene har z = 0. 



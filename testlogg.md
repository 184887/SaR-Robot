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
- Kjøring 1 (gammel kode, telles ikke)

- Dato: 11.11
- Commit: 8cfc3ce
- Verden: w1
- Poeng: 500
- Markører funnet: 0 og 4 (begge av tb3_1)
- Storbrann: ja
- Kommentar:
  - Etter en stund kom det ikke flere markører på /markers_found fra noen av robotene.
  - tb3_1 meldte markør 88 mange ganger. Den finnes ikke og ble avvist.

- Kjøring 2 (gammel kode, telles ikke)

- Dato: 11.11
- Commit: 8cfc3ce
- Verden: w1
- Poeng: 200
- Markører funnet: 0 (tb3_1) og 3 (tb3_0)
- Storbrann: nei
- Kommentar:
  - tb3_0 meldte markør 4 sju ganger, men alle ble avvist.
  - tb3_0 meldte markør 2 tre ganger, også avvist.

- Kjøring 3

- Dato: 12.11
- Commit: 749fe98
- Verden: w1
- Poeng: 600
- Markører funnet: 0 (tb3_1), 4 og 3 (tb3_0)
- Storbrann: ja
- Kommentar:
  - Robotene stoppet litt når de så en ny markør.
  - Markør 4 ble avvist første gang, men godkjent rett etter.
  - tb3_0 sto lenge og ventet ved storbrannen før tb3_1 kom fram.
  - Etter bonusen sto robotene i veien for hverandre en stund.

- Kjøring 4

- Dato: 12.11
- Commit: 749fe98
- Verden: w2
- Poeng: 700
- Markører funnet: 4 og 3 (tb3_0), 2 og 1 (tb3_1)
- Storbrann: ja
- Kommentar:
  - Markør 0 ble ikke funnet før tiden var ute. Den står rett ved siden av markør 3.
  - Robotene ble stående ved storbrannen en stund etter at begge var kommet fram.

- Kjøring 5

- Dato: 12.11
- Commit: 749fe98
- Verden: w1
- Poeng: 600
- Markører funnet: 0 og 4 (tb3_1), 1 (tb3_0)
- Storbrann: ja
- Kommentar:
  - tb3_1 sto lenge og ventet ved storbrannen før tb3_0 kom fram.
  - Markør 2 og 3 ble ikke funnet før tiden var ute.
  - Etter at tiden var ute meldte tb3_1 markør 3 mange ganger, og posisjonen var forskjellig hver gang.

- Kjøring 6

- Dato: 12.11
- Commit: 749fe98
- Verden: w3
- Poeng: 1066
- Markører funnet: 3 og 0 (tb3_1), 4, 2 og 1 (tb3_0)
- Storbrann: ja
- Kommentar:
  - Alle markørene ble funnet og godkjent på første forsøk, så vi fikk tidspoeng også.
  - RViz- og Gazebo-vinduet ble lukket rett etter start.

- Kjøring 7

- Dato: 12.11
- Commit: 749fe98
- Verden: w4
- Poeng: 700
- Markører funnet: 1 og 4 (tb3_1), 2 og 3 (tb3_0)
- Storbrann: ja
- Kommentar:
  - Alle markørene som ble funnet, ble godkjent på første forsøk.
  - Markør 0 ble ikke funnet før tiden var ute.
  - Markør 2 og 4 står rett ved siden av hverandre. tb3_0 meldte markør 2 tidlig, men markør 4 kom mye senere fra tb3_1.

- Kjøring 8

- Dato: 12.11
- Commit: 749fe98
- Verden: w5
- Poeng: 1103
- Markører funnet: 0, 1, 4 og 3 (tb3_1), 2 (tb3_0)
- Storbrann: ja
- Kommentar:
  - Alle markørene ble funnet og godkjent på første forsøk, så vi fikk tidspoeng også.
  - tb3_1 fant fire av de fem markørene.

- Kjøring 9

- Dato: 12.11
- Commit: 749fe98
- Verden: w1
- Poeng: 925
- Markører funnet: 0 og 1 (tb3_1), 4, 3 og 2 (tb3_0)
- Storbrann: ja
- Kommentar:
  - Alle markørene ble funnet og godkjent på første forsøk, så vi fikk tidspoeng også.
  - Første gang alle markørene ble funnet i w1.

- Kjøring 10

- Dato: 15.11
- Commit: 3f4dee2
- Verden: w2
- Poeng: 1051
- Markører funnet: 2, 1 og 3 (tb3_1), 0 og 4 (tb3_0)
- Storbrann: ja
- Kommentar:
  - Alle markørene ble funnet, så vi fikk tidspoeng også.
  - Markør 3 ble avvist fire ganger før den ble godkjent. tb3_1 så den fra ca 6 m unna, og etterpå ble den gamle målingen sendt mens roboten snudde seg. Samme feil som i kjøring 2.
  - tb3_0 ventet ca 90 s ved storbrannen, fordi tb3_1 var langt vest i kartet da markør 4 ble funnet.

- Kjøring 11

- Dato: 15.11
- Commit: 3f4dee2 
- Verden: w3
- Poeng: 1042
- Markører funnet: 3, 4 og 2 (tb3_1), 1 og 0 (tb3_0)
- Storbrann: ja
- Kommentar:
  - Alle markørene ble funnet og godkjent på første forsøk, så vi fikk tidspoeng også.
  - Bonusen kom allerede etter ca 2 minutter. Det som tok tid var markør 0, som ble funnet sist, nesten 2.5 minutter etter markør 2.

- Kjøring 12

- Dato: 15.11
- Commit: 3f4dee2 
- Verden: w4
- Poeng: 700
- Markører funnet: 1 og 4 (tb3_1), 2 og 3 (tb3_0)
- Storbrann: ja
- Kommentar:
  - Alle markørene som ble funnet, ble godkjent på første forsøk.
  - Markør 0 ble ikke funnet, samme som i kjøring 7. tb3_1 var 1.4 m fra den etter ca 2.5 min, men kameraet så den aldri.
  - Markør 2 og 4 ser ut til å stå rygg mot rygg. Markør 2 ble bare sett fra vest og markør 4 bare fra øst, så de kom 200 s fra hverandre. Det forklarer nok det samme i kjøring 7.
  - RViz- og Gazebo-vinduet var åpne de første ca 5 minuttene, så real-time factor var på rundt 0.50-0.60.

- Kjøring 13

- Dato: 15.11
- Commit: 3f4dee2 
- Verden: w5
- Poeng: 1083
- Markører funnet: 0, 1, 4 og 3 (tb3_1), 2 (tb3_0)
- Storbrann: ja
- Kommentar:
  - Alle markørene ble funnet og godkjent på første forsøk, så vi fikk tidspoeng også.
  - Nesten likt kjøring 8: samme robot fant de samme markørene i samme rekkefølge.
  - tb3_1 ventet ca 80 s ved storbrannen før tb3_0 kom.



# 5. Bevegelse – utkast

*Utkast 2026-11-10, basert på koden på `main` (commit `d41f091`). Tall og oppførsel er hentet fra koden. Det som står i [hakeparenteser], må fylles inn etter testkjøringer.*

Bevegelsen består av tre deler. To av dem er rene Python-klasser uten ROS-kode: en veggfølger (`WallFollower`) og en stifølger (`PathFollower`). Den tredje er ROS-noden `robot_controller`, som kobler klassene til sensorene og bestemmer hvilken av dem som styrer roboten. Ved å holde ROS utenfor klassene kan logikken testes med vanlige enhetstester, uten å starte Gazebo.

## 5.1 Veggfølger

Veggfølgeren bygger på veggfølgeren fra Bug2-labben i kurset. Den er skrevet om til en klasse som tar inn avstandene fra lidaren og returnerer lineær fart *v* og vinkelfart *ω*.

**Soner.** Lidaren gir 360 avstander, én per grad. Disse deles inn i seks soner: foran, foran-venstre, venstre, bak, høyre og foran-høyre. For hver sone brukes den minste gyldige avstanden. Målinger utenfor sensorens område (`range_min`–`range_max`) forkastes, slik at verken 0 eller uendelig blir tolket som en vegg. Sonen på siden roboten følger, kalles i det videre *sideavstanden*.

**Tilstander.** Veggfølgeren er en tilstandsmaskin med fire tilstander (figur 5.1):

- `FINN_VEGG`: Roboten kjører rett fram med 0,15 m/s til den finner en vegg.
- `SVING_BORT`: Er noe nærmere enn 0,5 m foran, snur roboten på stedet med 0,5 rad/s. Denne tilstanden har høyest prioritet.
- `FOLLOW_WALL`: Er sideavstanden under 0,7 m, følger roboten veggen.
- `SVING_MOT`: Forsvinner veggen på siden, for eksempel ved et ytre hjørne, svinger roboten tilbake mot den mens den kjører fram.

[Figur 5.1: Tilstandsdiagram for veggfølgeren med overgangene over.]

**Regulering.** I `FOLLOW_WALL` brukes en P-regulator for å holde en fast avstand til veggen:

ω = K_p · (d_ref − d_side), med d_ref = 0,4 m og K_p = 0,5.

Vinkelfarten er begrenset til ±0,5 rad/s, og den lineære farten er 0,15 m/s.

**Timeout.** I et åpent rom kan `SVING_MOT` føre til at roboten kjører i sirkel uten å finne veggen igjen. Etter 7 sekunder i `SVING_MOT` går roboten derfor tilbake til `FINN_VEGG` og kjører rett fram til den treffer en ny vegg. [Beskriv hva dere observerte før timeouten ble lagt inn.]

**Høyre eller venstre vegg.** Parameteren `follow_left` bestemmer hvilken side roboten følger. Samme kode brukes for begge sidene: sideavstanden hentes fra motsatt sone, og fortegnet på *ω* snus. `tb3_0` følger høyre vegg og `tb3_1` venstre, slik at robotene går hver sin vei og dekker ulike deler av kartet når de bruker veggfølging.

## 5.2 Stifølger

Stifølgeren kjører roboten gjennom en liste med punkter i `map`-rammen, i praksis ruta fra A*-planleggeren (kapittel 4.2). For hvert steg får den robotens posisjon (*x*, *y*, *θ*) og returnerer (*v*, *ω*).

**Styring mot neste punkt.** Vinkelfeilen er forskjellen mellom retningen til neste punkt og robotens retning:

e = atan2(y_mål − y, x_mål − x) − θ

Feilen normaliseres til intervallet [−π, π], slik at roboten alltid svinger den korteste veien. Vinkelfarten er ω = K_p · e med K_p = 1,0, begrenset til ±0,5 rad/s.

**Snu på stedet.** Er vinkelfeilen større enn 0,5 rad (omtrent 29°), settes *v* = 0, og roboten snur på stedet før den kjører videre. Ellers kjører den med 0,15 m/s. Dette hindrer at roboten kjører i en vid bue og kommer for nær veggene når ruta svinger skarpt.

**Punkter som er nådd.** Et punkt regnes som nådd når roboten er nærmere enn 0,2 m. Det fjernes fra lista, og det samme gjelder alle påfølgende punkter roboten allerede er innenfor. Når lista er tom, er ruta ferdig.

**Begrunnelse.** Stifølgeren unngår ikke hindringer selv. Det er ikke nødvendig, fordi A* planlegger på et kart med buffer rundt veggene (kapittel 4.1), og en enkel regulator holder dermed. Mer avanserte metoder, som pure pursuit eller Dynamic Window Approach, kunne gitt jevnere kjøring, men ville gjort koden mer kompleks.

## 5.3 robot_controller

`robot_controller` er noden som styrer roboten. Det går én instans per robot, i namespacet `tb3_0` eller `tb3_1`. Noden bruker relative topicnavn (`scan`, `cmd_vel`, `coverage_path`, `goal`), slik at samme kode virker i begge namespacene. Unntaket er `/robot_states`, som er globalt, slik at coordinatoren får tilstanden til begge robotene på ett topic.

**Posisjon.** Odometrien til hver robot starter i null der roboten står ved oppstart, og stemmer derfor ikke med kartet. Posisjonen hentes i stedet med tf2, som transformen fra `map` til `tb3_X/base_footprint`. Retningen *θ* regnes ut fra quaternionen. Posisjonen publiseres som `RobotState` på `/robot_states` hver runde, også når roboten er skrudd av, slik at coordinatoren alltid vet hvor robotene er.

**Kontrollsløyfe.** Noden kjører en timer på 10 Hz. Hver runde velger den én av tre måter å kjøre på, i denne rekkefølgen (figur 5.2):

1. **`AT_GOAL`:** Har coordinatoren gitt et mål, og roboten er nærmere enn 1 m, stopper den og venter.
2. **`FOLLOW_PATH`:** Finnes det et kart og en rute, følger roboten ruta med stifølgeren.
3. **Veggfølging:** I alle andre tilfeller styrer veggfølgeren.

[Figur 5.2: Modusene i `robot_controller` og overgangene mellom dem.]

Veggfølging brukes altså som reserve: før kartet og dekningsruta har kommet, når ruta er blokkert, og når alle dekningspunktene er besøkt. Roboten står dermed aldri stille og venter, men utforsker videre.

**Dekningsruta.** Noden får dekningspunktene sine på `coverage_path` (kapittel 4.3). For hvert punkt planlegges en rute fra robotens posisjon med A*. Planleggingen gjøres på `/inflated_map` nedskalert til 5 cm-ruter, som gjør A* raskere enn på kartets opprinnelige oppløsning på 1 cm. Finner A* ingen rute til et punkt, hoppes punktet over.

**Blokkert rute.** Kartet viser bare faste vegger, ikke den andre roboten. Mens roboten følger ruta, sjekkes derfor sonen foran. Er noe nærmere enn 0,3 m, regnes ruta som blokkert. Roboten følger da veggen i 3 sekunder og planlegger deretter på nytt til samme punkt. Blokkeres samme punkt to ganger, hoppes det over, slik at roboten ikke blir stående fast ved ett punkt. Et mål fra coordinatoren hoppes aldri over.

**Mål fra coordinatoren.** Når storbrannen er funnet, sender coordinatoren et mål på `/tb3_X/goal` (`PoseStamped`). Målet legges først i køen, og punktet roboten var på vei til, legges rett bak, slik at dekningsruta kan fortsette senere. Når roboten er innenfor 1 m av målet, stopper den. Scoring krever at begge robotene er innenfor 2 m, så 1 m gir margin for unøyaktighet i posisjonen. Roboten kan skrus av og på med tjenesten `wallfollower_switch`. Skrus den på igjen etter målet, fortsetter den dekningsruta.

**Logging.** Hvert bytte av modus eller tilstand logges. Dette ble brukt under testingen for å finne ut hvor og hvorfor robotene satte seg fast. [Henvis til kapittel 8 og 9.]

**Begrensninger.**
- Blokkering oppdages bare i sonen rett foran, ikke på sidene, så roboten kan komme nær vegger på siden.
- Reguleringsparametrene er stilt inn for hånd og er de samme i alle verdenene. [Kommenter etter testing.]
- Farten på 0,15 m/s er valgt for å være sikker. Siden poengsummen synker med 1 poeng i sekundet, kan høyere fart gi mer poeng. [Kommenter etter testing.]

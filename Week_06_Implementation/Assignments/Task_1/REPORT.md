# Task 1 – Klonovanie repozitára cez coding asistenta

## Čo agent urobil

1. Prečítal si zadania a `missing_code.json`. Cesty v JSON-e začínajú `playground/...`, takže repo
   naklonoval do `Assignments/AI4SE_Playground/`. Tam ho vedia použiť aj Tasky 2–5.
2. V shelli spustil `git clone https://github.com/Neltharion59/AI4SE_Playground.git`.
3. Klon skontroloval cez `git log`, výpis súborov a `grep` na metódy s telom `pass`. Našlo sa
   presne tých 10 prázdnych metód, ktoré vypisuje `missing_code.json`.
4. Zmazal `AI4SE_Playground/.git`. Keby tam ostal, git by priečinok bral ako vnorený repozitár a
   uložil by si len odkaz naň, nie samotné súbory.

## Ako to funguje

Samotný model nemá prístup na internet ani k súborom. Klonovanie fungovalo vďaka **tool use v
agentickej slučke**:

- Claude Code dá modelu zoznam nástrojov. Každý má názov, popis a schému parametrov. Jeden z nich je
  `Bash`, ktorý spustí príkaz v shelli.
- Model namiesto obyčajného textu vráti štruktúrované volanie nástroja, napríklad
  `Bash{command: "git clone https://..."}`.
- Claude Code volanie skontroluje podľa mojich nastavení povolení a spustí ho v lokálnom shelli.
  Samotné stiahnutie urobí `git` nainštalovaný na mojom počítači, cez HTTPS. Repo je verejné, takže
  netreba žiadne prihlasovacie údaje.
- Výstup príkazu sa vráti modelu ako výsledok nástroja. Model si ho prečíta a rozhodne o ďalšom kroku:
  skontrolovať klon, potom zmazať `.git`.

Skrátka: **LLM vymyslí príkazy, Claude Code ich spustí a naklonuje to lokálny `git`.**

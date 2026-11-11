# Task 2 – Rozdelenie repozitára na chunky

Skript [`chunk_repo.py`](chunk_repo.py) prečíta `../AI4SE_Playground` a uloží chunky do
[`chunks.json`](chunks.json). Spúšťa sa cez `python chunk_repo.py`.

## Ako delím

Repo je čistý Python, tak ho nedelím podľa počtu znakov, ale podľa štruktúry kódu cez vstavaný
modul `ast`. Z každého `.py` súboru vzniknú tri druhy chunkov:

- **metóda / funkcia:** celý kód jednej metódy aj s dekorátormi a docstringom,
- **trieda:** signatúra, docstring, atribúty a jednoriadkový zoznam všetkých metód, niečo ako obsah
  triedy,
- **modul:** docstring, importy a konštanty.

Každý chunk má na začiatku krátku hlavičku (`# File`, `# Kind`, `# Class`, `# Symbol`), aby jeho
embedding vedel, kam kód patrí. Okrem toho si pamätám metadáta: súbor, či ide o zdrojový kód alebo
test, rozsah riadkov a príznak `is_stub` pre metódy, ktoré majú telo iba `pass`. Výsledok je obyčajný
zoznam v JSON-e.

## Prečo takáto veľkosť

- Každá úloha v `missing_code.json` je jedna metóda. Najviac pomôžu iné metódy, napríklad susedná
  metóda v tej istej triede alebo helper, ktorý treba zavolať. Pevné okná by metódy rozsekali a
  miešali by nesúvisiaci kód.
- Malé chunky (typicky okolo 75 tokenov) majú jeden jasný význam, takže ich embedding nie je
  „rozmazaný“. Top 5 sa v Tasku 5 navyše pohodlne zmestí do promptu.
- Chunky tried a modulov vracajú kontext, ktorý by sa pri malých metódach stratil: aké metódy
  trieda má a čo je importované.
- Ak by bol nejaký kus dlhší ako 60 riadkov, rozdelí sa na okná s 5-riadkovým prekryvom. V tomto repe
  sa to nestalo ani raz.

Do chunkov som zobral aj testy (označené `kind: "test"`), lebo najpresnejšie hovoria, čo majú chýbajúce
metódy robiť.

## Výsledok

798 chunkov: 201 zo zdrojového kódu a 597 z testov. Celé repo má iba asi 51k tokenov, takže by sa
zmestilo aj do veľkého kontextu. Rozdelenie má ale aj tak zmysel, lebo prompty ostanú malé a lacné,
a presne toto RAG pipeline potrebuje.

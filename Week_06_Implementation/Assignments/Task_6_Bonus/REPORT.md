# Task 6 (bonus) – Návrh lepšieho pipeline

Task 5 ukázal, že model nezlyhal na písaní kódu, ale na kontexte. Pri `price` a `transition`
nepoznal API tried `Money` a `InvalidTransitionError`. Silnejší model urobil tie isté chyby.

## Je embedding matching najlepšia stratégia?

Pre kód nie, ak je jediná. Embedding nájde kód, ktorý sa na úlohu podobá. Na napísanie metódy však
treba hlavne kód, od ktorého úloha závisí, teda typy, importy a výnimky. Tie sa na text úlohy podobať
nemusia: v dotaze o zľave sa `Money` vôbec nevyskytuje. Závislosti sa dajú zistiť presne z kódu, takže
embedding by som nechal len ako doplnok.

## Iný počet chunkov?

Viac chunkov rovnakého druhu by nepomohlo, nechýbalo viac kontextu, ale iný. Namiesto pevného *n* by
som dal tokenový rozpočet. Pri takom malom repe (zdrojový kód má asi 12k tokenov) by som RAG
nepoužil vôbec a poslal by som celé súbory.

## Sofistikovanejšie delenie?

Delenie podľa AST fungovalo dobre. Chýbajú len väzby medzi chunkami: kde je definované to, čo metóda
používa, kto ju volá a ktoré testy ju testujú.

## Môj návrh

1. **Index:** AST chunky a k nim graf závislostí (definície, importy, volania, testy).
2. **Kontext podľa priority:** cieľová trieda a importy, potom definície použitých typov, miesta
   volania a testy. Až nakoniec vyhľadávanie podľa podobnosti. Ak sa všetko zmestí, pošlú sa celé
   súbory.
3. **Generovanie** ako doteraz, s kontrolou cez `ast`.
4. **Spustiť testy** a pri chybe poslať hlášku späť modelu (2–3 kolá). Naše chyby, napríklad
   `missing 1 required positional argument: 'target'`, presne hovoria, čo treba opraviť.
5. **Ak si docstring a test odporujú**, model to má nahlásiť, nie hádať.

Ďalšou možnosťou je agent, ktorý si kontext dohľadá sám cez nástroje (grep, čítanie súborov, testy). Je
to flexibilnejšie, ale drahšie a menej predvídateľné. Pre jednoduché úlohy ako tieto by som začal
pipeline vyššie.

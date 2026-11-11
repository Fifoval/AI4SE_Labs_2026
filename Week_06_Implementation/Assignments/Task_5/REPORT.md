# Task 5 – Riešenie úloh cez RAG

Skript: [`solve.py`](solve.py). Spúšťa sa cez `python solve.py [--model gpt-5-mini] [--restore] [--naive]`
a potrebuje `OPENAI_API_KEY` v `../.env`.

## Pipeline

Pre každú položku z `missing_code.json`:

1. **Text úlohy.** Z položky spravím jednu vetu, napríklad: *"Implement the method `transition` of class
   `OrderStateMachine` in `.../orders.py`. Return `target` if the transition is allowed, else raise."*
   Funkcia `solve(task, ...)` dostane iba tento text a cieľový súbor, triedu a metódu si z neho nájde
   sama.
2. **Vyhľadanie.** Top 5 chunkov z Tasku 3 a 4.
3. **Prompt.** Úloha, prázdna metóda a 5 chunkov aj so súborom a skóre. V systémovom prompte sú
   pravidlá: vrátiť iba metódu, nemeniť signatúru, používať len to, čo je v kontexte.
4. **Zápis.** Kód z odpovede skontrolujem cez `ast`: musí to byť presne jedna metóda so správnym
   názvom a celý súbor musí ísť stále sparsovať. Potom ním nahradím prázdnu metódu. Keby kontrola
   zlyhala, chyba sa pošle späť modelu, najviac na 3 pokusy. V praxi to ani raz nebolo treba.
5. **Testy.** Nakoniec sa spustí `python -m unittest discover`.

Prompty a odpovede sú uložené v `runX/runs/`, vygenerovaný kód v `runX/generated_src/`. Pôvodné súbory
s prázdnymi metódami sú v `original/` a prepínač `--restore` ich vráti späť.

## Výsledky

Pred generovaním padalo **52 z 481 testov**.

| Beh | Nastavenie | Model | Padá | Prechádza |
|---|---|---|---|---|
| 1 | čisté top 5 | gpt-5-mini | 18 | 463 / 481 |
| **2** | **bez prázdnych metód v top 5 + importy cieľového súboru** | **gpt-5-mini** | **13** | **468 / 481** |
| 3 | rovnaké ako beh 2 | gpt-6-luna | 14 | 467 / 481 |

V repe som nechal výsledok behu 2. Z 10 metód je 7 úplne správnych, zvyšných 13 padajúcich testov
spôsobujú 3 metódy.

## Čo nevyšlo a prečo

**Beh 1 → beh 2.** V prvom behu sa ukázali dva problémy:

- Medzi top 5 sa dostávali samotné prázdne metódy, ktoré nenesú žiadnu informáciu. V behu 2 ich
  vynechávam (`skip_stubs`).
- Model nevedel, aké mená sú v cieľovom súbore dostupné. `is_terminal` použil `OrderStateMachine`
  z iného súboru (`NameError`) a `transition` vyhadzoval `ValueError` namiesto importovaného
  `InvalidTransitionError`. V behu 2 preto pridávam do promptu importy cieľového súboru. To opravilo
  `is_terminal` a `transition` už používa správnu výnimku.

Importy sú jediný kontext navyše. Vyhľadaná časť promptu je stále presne top 5.

**Čo padá aj po behu 2:**

| Metóda | Testy | Prečo |
|---|---|---|
| `BulkDiscountPricing.price` | 7 | Robí `Money * percent // 100`, ale `Money` nepodporuje `//`. Správne je `Money(total.cents * percent // 100)`. Trieda `Money` sa medzi top 5 nedostala. |
| `OrderStateMachine.transition` | 5 | Volá `InvalidTransitionError("správa")`, ale konštruktor chce `(source, target)`. Ani táto trieda sa nenašla. |
| `InventoryLedger.__contains__` | 1 | Riadi sa docstringom („positive on-hand stock“), ale test chce `True` aj pri nulovom stave. **Docstring odporuje testu**, takže to nesplní žiadny model. |

Prvé dve chyby majú spoločnú príčinu: **vyhľadávanie podľa podobnosti nájde kód, ktorý sa na úlohu
podobá, ale nie kód, od ktorého úloha závisí.** Dotaz hovorí o „discount“ alebo „transition“, takže
vráti susedné metódy tej istej triedy. Definície `Money` a `InvalidTransitionError` sú v iných
súboroch a do top 5 sa nedostanú.

Beh 3 to potvrdzuje: aj najsilnejší povolený model urobil presne tie isté dve chyby. Navyše v
`by_status` vynechal kontrolu typu, ktorú `gpt-5-mini` mal. **Problém je teda v kontexte, nie v
modeli.**

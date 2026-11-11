# Task 4 – Vyhľadávanie podľa embeddingu

Skript: [`match.py`](match.py).

- `python match.py "<úloha>" [-n 5]` vypíše top *n* chunkov pre zadanú úlohu.
- `python match.py --eval` to vyhodnotí na úlohách z `missing_code.json`.

## Ako to funguje

- **Cosine similarity.** Na nej bol model trénovaný. Vektory aj dotaz sú normalizované, takže celé
  vyhľadávanie je jedno násobenie `embeddings @ query`.
- **Presné vyhľadávanie bez indexu.** Pri 798 vektoroch trvá jeden dotaz asi 0,035 ms. Približný
  index (FAISS, HNSW) by tu nič nepriniesol.
- **Výber top *n*** cez `np.argpartition`. Zoradí sa potom len tých *n* najlepších.
- **Voliteľné filtre:** `kinds` obmedzí výsledky na zdrojový kód alebo testy a `skip_stubs` vynechá
  prázdne metódy s telom `pass`. Vyradené chunky dostanú skóre `-inf`.
- `retrieve(store, task, n)` zembedduje text úlohy a zavolá `top_n`. `task_to_query()` spraví
  z položky `missing_code.json` vetu na vyhľadanie.

Prahovú hodnotu skóre som nepridával. Skóre sú v úzkom pásme (asi 0,65–0,92), takže akákoľvek hranica by
bola náhodná. Zadanie navyše chce pevné *n*.

## Vyhodnotenie

Každú úlohu z `missing_code.json` som pustil ako dotaz. Vyhľadávanie zoradí všetkých 798 chunkov od
najpodobnejšieho, a ja som sa pozrel, na ktorom mieste v tomto poradí skončili dva chunky:

- **chunk prázdnej metódy:** samotná metóda, ktorú treba doplniť (má len `pass`),
- **chunk triedy:** súhrn triedy, do ktorej metóda patrí (jej signatúra a zoznam metód).

Napríklad pre úlohu `OrderStateMachine.transition` vyzerá začiatok poradia takto:

```
1. OrderStateMachine            ← chunk triedy
2. OrderStateMachine.transition ← chunk prázdnej metódy
3. OrderStateMachine.can_transition
4. OrderStateMachine.__call__
5. Order.advance
```

V tabuľke je teda pri `transition` 2 a 1. Do promptu v Tasku 5 idú iba prvé miesta (top 5), takže
**čím menšie číslo, tým lepšie**.

| Úloha | Miesto prázdnej metódy | Miesto chunku triedy |
|---|---|---|
| OrderStatus.is_terminal | 2 | 1 |
| InventoryLedger.\_\_contains\_\_ | 1 | 1 |
| Warehouse.stock_report | 3 | 1 |
| OrderStateMachine.transition | 2 | 1 |
| OrderLog.by_status | 1 | 1 |
| Customer.can_afford | 4 | 1 |
| Order.\_\_len\_\_ | 3 | 3 |
| BulkDiscountPricing.price | 6 | 1 |
| EventBus.\_\_contains\_\_ | 1 | 1 |
| Money.\_\_bool\_\_ | 13 | 1 |

- Chunk triedy je pri všetkých 10 úlohách na 1. až 3. mieste, takže model vždy vidí, ako trieda
  vyzerá, aj signatúru metódy, ktorú má doplniť.
- Prázdna metóda je v top 5 pri 8 z 10 úloh.

Najhoršie dopadol `Money.__bool__`, lebo jeho telo je len `pass` a podobá sa na ostatné metódy triedy
`Money`. To ale nevadí: samotný stub do promptu nič nové neprinesie, zato susedné metódy áno. Naopak,
keď sa stub do top 5 dostane, iba zaberie miesto. Preto ho v Tasku 5 vynechávam cez `skip_stubs`.

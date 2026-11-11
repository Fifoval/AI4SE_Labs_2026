# Task 3 – Embeddingy a úložisko

Skript [`embed_chunks.py`](embed_chunks.py) zoberie `../Task_2/chunks.json` a vytvorí
[`embeddings.npy`](embeddings.npy) a [`store.json`](store.json). Spúšťa sa cez
`python embed_chunks.py` a balíčky sú v `../requirements.txt`.

## Model

Používam `BAAI/bge-small-en-v1.5` cez `sentence-transformers`, lokálne na CPU.

- Kurz povoľuje len konkrétne chatovacie modely a embedding model medzi nimi nie je. Lokálny model
  túto otázku úplne obíde a nič nestojí. Celé repo zembedduje asi za 30 sekúnd.
- Je malý (384 dimenzií), ale na vyhľadávanie dosť dobrý. Dotaz a text sa pri ňom spracúvajú
  inak, čo sedí na náš prípad: krátka úloha v angličtine proti kódu. Pred dotazy dávam odporúčaný
  BGE prefix, chunky embeddujem tak, ako sú.
- Modely špeciálne na kód sú niekoľkonásobne väčšie. Tu však úlohy sú anglické vety a kód má
  zrozumiteľné názvy aj docstringy, takže bežný anglický model na to stačí.

## Čo sa embedduje

Text chunku, teda hlavička plus kód. Hlavička je dôležitá hlavne pri prázdnych metódach: majú len
`pass`, takže ich embedding vychádza skoro celý z názvu triedy, metódy a signatúry. To sú presne slová,
ktoré sa objavia aj v zadaní úlohy.

Model číta najviac 512 tokenov. Dlhší je len jeden chunk (`Simulation.step`), ktorému sa pri embeddingu
odreže koniec. Uložený kód je však celý.

## Úložisko

- `embeddings.npy`: matica 798 × 384 (asi 1,2 MB), riadok *i* patrí chunku *i*,
- `store.json`: názov modelu a chunky v rovnakom poradí ako riadky.

Trieda `EmbeddingStore` v skripte ich načíta a dá prístup podľa indexu alebo ID chunku. Vektory sú
normalizované, takže cosine similarity je jedno maticové násobenie. Pri 798 vektoroch to trvá zlomok
milisekundy. Vektorovú databázu (FAISS, Chroma) by som tu nevyužil, len by pridala ďalšiu
závislosť.

Pri rýchlom teste na úlohách z `missing_code.json` bola cieľová metóda alebo jej trieda vždy medzi
prvými tromi výsledkami.

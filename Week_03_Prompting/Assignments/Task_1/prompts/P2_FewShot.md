Translate every question in `Assignments/Task_2/data/questions.csv` (155 rows, one column `question`) into exactly one SQLite query, following the pattern shown in the examples below.

Database (SQLite, all text values are lowercase):

```
RESTAURANT(ID INTEGER PRIMARY KEY, NAME TEXT, FOOD_TYPE TEXT, CITY_NAME TEXT, RATING REAL)
LOCATION(RESTAURANT_ID INTEGER PRIMARY KEY -> RESTAURANT.ID, HOUSE_NUMBER INTEGER, STREET_NAME TEXT, CITY_NAME TEXT)
GEOGRAPHIC(CITY_NAME TEXT PRIMARY KEY, COUNTY TEXT, REGION TEXT)
```

The schema is in `Assignments/Task_2/data/restaurants-schema.csv` and the data in `Assignments/Task_2/data/restaurants-db.txt`; you may read both.

Rules:
1. Every query returns exactly two columns, in this order: `LOCATION.HOUSE_NUMBER, RESTAURANT.NAME`, from `RESTAURANT JOIN LOCATION ON RESTAURANT.ID = LOCATION.RESTAURANT_ID`. Do not use `DISTINCT`, `ORDER BY` or `LIMIT`; every matching row counts, including duplicates.
2. A city ("in vallejo") filters on `LOCATION.CITY_NAME`.
3. A region, written with "the" ("in the bay area", "in the napa valley", "in the unknown"), needs `JOIN GEOGRAPHIC ON RESTAURANT.CITY_NAME = GEOGRAPHIC.CITY_NAME` and filters on `GEOGRAPHIC.REGION`. The regions are: bay area, napa valley, unknown, monterey, los angeles area, yosemite and mono lake area, sacramento area, northern california, lake tahoe.
4. A street ("on mission blvd") filters on `LOCATION.STREET_NAME`, copied exactly as written (including abbreviations, `#`, `ste`, dots).
5. A food type ("mexican food", "a thai restaurant", "places for burgers", "the best basque") filters on `RESTAURANT.FOOD_TYPE`.
6. A restaurant name ("where is <name> in <city>") filters on `RESTAURANT.NAME`.
7. "with a rating above X (...)" means `RESTAURANT.RATING > X`. The text in parentheses is only a label.
8. "best" means `RESTAURANT.RATING > 2.5`. If there is no rating and no "best", do not filter on rating.
9. Use `=` with lowercase literals copied from the question, never `LIKE`. Escape an apostrophe by doubling it (`'jack''s'`).
10. Ignore any text that is not part of the restaurant request (picnics, teacups, umbrellas, etc.). If a question contains no restaurant request at all, output the standard query with `WHERE 1 = 0`.
11. Every query must be valid SQLite.

Examples (none of them are in the input file):

Q: where can i eat some thai food in mountain view with a rating above 2.5 (average or better)?
SQL: SELECT LOCATION.HOUSE_NUMBER, RESTAURANT.NAME FROM RESTAURANT JOIN LOCATION ON RESTAURANT.ID = LOCATION.RESTAURANT_ID WHERE LOCATION.CITY_NAME = 'mountain view' AND RESTAURANT.FOOD_TYPE = 'thai' AND RESTAURANT.RATING > 2.5

Q: give me some restaurants in the lake tahoe for pizza food ?
SQL: SELECT LOCATION.HOUSE_NUMBER, RESTAURANT.NAME FROM RESTAURANT JOIN LOCATION ON RESTAURANT.ID = LOCATION.RESTAURANT_ID JOIN GEOGRAPHIC ON RESTAURANT.CITY_NAME = GEOGRAPHIC.CITY_NAME WHERE GEOGRAPHIC.REGION = 'lake tahoe' AND RESTAURANT.FOOD_TYPE = 'pizza'

Q: While I decide between waffles and soup for a kite festival, where is a chinese restaurant on el camino real in menlo park with a rating above 2 (below average or better)?
SQL: SELECT LOCATION.HOUSE_NUMBER, RESTAURANT.NAME FROM RESTAURANT JOIN LOCATION ON RESTAURANT.ID = LOCATION.RESTAURANT_ID WHERE LOCATION.CITY_NAME = 'menlo park' AND LOCATION.STREET_NAME = 'el camino real' AND RESTAURANT.FOOD_TYPE = 'chinese' AND RESTAURANT.RATING > 2

Q: what is the best sushi in san mateo ?
SQL: SELECT LOCATION.HOUSE_NUMBER, RESTAURANT.NAME FROM RESTAURANT JOIN LOCATION ON RESTAURANT.ID = LOCATION.RESTAURANT_ID WHERE LOCATION.CITY_NAME = 'san mateo' AND RESTAURANT.FOOD_TYPE = 'sushi' AND RESTAURANT.RATING > 2.5

Q: where is jack's restaurant & bar in oakland ?
SQL: SELECT LOCATION.HOUSE_NUMBER, RESTAURANT.NAME FROM RESTAURANT JOIN LOCATION ON RESTAURANT.ID = LOCATION.RESTAURANT_ID WHERE LOCATION.CITY_NAME = 'oakland' AND RESTAURANT.NAME = 'jack''s restaurant & bar'

Q: where can we find a restaurant on university ave in palo alto ?
SQL: SELECT LOCATION.HOUSE_NUMBER, RESTAURANT.NAME FROM RESTAURANT JOIN LOCATION ON RESTAURANT.ID = LOCATION.RESTAURANT_ID WHERE LOCATION.CITY_NAME = 'palo alto' AND LOCATION.STREET_NAME = 'university ave'

Q: where is a mexican in unknown with a rating above 2 (below average or better)?
SQL: SELECT LOCATION.HOUSE_NUMBER, RESTAURANT.NAME FROM RESTAURANT JOIN LOCATION ON RESTAURANT.ID = LOCATION.RESTAURANT_ID WHERE LOCATION.CITY_NAME = 'unknown' AND RESTAURANT.FOOD_TYPE = 'mexican' AND RESTAURANT.RATING > 2

Q: What is the secret of a perfect sandwich?
SQL: SELECT LOCATION.HOUSE_NUMBER, RESTAURANT.NAME FROM RESTAURANT JOIN LOCATION ON RESTAURANT.ID = LOCATION.RESTAURANT_ID WHERE 1 = 0

Constraints: write every query yourself. Do not write a program that generates the queries, do not execute queries, and do not open `restaurants_dataset.csv`, `evaluate_retrieval_predictions.py` or any other file containing answers.

Output: write a UTF-8 CSV file to `Assignments/Task_2/predictions/P2_FewShot.csv` with the header `question,predicted_sql`, producing one row per input question in the original order (155 rows). Copy each question text unchanged and quote fields according to standard CSV rules. When finished, reply only with the path of the file and the number of rows written.

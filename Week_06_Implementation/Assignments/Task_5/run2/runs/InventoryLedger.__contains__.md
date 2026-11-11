# InventoryLedger.__contains__

Model: gpt-5-mini

## Prompt

## Task
Implement the method __contains__ of class InventoryLedger in playground/playground/inventory.py. """Return whether ``sku`` normalises to a SKU with positive on-hand stock."""

## Stub to replace
```python
    def __contains__(self, sku: object) -> bool:
        pass
```

## Imports of the target file (the only external names available there)
```python
from __future__ import annotations
from typing import Dict, Iterator
from .base import Entity, Repository
from .exceptions import InvalidTransitionError, OutOfStockError, UnknownSKUError
from .util import ensure_positive_int, normalize_sku
```

## Relevant code from the repository (retrieved)
### Context 1: playground/tests/test_inventory.py::InventoryLedgerStockTests.test_require_sku_returns_normalized (lines 81-82, similarity 0.830)
```python
    def test_require_sku_returns_normalized(self) -> None:
        self.assertEqual(self.ledger._require_sku(" gr-2001 "), "GR-2001")
```

### Context 2: playground/playground/inventory.py::InventoryLedger._require_sku (lines 23-28, similarity 0.827)
```python
    def _require_sku(self, sku: str) -> str:
        """Normalise ``sku`` and raise ``UnknownSKUError`` if it is unregistered."""
        sku = normalize_sku(sku)
        if sku not in self._product_repo:
            raise UnknownSKUError(sku)
        return sku
```

### Context 3: playground/tests/test_inventory.py::InventoryLedgerStockTests.test_add_stock_normalizes_sku (lines 44-46, similarity 0.822)
```python
    def test_add_stock_normalizes_sku(self) -> None:
        self.assertEqual(self.ledger.add_stock(" el-1001 ", 2), 2)
        self.assertEqual(self.ledger.available("EL-1001"), 2)
```

### Context 4: playground/playground/inventory.py::InventoryLedger (lines 12-81, similarity 0.820)
```python
class InventoryLedger:
    """Tracks on-hand and reserved quantities per SKU."""
    def __init__(self, product_repo: Repository) -> None:  ...  # Create a ledger backed by ``product_repo`` for SKU validation.
    def _require_sku(self, sku: str) -> str:  ...  # Normalise ``sku`` and raise ``UnknownSKUError`` if it is unregistered.
    def add_stock(self, sku: str, quantity: int) -> int:  ...  # Add ``quantity`` to on-hand stock for ``sku``; return the new total.
    def available(self, sku: str) -> int:  ...  # Return on-hand minus reserved for ``sku``.
    def reserve(self, sku: str, quantity: int) -> ReservationContext:  ...  # Reserve ``quantity`` of ``sku`` and return a context that can commit or release it.
    def release(self, sku: str, quantity: int) -> None:  ...  # Release ``quantity`` previously reserved for ``sku``.
    def commit(self, sku: str, quantity: int) -> None:  ...  # Commit ``quantity`` of ``sku``: decrement both reserved and on-hand.
    def __contains__(self, sku: object) -> bool:  ...
    def __len__(self) -> int:  ...  # Return the number of SKUs with positive on-hand stock.
    def __iter__(self) -> Iterator[str]:  ...  # Iterate over SKUs with positive on-hand stock, in sorted order.
```

### Context 5: playground/playground/inventory.py::InventoryLedger.available (lines 37-40, similarity 0.818)
```python
    def available(self, sku: str) -> int:
        """Return on-hand minus reserved for ``sku``."""
        sku = self._require_sku(sku)
        return self._on_hand.get(sku, 0) - self._reserved.get(sku, 0)
```

Write the implementation of the method now.

## Answer (attempt 1)

```python
def __contains__(self, sku: object) -> bool:
    """Return whether ``sku`` normalises to a SKU with positive on-hand stock."""
    try:
        sku = normalize_sku(sku)
    except Exception:
        return False
    if sku not in self._product_repo:
        return False
    return self._on_hand.get(sku, 0) > 0
```

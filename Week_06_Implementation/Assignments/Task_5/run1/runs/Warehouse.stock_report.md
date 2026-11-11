# Warehouse.stock_report

Model: gpt-5-mini

## Prompt

## Task
Implement the method stock_report of class Warehouse in playground/playground/inventory.py. """Return a mapping of SKU to available quantity."""

## Stub to replace
```python
    def stock_report(self) -> Dict[str, int]:
        pass
```

## Relevant code from the repository (retrieved)
### Context 1: playground/playground/inventory.py::Warehouse (lines 124-155, similarity 0.832)
```python
class Warehouse(Entity):
    """Named location owning an :class:`InventoryLedger`."""
    def __init__(self, warehouse_id: str, name: str, ledger: InventoryLedger) -> None:  ...  # Create a warehouse with the given id, name, and ledger.
    def identity(self) -> str:  ...  # Return the warehouse_id as the entity identity.
    @property def ledger(self) -> InventoryLedger:  ...  # Return the warehouse inventory ledger.
    def receive(self, sku: str, quantity: int) -> int:  ...  # Add stock to the warehouse ledger; return the new on-hand total.
    def stock_report(self) -> Dict[str, int]:  ...
    def __repr__(self) -> str:  ...  # Return a developer-friendly representation.
```

### Context 2: playground/playground/inventory.py::Warehouse.receive (lines 146-148, similarity 0.830)
```python
    def receive(self, sku: str, quantity: int) -> int:
        """Add stock to the warehouse ledger; return the new on-hand total."""
        return self._ledger.add_stock(sku, quantity)
```

### Context 3: playground/playground/inventory.py::Warehouse.stock_report (lines 150-151, similarity 0.825)
```python
    def stock_report(self) -> Dict[str, int]:
        pass
```

### Context 4: playground/playground/inventory.py::InventoryLedger (lines 12-81, similarity 0.801)
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

### Context 5: playground/playground/__init__.py::<module> (lines 1-49, similarity 0.782)
```python
"""Warehouse inventory and order processing playground."""
from __future__ import annotations
__version__ = "0.1.0"
from .decorators import AuditTrail
from .enums import Category, EventType, OrderStatus
from .events import EventBus
from .exceptions import (
    DuplicateEntityError,
    InvalidTransitionError,
    InventoryError,
    OutOfStockError,
    PlaygroundError,
    UnknownSKUError,
)
from .inventory import Warehouse
from .models import Customer, LineItem, Money, Product
from .orders import Order, OrderBuilder, OrderLog
from .pricing import BulkDiscountPricing, FlatPricing
from .simulation import Simulation, run_simulation
__all__ = [
    "__version__",
    "Money",
    "Product",
    "LineItem",
    "Customer",
    "Warehouse",
    "Order",
    "OrderBuilder",
    "OrderLog",
    "FlatPricing",
    "BulkDiscountPricing",
    "EventBus",
    "AuditTrail",
    "Simulation",
    "PlaygroundError",
    "InventoryError",
    "OutOfStockError",
    "UnknownSKUError",
    "DuplicateEntityError",
    "InvalidTransitionError",
    "Category",
    "OrderStatus",
    "EventType",
    "run_simulation",
]
```

Write the implementation of the method now.

## Answer (attempt 1)

```python
def stock_report(self) -> Dict[str, int]:
    """Return a mapping of SKU to available quantity."""
    return {sku: self._ledger.available(sku) for sku in self._ledger}
```

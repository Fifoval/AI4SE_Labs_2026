# Order.__len__

Model: gpt-5-mini

## Prompt

## Task
Implement the method __len__ of class Order in playground/playground/orders.py. """Return the number of line items."""

## Stub to replace
```python
    def __len__(self) -> int:
        pass
```

## Imports of the target file (the only external names available there)
```python
from __future__ import annotations
from typing import Dict, FrozenSet, Iterator, List, Tuple
from .base import PricingStrategy
from .enums import OrderStatus
from .exceptions import DuplicateEntityError, InvalidTransitionError
from .models import Customer, LineItem, Money
from .pricing import FlatPricing
```

## Relevant code from the repository (retrieved)
### Context 1: playground/playground/orders.py::OrderBuilder.__len__ (lines 158-160, similarity 0.855)
```python
    def __len__(self) -> int:
        """Return the number of recorded lines."""
        return len(self._lines)
```

### Context 2: playground/playground/orders.py::OrderLog.__len__ (lines 190-192, similarity 0.828)
```python
    def __len__(self) -> int:
        """Return the number of logged orders."""
        return len(self._orders)
```

### Context 3: playground/playground/orders.py::OrderBuilder.__bool__ (lines 162-164, similarity 0.793)
```python
    def __bool__(self) -> bool:
        """Return True when at least one line has been recorded."""
        return len(self) > 0
```

### Context 4: playground/playground/orders.py::OrderBuilder.build (lines 149-156, similarity 0.789)
```python
    def build(self, order_id: str) -> Order:
        """Construct and return the order; raises if no lines were recorded."""
        if len(self._lines) == 0:
            raise ValueError("no items")
        order = Order(order_id, self._customer, self._pricing)
        for sku, quantity, unit_price in self._lines:
            order.add_item(LineItem(sku, quantity, unit_price))
        return order
```

### Context 5: playground/playground/orders.py::Order.items (lines 76-79, similarity 0.788)
```python
    @property
    def items(self) -> Tuple[LineItem, ...]:
        """Return a tuple copy of the order's line items."""
        return tuple(self._items)
```

Write the implementation of the method now.

## Answer (attempt 1)

```python
def __len__(self) -> int:
    """Return the number of line items."""
    return len(self._items)
```

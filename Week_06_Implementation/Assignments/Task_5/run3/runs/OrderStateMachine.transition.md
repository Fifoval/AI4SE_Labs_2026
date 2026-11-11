# OrderStateMachine.transition

Model: gpt-6-luna

## Prompt

## Task
Implement the method transition of class OrderStateMachine in playground/playground/orders.py. """Return ``target`` if the transition is allowed, else raise."""

## Stub to replace
```python
    def transition(self, source: OrderStatus, target: OrderStatus) -> OrderStatus:
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
### Context 1: playground/playground/orders.py::OrderStateMachine (lines 14-40, similarity 0.847)
```python
class OrderStateMachine:
    """Legal OrderStatus transitions, data-driven via TRANSITIONS."""
    TRANSITIONS: Dict[OrderStatus, FrozenSet[OrderStatus]] = {
        OrderStatus.NEW: frozenset({OrderStatus.RESERVED, OrderStatus.CANCELLED}),
        OrderStatus.RESERVED: frozenset({OrderStatus.SHIPPED, OrderStatus.CANCELLED}),
        OrderStatus.SHIPPED: frozenset(),
        OrderStatus.CANCELLED: frozenset(),
    }
    @staticmethod def allowed_from(status: OrderStatus) -> FrozenSet[OrderStatus]:  ...  # Return the set of statuses reachable from ``status``.
    def can_transition(self, source: OrderStatus, target: OrderStatus) -> bool:  ...  # Return whether ``target`` is reachable from ``source``.
    def transition(self, source: OrderStatus, target: OrderStatus) -> OrderStatus:  ...
    def __call__(self, source: OrderStatus, target: OrderStatus) -> OrderStatus:  ...  # Convenience alias for :meth:`transition`.
```

### Context 2: playground/playground/orders.py::OrderStateMachine.can_transition (lines 31-33, similarity 0.839)
```python
    def can_transition(self, source: OrderStatus, target: OrderStatus) -> bool:
        """Return whether ``target`` is reachable from ``source``."""
        return target in OrderStateMachine.allowed_from(source)
```

### Context 3: playground/playground/orders.py::OrderStateMachine.__call__ (lines 38-40, similarity 0.835)
```python
    def __call__(self, source: OrderStatus, target: OrderStatus) -> OrderStatus:
        """Convenience alias for :meth:`transition`."""
        return self.transition(source, target)
```

### Context 4: playground/playground/orders.py::Order.advance (lines 98-101, similarity 0.820)
```python
    def advance(self, target: OrderStatus) -> None:
        """Transition the order to ``target`` status, raising if not allowed."""
        new_status = self._machine.transition(self._status, target)
        self._status = new_status
```

### Context 5: playground/tests/test_orders.py::OrderStateMachineTests.test_transition_returns_target_when_legal (lines 58-60, similarity 0.811)
```python
    def test_transition_returns_target_when_legal(self) -> None:
        sm = OrderStateMachine()
        self.assertIs(sm.transition(OrderStatus.NEW, OrderStatus.RESERVED), OrderStatus.RESERVED)
```

Write the implementation of the method now.

## Answer (attempt 1)

```python
    def transition(self, source: OrderStatus, target: OrderStatus) -> OrderStatus:
        """Return ``target`` if the transition is allowed, else raise."""
        if not self.can_transition(source, target):
            raise InvalidTransitionError(
                f"Cannot transition from {source} to {target}"
            )
        return target
```

# OrderStatus.is_terminal

Model: gpt-5-mini

## Prompt

## Task
Implement the method is_terminal of class OrderStatus in playground/playground/enums.py. """True when the status ends further transitions."""

## Stub to replace
```python
    @property
    def is_terminal(self) -> bool:
        pass
```

## Relevant code from the repository (retrieved)
### Context 1: playground/playground/enums.py::OrderStatus (lines 37-47, similarity 0.922)
```python
class OrderStatus(Enum):
    """Lifecycle stages for an order."""
    NEW = "new"
    RESERVED = "reserved"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"
    @property def is_terminal(self) -> bool:  ...
```

### Context 2: playground/playground/enums.py::OrderStatus.is_terminal (lines 45-47, similarity 0.875)
```python
    @property
    def is_terminal(self) -> bool:
        pass
```

### Context 3: playground/tests/test_enums.py::OrderStatusTests.test_cancelled_is_terminal (lines 60-61, similarity 0.842)
```python
    def test_cancelled_is_terminal(self) -> None:
        self.assertIs(OrderStatus.CANCELLED.is_terminal, True)
```

### Context 4: playground/tests/test_enums.py::OrderStatusTests.test_new_is_not_terminal (lines 63-64, similarity 0.824)
```python
    def test_new_is_not_terminal(self) -> None:
        self.assertIs(OrderStatus.NEW.is_terminal, False)
```

### Context 5: playground/playground/orders.py::OrderStateMachine (lines 14-40, similarity 0.820)
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

Write the implementation of the method now.

## Answer (attempt 1)

```python
    @property
    def is_terminal(self) -> bool:
        """True when the status ends further transitions."""
        # A status is terminal when there are no allowed transitions from it.
        return not OrderStateMachine.TRANSITIONS.get(self, frozenset())
```

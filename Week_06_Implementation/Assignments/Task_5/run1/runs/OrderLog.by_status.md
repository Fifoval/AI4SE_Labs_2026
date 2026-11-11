# OrderLog.by_status

Model: gpt-5-mini

## Prompt

## Task
Implement the method by_status of class OrderLog in playground/playground/orders.py. """Yield orders whose status matches ``status``."""

## Stub to replace
```python
    def by_status(self, status: OrderStatus) -> Iterator[Order]:
        pass
```

## Relevant code from the repository (retrieved)
### Context 1: playground/playground/orders.py::OrderLog.by_status (lines 183-184, similarity 0.821)
```python
    def by_status(self, status: OrderStatus) -> Iterator[Order]:
        pass
```

### Context 2: playground/playground/orders.py::OrderLog.__iter__ (lines 194-196, similarity 0.811)
```python
    def __iter__(self) -> Iterator[Order]:
        """Iterate over the logged orders."""
        yield from list(self._orders)
```

### Context 3: playground/tests/test_orders.py::OrderLogTests.test_by_status_is_lazy_generator (lines 401-404, similarity 0.801)
```python
    def test_by_status_is_lazy_generator(self) -> None:
        gen = self.log.by_status(OrderStatus.NEW)
        self.assertFalse(hasattr(gen, "__len__"))
        self.assertEqual(list(gen), [])
```

### Context 4: playground/playground/orders.py::OrderLog (lines 167-196, similarity 0.797)
```python
class OrderLog:
    """Ordered, deduplicated record of orders; iterable."""
    def __init__(self) -> None:  ...  # Create an empty order log.
    def record(self, order: Order) -> None:  ...  # Append ``order``; raises if an order with the same id is already logged.
    def by_status(self, status: OrderStatus) -> Iterator[Order]:  ...
    def __getitem__(self, index: int) -> Order:  ...  # Return the order at ``index``.
    def __len__(self) -> int:  ...  # Return the number of logged orders.
    def __iter__(self) -> Iterator[Order]:  ...  # Iterate over the logged orders.
```

### Context 5: playground/playground/orders.py::Order.status (lines 71-74, similarity 0.794)
```python
    @property
    def status(self) -> OrderStatus:
        """Return the current order status."""
        return self._status
```

Write the implementation of the method now.

## Answer (attempt 1)

```python
def by_status(self, status: OrderStatus) -> Iterator[Order]:
    """Yield orders whose status matches ``status``."""
    for order in self:
        if order.status == status:
            yield order
```

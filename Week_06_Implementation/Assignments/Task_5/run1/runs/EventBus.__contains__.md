# EventBus.__contains__

Model: gpt-5-mini

## Prompt

## Task
Implement the method __contains__ of class EventBus in playground/playground/events.py. """Return whether any handlers are registered for ``event_type``."""

## Stub to replace
```python
    def __contains__(self, event_type: object) -> bool:
        pass
```

## Relevant code from the repository (retrieved)
### Context 1: playground/playground/events.py::EventBus.__contains__ (lines 53-54, similarity 0.873)
```python
    def __contains__(self, event_type: object) -> bool:
        pass
```

### Context 2: playground/tests/test_events.py::EventBusContainsTests.test_contains_true_with_handler (lines 156-159, similarity 0.844)
```python
    def test_contains_true_with_handler(self) -> None:
        bus = EventBus()
        bus.subscribe(EventType.ORDER_SHIPPED, lambda p: None)
        self.assertIn(EventType.ORDER_SHIPPED, bus)
```

### Context 3: playground/tests/test_events.py::EventBusContainsTests (lines 152-173, similarity 0.829)
```python
class EventBusContainsTests(unittest.TestCase):
    def test_contains_false_without_handlers(self) -> None:  ...
    def test_contains_true_with_handler(self) -> None:  ...
    def test_contains_false_after_all_unsubscribed(self) -> None:  ...
    def test_contains_non_event_type_is_false(self) -> None:  ...
```

### Context 4: playground/playground/events.py::EventBus (lines 11-54, similarity 0.827)
```python
class EventBus:
    """Synchronous publish/subscribe keyed by :class:`EventType`."""
    def __init__(self) -> None:  ...  # Initialise an empty handler registry.
    def subscribe(self, event_type: EventType, handler: Callable[..., None]) -> None:  ...  # Register ``handler`` to be called when ``event_type`` is published.
    def unsubscribe(self, event_type: EventType, handler: Callable[..., None]) -> bool:  ...  # Remove ``handler`` from ``event_type``; return whether it was present.
    def publish(self, event_type: EventType, payload: Mapping[str, object]) -> int:  ...  # Invoke every handler subscribed to ``event_type`` with ``payload``.
    def __len__(self) -> int:  ...  # Return the total number of registered handlers across all event types.
    def __contains__(self, event_type: object) -> bool:  ...
```

### Context 5: playground/tests/test_events.py::EventBusContainsTests.test_contains_false_without_handlers (lines 153-154, similarity 0.817)
```python
    def test_contains_false_without_handlers(self) -> None:
        self.assertNotIn(EventType.ORDER_SHIPPED, EventBus())
```

Write the implementation of the method now.

## Answer (attempt 1)

```python
def __contains__(self, event_type: object) -> bool:
    """Return whether any handlers are registered for ``event_type``."""
    if not isinstance(event_type, EventType):
        return False
    try:
        handlers = self._handlers.get(event_type)
    except AttributeError:
        # If the internal registry doesn't exist, there are no handlers.
        return False
    return bool(handlers)
```

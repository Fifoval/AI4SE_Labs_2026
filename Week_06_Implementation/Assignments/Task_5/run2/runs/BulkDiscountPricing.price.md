# BulkDiscountPricing.price

Model: gpt-5-mini

## Prompt

## Task
Implement the method price of class BulkDiscountPricing in playground/playground/pricing.py. """Return the base price, less the discount if the quantity qualifies."""

## Stub to replace
```python
    def price(self, items: Sequence[LineItem]) -> Money:
        pass
```

## Imports of the target file (the only external names available there)
```python
from __future__ import annotations
from typing import Sequence
from .base import PricingStrategy
from .models import LineItem, Money
from .util import ensure_positive_int
```

## Relevant code from the repository (retrieved)
### Context 1: playground/playground/pricing.py::BulkDiscountPricing (lines 37-68, similarity 0.883)
```python
class BulkDiscountPricing(PricingStrategy):
    """Wraps another strategy; applies a percent discount when total quantity meets a threshold."""
    def __init__(self, base: PricingStrategy, threshold: int, percent_off: int) -> None:  ...  # Create a strategy that discounts ``base`` totals above ``threshold`` quantity.
    @property def threshold(self) -> int:  ...  # Return the qualifying total quantity.
    @property def percent_off(self) -> int:  ...  # Return the discount percentage.
    def price(self, items: Sequence[LineItem]) -> Money:  ...
    def __repr__(self) -> str:  ...  # Return a developer-friendly representation.
```

### Context 2: playground/playground/pricing.py::BulkDiscountPricing.__init__ (lines 40-51, similarity 0.844)
```python
    def __init__(self, base: PricingStrategy, threshold: int, percent_off: int) -> None:
        """Create a strategy that discounts ``base`` totals above ``threshold`` quantity."""
        if not isinstance(base, PricingStrategy):
            raise TypeError("base must be PricingStrategy")
        threshold = ensure_positive_int(threshold, "threshold")
        if isinstance(percent_off, bool) or not isinstance(percent_off, int):
            raise TypeError("percent_off must be int")
        if percent_off < 0 or percent_off > 100:
            raise ValueError("percent_off must be 0..100")
        self._base = base
        self._threshold = threshold
        self._percent_off = percent_off
```

### Context 3: playground/tests/test_pricing.py::BulkDiscountPriceTests (lines 118-164, similarity 0.830)
```python
class BulkDiscountPriceTests(unittest.TestCase):
    def test_below_threshold_returns_base_total(self) -> None:  ...
    def test_at_threshold_applies_discount(self) -> None:  ...
    def test_quantity_summed_across_lines(self) -> None:  ...
    def test_zero_percent_returns_base_even_above_threshold(self) -> None:  ...
    def test_discount_uses_floor_division(self) -> None: # base 333; 333 * 10 // 100 = 33 -> 300  ...
    def test_full_discount_yields_zero(self) -> None:  ...
    def test_wraps_base_with_tax(self) -> None:  ...
    def test_empty_items_below_threshold(self) -> None:  ...
    def test_call_matches_price(self) -> None:  ...
```

### Context 4: playground/playground/pricing.py::BulkDiscountPricing.__repr__ (lines 66-68, similarity 0.824)
```python
    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return f"BulkDiscountPricing(threshold={self._threshold}, percent_off={self._percent_off})"
```

### Context 5: playground/playground/pricing.py::BulkDiscountPricing.percent_off (lines 58-61, similarity 0.823)
```python
    @property
    def percent_off(self) -> int:
        """Return the discount percentage."""
        return self._percent_off
```

Write the implementation of the method now.

## Answer (attempt 1)

```python
def price(self, items: Sequence[LineItem]) -> Money:
    """Return the base price, less the discount if the quantity qualifies."""
    total_qty = sum(item.quantity for item in items)
    base_total = self._base.price(items)
    if total_qty < self._threshold or self._percent_off == 0:
        return base_total
    discount = (base_total * self._percent_off) // 100
    return base_total - discount
```

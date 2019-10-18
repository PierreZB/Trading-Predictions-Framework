# General rules applied in the transformation process:

1. We obviously process our signals only when we receive a full candle: OHLC.
2. We take only one position at a time.
3. We don't update positions unless it's to close them.
4. In case we have contradictory signals, we will need to write down the different actions to take in each scenario.

Given that we have:

- 3 original situations: no position opened, buying position opened or selling position opened
- 2 possible situations for the buying flag (0 or 1)
- 2 possible situations for the selling flag (0 or 1)
- 2 possible situations for the closing flag (0 or 1)

That makes 24 possible scenarios to review. Fortunately half of them will be easy to sort out as they don't include contradictory signals. However, to make this settings table clearer, and to give more flexibility to the users, we will include all scenarios in it.

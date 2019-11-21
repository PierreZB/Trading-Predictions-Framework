# General rules applied in the backtest process:

1. We obviously process our signals only when we receive a full candle: OHLC.
2. We take only one position at a time.
3. We don't update positions unless it's to close them.
4. In case we have contradictory signals, we will need to write down the different actions to take in each scenario.

Please refer to backtestStrategy.xlsx to review the list of actions to take ine ach situation
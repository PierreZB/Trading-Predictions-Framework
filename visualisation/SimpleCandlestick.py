import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from pathlib import Path

pd.set_option('display.expand_frame_repr', False)

dataFolder = Path("../Data/")

df = pd.read_csv(dataFolder / "df_rawConcat.csv")

df = df[
    (df['year'] == 2018) &
    (df['month'] == 12) &
    (df['day'] >= 1) &
    (df['day'] <= 15)
]

print(df)

# exit()

fig = go.Figure(data=[go.Candlestick(x=df['timestamp'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'])])

fig.update_layout(xaxis_rangeslider_visible=False)
fig.show()

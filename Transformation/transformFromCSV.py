import time
import numpy as np
import pandas as pd
from pathlib import Path
# import random

# <editor-fold desc=" Load data ">
# Define file paths
dataFolder = Path("Data/")
sourceFile = dataFolder / "df_rawConcat.csv"

# Store start time
start_time = time.time()

# Create empty data frames
df = pd.DataFrame()
df_output = pd.DataFrame()
df_transf = pd.DataFrame()
df_lastrec = pd.DataFrame()

# Load csv, sort by ID, and reset the index
df = pd.read_csv(sourceFile, sep=",", encoding='utf-8', engine='c')
df = df.sort_values(by=['ID'], ascending=True, na_position='first')
df = df.reset_index(drop=True)
# df = df.head(5)
# print(df)

df = df.drop([
    'Unnamed: 0'
    ],
    axis=1)
# </editor-fold>

# <editor-fold desc=" Create random Buying, selling and closing signals ">

df['Buying Signal tmp'] = np.random.randint(0, 2, df.shape[0])
df['Selling Signal tmp'] = np.random.randint(0, 2, df.shape[0])
df['Closing Signal tmp'] = np.random.randint(0, 2, df.shape[0])

df['Buying Signal'] = np.where(
    df['Buying Signal tmp'] == df['Buying Signal tmp'].shift(),
    0,
    df['Buying Signal tmp']
    )
df['Selling Signal'] = np.where(
    df['Selling Signal tmp'] == df['Selling Signal tmp'].shift(),
    0,
    df['Selling Signal tmp']
    )
df['Closing Signal'] = np.where(
    df['Closing Signal tmp'] == df['Closing Signal tmp'].shift(),
    0,
    df['Closing Signal tmp']
    )

# Drop tmp fields
df = df.drop([
    'Buying Signal tmp',
    'Selling Signal tmp',
    'Closing Signal tmp'
    ],
    axis=1)

# </editor-fold>

# <editor-fold desc=" Check Buying and Selling Signals ">

# Here we want to make sure we don't have
# a buying ans selling flag at the same time.
# If this happens, the we reset both flags to 0.
# The outuput will be the verified values, under the same column names.

'''conditions = [((df['Buying Signal'] == 1) & (df['Selling Signal'] == 1))]
choices = [0]

df['Buying Signal Verified'] = np.select(
    conditions,
    choices,
    default=df['Buying Signal']
    )'''

df['Buying Signal Verified'] = np.where(
    ((df['Buying Signal'] == 1) & (df['Selling Signal'] == 1)),
    0,
    df['Buying Signal']
    )

df['Selling Signal Verified'] = np.where(
    ((df['Buying Signal'] == 1) & (df['Selling Signal'] == 1)),
    0,
    df['Selling Signal']
    )

# Drop tmp fields
df = df.drop([
    'Buying Signal',
    'Selling Signal'
    ],
    axis=1)

# Change columns names and order
df = df.rename(
    index=int,
    columns={
        "Buying Signal Verified": "Buying Signal",
        "Selling Signal Verified": "Selling Signal"
        }
    )

# </editor-fold>

# <editor-fold desc=" Position Status Tmp Fields ">

# In this section we will calculate temporary fields (simple flags)
# to know how have the positions been affected by the signals.

# Create the temporary fields, set at 0 by default
df['Tmp01'] = 0
df['Tmp02'] = 0
df['Tmp03'] = 0
df['Tmp04'] = 0
df['Tmp05'] = 0
df['Tmp06'] = 0


# open Buy status at end of current candle and before close action
def Tmp01(dfx):
    for i in range(0, len(dfx)):
        # calculate current and previous record number
        curRec = int(i)
        prvRec = int(np.where(curRec == 0, 0, curRec-1))
        # prepare the current column's previous record value
        Tmp01_prv = dfx.at[prvRec, "Tmp01"]
        # get main values required to calculate this column
        buySgn_prvRec = dfx.at[prvRec, "Buying Signal"]
        selSgn_prvRec = dfx.at[prvRec, "Selling Signal"]
        clsSgn_prvRec = dfx.at[prvRec, "Closing Signal"]

        if (
            ((clsSgn_prvRec == 1) and (buySgn_prvRec == 0))
            or (selSgn_prvRec == 1)
            or ((buySgn_prvRec == 0) and (Tmp01_prv == 0))
            or (curRec == 0)
        ):
                dfx.at[curRec, "Tmp01"] = 0
        else:
                dfx.at[curRec, "Tmp01"] = 1


print(Tmp01(df))


# open Sell status at end of current candle and before close action
def Tmp02(dfx):
    for i in range(0, len(dfx)):
        # calculate current and previous record number
        curRec = int(i)
        prvRec = int(np.where(curRec == 0, 0, curRec-1))
        # prepare the current column's previous record value
        Tmp02_prv = dfx.at[prvRec, "Tmp02"]
        # get main values required to calculate this column
        buySgn_prvRec = dfx.at[prvRec, "Buying Signal"]
        selSgn_prvRec = dfx.at[prvRec, "Selling Signal"]
        clsSgn_prvRec = dfx.at[prvRec, "Closing Signal"]

        if (
            ((clsSgn_prvRec == 1) and (selSgn_prvRec == 0))
            or (buySgn_prvRec == 1)
            or ((selSgn_prvRec == 0) and (Tmp02_prv == 0))
            or (curRec == 0)
        ):
                dfx.at[curRec, "Tmp02"] = 0
        else:
                dfx.at[curRec, "Tmp02"] = 1


print(Tmp02(df))


# closing at the end of current candle
df['Tmp03'] = np.where(
    ((df['Closing Signal'] == 1) & ((df['Tmp01'] == 1) | (df['Tmp02'] == 1)))
    | ((df['Tmp01'] == 1) & (df['Selling Signal'] == 1))
    | ((df['Tmp01'] == 1) & (df['Buying Signal'] == 1)),
    1,
    0
    )


# Redundant action
df['Tmp04'] = np.where(
    ((df['Tmp01'] == 1) & (df['Buying Signal'] == 1) & (df['Tmp03'] == 0))
    | ((df['Tmp02'] == 1) & (df['Selling Signal'] == 1) & (df['Tmp03'] == 0)),
    1,
    0
    )

# Open NEW Buy  ON OPEN
df['Tmp05'] = np.where(
    ((df['Tmp01'] == 1) & (df['Tmp01'].shift() == 0)),
    1,
    0
    )

# Open NEW Sell  ON OPEN
df['Tmp06'] = np.where(
    ((df['Tmp02'] == 1) & (df['Tmp02'].shift() == 0)),
    1,
    0
    )

# </editor-fold>

# <editor-fold desc=" Position Outputs ">
# Closing buying position
df['Closing buying position'] = np.where(
    ((df['Tmp03'] == 1) & (df['Tmp01'] == 1) & (df['Tmp01'].shift(-1) == 0)),
    1,
    0
    )

# Close selling position
df['Close selling position'] = np.where(
    ((df['Tmp03'] == 1) & (df['Tmp02'] == 1) & (df['Tmp02'].shift(-1) == 0)),
    1,
    0
    )

# Price on Open position; create field and format float 5
df['Price on Open position'] = 0.00000


# open Buy status at end of current candle and before close action
def PrcOpPos(dfx):
    for i in range(0, len(dfx)):
        # calculate current and previous record number
        curRec = int(i)
        prvRec = int(np.where(curRec == 0, 0, curRec-1))
        # get main values required to calculate this column
        Tmp01_curRec = dfx.at[curRec, "Tmp01"]
        Tmp02_curRec = dfx.at[curRec, "Tmp02"]
        Tmp05_curRec = dfx.at[curRec, "Tmp05"]
        Tmp06_curRec = dfx.at[curRec, "Tmp06"]

        if (
            ((Tmp01_curRec == 1) and (Tmp05_curRec == 1))
            or ((Tmp02_curRec == 1) and (Tmp06_curRec == 1))
        ):
                dfx.at[curRec, "Price on Open position"] = (
                    dfx.at[curRec, "open"]
                    )
        elif (
            (Tmp01_curRec == 1) or (Tmp02_curRec == 1)
        ):
                dfx.at[curRec, "Price on Open position"] = (
                    dfx.at[prvRec, "Price on Open position"]
                )
        else:
                dfx.at[curRec, "Price on Open position"] = np.NaN


print(PrcOpPos(df))


# Price on Close position; create field and format float 5
df['Price on Close position'] = 0.00000
df['Price on Close position'] = np.where(
    (df['Closing buying position'] == 1) | (df['Close selling position'] == 1),
    df['close'],
    np.NaN
    )

# PL pips on Close; create field and format float 5
df['Pips PL on Close any position'] = 0.00000

conditions = [
    (df['Closing buying position'] == 1),
    (df['Close selling position'] == 1)
    ]
choices = [
    df['Price on Close position'] - df['Price on Open position'],
    df['Price on Open position'] - df['Price on Close position'],
    ]

df['Pips PL on Close any position'] = np.select(
    conditions,
    choices,
    default=np.NaN
    )

# Pips PL any position cumlative
df['Pips PL any position cumlative'] = (
    df['Pips PL on Close any position'].fillna(0).cumsum(skipna=True)
    )

# export as csv
fileOutput = dataFolder / "df_processed_tmp.csv"
df.to_csv(fileOutput)
print(df)
# print(df[['Pips PL any position cumlative']])

# <editor-fold desc=" ===== Import Libraries ============================== ">
# Note that importing ta will import pandas and numpy as well
from ta import *
from scripts.project_settings import *

pd.set_option('display.expand_frame_repr', False)

# </editor-fold>

# List of files on which you want to apply this strategy
strategyFileList = ['']

for strategyFile in strategyFileList:

    # <editor-fold desc=" ===== Load data ================================= ">
    # Define file paths
    inputFile = (
            str(dataRawExtracts) + "/" +
            str(strategyFile) + str(".csv")
    )
    outputFile = (
            str(dataStrategies) + "/" +
            str(strategyFile) + str(".csv")
    )

    df["nextRec"] = df["close"].shift(-1)

    for emaPeriod in emaPeriods_list:
        ema_X = str("ema_") + str(emaPeriod)
        df[ema_X] = ema(df["close"], periods=emaPeriod, fillna=False)

        ema_X_ohlc4_ratio = str("ema_") + str(emaPeriod) + str("_ohlc4_ratio")
        df[ema_X_ohlc4_ratio] = df[ema_X] / (
            (df["open"] + df["high"] + df["low"] + df["close"]) / 4
        )

    for emaXY in emaPeriodsCartesian_list:
        emaCross_X, emaCross_Y = emaXY

        emaCross_X_Y = (
                str("emaCross_") + str(emaCross_X) + "_" + str(emaCross_Y)
        )
        emaRatio_X_Y = (
                str("emaRatio_") + str(emaCross_X) + "_" + str(emaCross_Y)
        )

        emaRatioDelta_X_Y = (
                str("emaRatioDelta_") + str(emaCross_X) + "_" + str(emaCross_Y)
        )

        ema_X = str("ema_") + str(emaCross_X)
        ema_Y = str("ema_") + str(emaCross_Y)

        df[emaRatio_X_Y] = df[ema_X] / df[ema_Y]
        df[emaRatioDelta_X_Y] = df[emaRatio_X_Y] / df[emaRatio_X_Y].shift(1)
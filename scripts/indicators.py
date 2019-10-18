# <editor-fold desc=" ===== Import Libraries ============================== ">
# Note that importing ta will import pandas and numpy as well
from ta import *
from scripts.project_settings import *

pd.set_option('display.expand_frame_repr', False)

# </editor-fold>

for indicatorsFile in indicatorsFileList:

    # <editor-fold desc=" ===== Load data ================================= ">
    # Define file paths
    inputFile = (
            str(dataStrategyBacktesting) + "/" +
            str(indicatorsFile) + str(".csv")
    )
    outputFile = (
            str(dataIndicators) + "/" +
            str(indicatorsFile) + str(".csv")
    )

    df = sort_deduplicate_reindex_data_frame(
        data_frame=df, index_field='ID', csv_source_file=inputFile
    )

    # Drop records where ID or core fields rae null
    df = df.dropna(
        subset=['ID', 'volume', 'open', 'high', 'low', 'close']
    )

    # </editor-fold>

    # <editor-fold desc=" ===== Add Indicators ============================ ">

    # Add all ta indicators
    df = add_all_ta_features(
        df, "open", "high", "low", "close", "volume", fillna=True
    )

    # </editor-fold>

    # <editor-fold desc=" ===== Trend ===================================== ">

    for rsiPeriod in rsiPeriods_List:
        rsi_X = str("rsi_") + str(rsiPeriod)
        df[rsi_X] = rsi(df["close"], n=rsiPeriod, fillna=False)
        for emaPeriod in emaPeriods_list:
            ema_X = str("ema_") + str(emaPeriod)
            rsi_X_ema_X = str(rsi_X) + "_" + str(ema_X)
            df[rsi_X_ema_X] = ema(df[rsi_X], periods=emaPeriod, fillna=False)

    for emaPeriod in emaPeriods_list:
        ema_X = str("ema_") + str(emaPeriod)
        df[ema_X] = ema(df["close"], periods=emaPeriod, fillna=False)

        ema_X_ohlc4_ratio = str("ema_") + str(emaPeriod) + str("_ohlc4_ratio")
        df[ema_X_ohlc4_ratio] = df[ema_X] / (
            (df["open"] + df["high"] + df["low"] + df["close"]) / 4
        )

    for emaXY in emaPeriodsCartesian_list:
        emaCross_X, emaCross_Y = emaXY

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

    # </editor-fold>

    # <editor-fold desc=" ===== PZB ======================================= ">

    # df[ema_X] = ema(df["close"], periods=emaPeriod, fillna=False)
    # n1 = 12
    # n2 = 26
    # n3 = 12
    #
    # MACD_PZB_X_Y_Z = "MACD_PZB_" + str(n1) + "_" + str(n2) + "_" + str(n3)
    #
    # ap = df["close"]
    # esa = ema(ap, n1)
    # d = ema(abs(ap - esa), n1)
    # ci = (ap - esa) / (0.015 * d)
    # tci = ema(ci, n2)
    #
    # wt1 = tci
    # wt2 = df[wt1].mean()
    #
    # df[MACD_PZB_X_Y_Z] = wt1 - wt2

    # </editor-fold>

    # <editor-fold desc=" ===== Export Output ============================= ">

    df.to_csv(outputFile)
    print(
        'Time lapsed: ' +
        str(outputFile) + " " + str(datetime.now() - startTime)
    )

    # </editor-fold>

print_time_lapsed(final=True)

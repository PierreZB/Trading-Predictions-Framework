# <editor-fold desc=" ===== Import Libraries ============================== ">
from scripts.project_settings import *
from datetime import datetime
import numpy as np

pd.set_option('display.expand_frame_repr', False)
pd.set_option('display.max_rows', 2500)
# </editor-fold>

# List of files on which you want to apply this strategy
# high Time Frame first, then Low Time Frame
strategyFileList = [
    ('EURUSD_H1_20050101_20191026', 'EURUSD_M15_20050101_20191026')
]

# Pips threshold beyond reference candle high/low
pipsThreshold = 2

# Strategy is based on the 7AM candle
referenceCandle = 7

for strategyFile in strategyFileList:

    highTimeFrameFile, lowTimeFrameFile = strategyFile

    # <editor-fold desc=" ===== Load data ================================= ">
    # Define file paths
    inputHighTimeFrameFile = (
            str(dataRawExtracts) + "/" +
            str(highTimeFrameFile) + str(".csv")
    )

    inputLowTimeFrameFile = (
            str(dataRawExtracts) + "/" +
            str(lowTimeFrameFile) + str(".csv")
    )

    outputFile = (
            str(dataStrategy) + "/" +
            str(lowTimeFrameFile) +
            str('_50pipsADay') +
            str('_StratThld') + str(str(pipsThreshold).zfill(3)) +
            str(".csv")
    )

    # Load csv, sort by ID, remove duplicates based on ID, reset the index
    dfHighTimeFrame = sort_deduplicate_reindex_data_frame(
        data_frame=df, index_field='ID',
        csv_source_file=inputHighTimeFrameFile
    )
    # Convert timestamp from UTC to Europe/London
    dfHighTimeFrame['timestamp'] = pd.to_datetime(
        pd.Series(dfHighTimeFrame['timestamp']), format="%Y-%m-%dT%H:%M:%S"
    )

    dfHighTimeFrame['timestamp'] = dfHighTimeFrame['timestamp'].\
        dt.tz_convert('Europe/London')

    dfLowTimeFrame = sort_deduplicate_reindex_data_frame(
        data_frame=df, index_field='ID',
        csv_source_file=inputLowTimeFrameFile
    )
    # Convert timestamp from UTC to Europe/London
    dfLowTimeFrame['timestamp'] = pd.to_datetime(
        pd.Series(dfLowTimeFrame['timestamp']), format="%Y-%m-%dT%H:%M:%S"
    )
    dfLowTimeFrame['timestamp'] = dfLowTimeFrame['timestamp'].\
        dt.tz_convert('Europe/London')

    # </editor-fold>

    # <editor-fold desc=" ===== Adapt timestamp and create key field ====== ">
    # High Time Frame
    dfHighTimeFrame['timestampMinusXh'] = (
        pd.to_datetime(dfHighTimeFrame['timestamp']) -
        pd.to_timedelta(referenceCandle, unit='h')
    )

    dfHighTimeFrame['yearMinusXh'] = pd.DatetimeIndex(
        dfHighTimeFrame['timestampMinusXh']
    ).year

    dfHighTimeFrame['monthMinusXh'] = pd.DatetimeIndex(
        dfHighTimeFrame['timestampMinusXh']
    ).month

    dfHighTimeFrame['dayMinusXh'] = pd.DatetimeIndex(
        dfHighTimeFrame['timestampMinusXh']
    ).day

    dfHighTimeFrame['hourMinusXh'] = pd.DatetimeIndex(
        dfHighTimeFrame['timestampMinusXh']
    ).hour

    dfHighTimeFrame['key'] = (
        dfHighTimeFrame['yearMinusXh'].astype(str) +
        dfHighTimeFrame['monthMinusXh'].astype(str).str.zfill(2) +
        dfHighTimeFrame['dayMinusXh'].astype(str).str.zfill(2) +
        dfHighTimeFrame['hourMinusXh'].astype(str).str.zfill(2)
    )

    # Make key field format matches with the other data frame key field
    dfHighTimeFrame['key'] = dfHighTimeFrame['key'].astype(int)

    # Low Time Frame
    dfLowTimeFrame['timestampMinusXh'] = (
        pd.to_datetime(dfLowTimeFrame['timestamp']) -
        pd.to_timedelta(referenceCandle, unit='h')
    )

    dfLowTimeFrame['yearMinusXh'] = pd.DatetimeIndex(
        dfLowTimeFrame['timestampMinusXh']
    ).year

    dfLowTimeFrame['monthMinusXh'] = pd.DatetimeIndex(
        dfLowTimeFrame['timestampMinusXh']
    ).month

    dfLowTimeFrame['dayMinusXh'] = pd.DatetimeIndex(
        dfLowTimeFrame['timestampMinusXh']
    ).day

    dfLowTimeFrame['hourMinusXh'] = pd.DatetimeIndex(
        dfLowTimeFrame['timestampMinusXh']
    ).hour

    dfLowTimeFrame['weekDay'] = pd.to_datetime(
        dfLowTimeFrame['timestampMinusXh']
    ).dt.dayofweek

    dfLowTimeFrame['keyTmp'] = (
        dfLowTimeFrame['yearMinusXh'].astype(str) +
        dfLowTimeFrame['monthMinusXh'].astype(str).str.zfill(2) +
        dfLowTimeFrame['dayMinusXh'].astype(str).str.zfill(2) +
        '00'
    )

    dfLowTimeFrame['key'] = 0

    for i in range(0, len(dfLowTimeFrame)):
        # calculate current and previous record number
        CurrentRecord = int(i)
        PreviousRecord = int(
            np.where(CurrentRecord == 0, 0, CurrentRecord - 1)
        )

        # key
        if dfLowTimeFrame.at[CurrentRecord, 'weekDay'] == 6:
            dfLowTimeFrame.at[CurrentRecord, 'key'] = (
                dfLowTimeFrame.at[PreviousRecord, 'key']
            )
        else:
            dfLowTimeFrame.at[CurrentRecord, 'key'] = (
                dfLowTimeFrame.at[CurrentRecord, 'keyTmp']
            )

    # Make key field format matches with the other data frame key field
    dfLowTimeFrame['key'] = dfLowTimeFrame['key'].astype(int)

    # Drop temporary fields
    dfLowTimeFrame = dfLowTimeFrame.drop(['keyTmp', 'weekDay'], axis=1)

    # </editor-fold>

    # <editor-fold desc=" ===== Get Thresholds =============================">

    # TODO [2] check behaviour on 25Dec and 01Jan
    # Isolate Reference Candle High/Low in High Time Frame
    dfHighTimeFrame['referenceCandleHigh'] = np.where(
        pd.DatetimeIndex(dfHighTimeFrame['timestampMinusXh']).hour == 0,
        dfHighTimeFrame['high'],
        0
    )

    dfHighTimeFrame['referenceCandleLow'] = np.where(
        pd.DatetimeIndex(dfHighTimeFrame['timestampMinusXh']).hour == 0,
        dfHighTimeFrame['low'],
        0
    )
    # Map Reference Candle High/Low from High Time Frame to Low Time Frame

    dfHighTimeFrame = dfHighTimeFrame[[
        'key',
        'referenceCandleHigh',
        'referenceCandleLow'
    ]]

    # Keep only records where the reference candle has value on high (and low)
    dfHighTimeFrame = dfHighTimeFrame[
        dfHighTimeFrame['referenceCandleHigh'] != 0
    ]

    # Left Join the High and Low Time Frames
    df = pd.merge(
        dfLowTimeFrame, dfHighTimeFrame, on='key', how='left'
    )

    # Drop dfHighTimeFrame and dfLowTimeFrame
    del dfHighTimeFrame
    del dfLowTimeFrame

    # </editor-fold>

    # <editor-fold desc=" ===== Calculate Threshold ======================= ">
    # Add pips to reference candle high/low
    df['referencePriceHigher'] = (
        df['referenceCandleHigh'] + pipsThreshold / 10_000
    )
    df['referencePriceLower'] = (
        df['referenceCandleLow'] - pipsThreshold / 10_000
    )

    # Check price cross threshold
    df['highAboveBuyThreshold'] = np.where(
        (df['hourMinusXh'] > 0) &
        (df['high'] >= df['referencePriceHigher']),
        1,
        0
    )

    df['lowBelowSellThreshold'] = np.where(
        (df['hourMinusXh'] > 0) &
        (df['low'] <= df['referencePriceLower']),
        1,
        0
    )

    # Cross thresholds cumulative
    df['crossHighThresholdCumulative'] = 0
    df['crossLowThresholdCumulative'] = 0

    for i in range(0, len(df)):
        # calculate current and previous record number
        CurrentRecord = int(i)
        PreviousRecord = int(
            np.where(CurrentRecord == 0, 0, CurrentRecord - 1)
        )

        # Cross high threshold cumulative
        if df.at[CurrentRecord, 'key'] == df.at[PreviousRecord, 'key']:
            df.at[CurrentRecord, 'crossHighThresholdCumulative'] = (
                df.at[CurrentRecord, 'highAboveBuyThreshold'] +
                df.at[PreviousRecord, 'crossHighThresholdCumulative']
            )
        else:
            df.at[CurrentRecord, 'crossHighThresholdCumulative'] = 0

        # Cross low threshold cumulative
        if df.at[CurrentRecord, 'key'] == df.at[PreviousRecord, 'key']:
            df.at[CurrentRecord, 'crossLowThresholdCumulative'] = (
                df.at[CurrentRecord, 'lowBelowSellThreshold'] +
                df.at[PreviousRecord, 'crossLowThresholdCumulative']
            )
        else:
            df.at[CurrentRecord, 'crossLowThresholdCumulative'] = 0

    df['crossHighOrLowThresholdCumulative'] = (
        df['crossHighThresholdCumulative'] +
        df['crossLowThresholdCumulative']
    )

    # </editor-fold>

    # <editor-fold desc=" ===== Buying/Selling/CLosing Signals ============ ">
    # Buy
    df['buyingSignal'] = np.where(
        (df['crossHighThresholdCumulative'] == 1) &
        (df['crossHighOrLowThresholdCumulative'].shift(1) == 0),
        1,
        0
    )

    # Sell
    df['sellingSignal'] = np.where(
        (df['crossLowThresholdCumulative'] == 1) &
        (df['crossHighOrLowThresholdCumulative'].shift(1) == 0),
        1,
        0
    )

    # Closing
    df['closingSignal'] = np.where(
        (df['key'] != df['key'].shift(-1)),
        1,
        0
    )

    # </editor-fold>

    # Convert timestamp back to UTC (from Europe/London)
    df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
    df['timestamp'] = pd.to_datetime(
        pd.Series(df['timestamp']),
        format="%Y-%m-%dT%H:%M:%S"
    )

    # Keep only default fields
    df = df[defaultColumnsList]

    df.to_csv(outputFile, index=False)
    print_time_lapsed(file_name=outputFile)
    # </editor-fold>

print_time_lapsed(final=True)

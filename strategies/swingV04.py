# <editor-fold desc=" ===== Import Libraries ============================== ">
from scripts.project_settings import *
from ta import *
import numpy as np

pd.set_option('display.expand_frame_repr', False)
pd.set_option('display.max_rows', 50)

# </editor-fold>

# List of files on which you want to apply this strategy
# high Time Frame first, then Low Time Frame
strategyFileList = [
    'EURUSD_H1_20180101_20181231',
    # 'EURUSD_H1_20050101_20191026',
    # 'EURUSD_M15_20040101_20191026'
]

# Difference between close and open threshold per candle (per ten thousand)
threshold = 5
# numbers of periods to analyse around current candle
periodsToAnalyseAroundCandle = 3
periodsToAnalyseAfterCandle = 240
periodsToAnalyseAfterCandleSL = 6
# set the maximum level of stop loss you can tolerate (per ten thousand)
maxSL = 0

# prepare those variables for the calculations
thresholdPerThsd = threshold / 10000
periodsToAnalyseCentered = periodsToAnalyseAroundCandle * 2 + 1
maxSLPerThsd = np.where(
    maxSL == 0,
    99_999,
    maxSL / 10000
)

for strategyFile in strategyFileList:

    # <editor-fold desc=" ===== Load data ================================= ">
    # Define file paths
    inputFile = (
            str(dataRawExtracts) + "/" +
            str(strategyFile) + str(".csv")
    )

    outputFile = (
            str(dataStrategy) + "/" +
            str(strategyFile) + '_' +
            str('swingV04') + '_' +
            str(str(threshold).zfill(4)) + '-' +
            str(str(periodsToAnalyseAroundCandle).zfill(4)) + '-' +
            str(str(periodsToAnalyseAfterCandle).zfill(4)) + '-' +
            str(str(periodsToAnalyseAfterCandleSL).zfill(4)) + '-' +
            str(str(maxSL).zfill(4)) +
            str(".csv")
    )

    # Load csv, sort by ID, remove duplicates based on ID, reset the index
    df = sort_deduplicate_reindex_data_frame(
        data_frame=df, index_field='ID',
        csv_source_file=inputFile
    )
    # </editor-fold>

    # <editor-fold desc=" ===== prepare roll max/min and shift values ===== ">

    # Convert timestamp from UTC to Europe/London
    df['timestamp'] = pd.to_datetime(
        pd.Series(df['timestamp']), format="%Y-%m-%dT%H:%M:%S"
    )

    # df['timestamp'] = df['timestamp'].dt.tz_convert('Europe/London')

    # Shift close
    df['closeShifted'] = df['close'].shift(-periodsToAnalyseAfterCandle)
    df['closeShiftedSL'] = df['close'].shift(-periodsToAnalyseAfterCandleSL)

    # find min and max in next candles
    df['maxHighNextP'] = df['closeShifted'].rolling(
        window=periodsToAnalyseAfterCandle, min_periods=0
    ).max()

    df['minLowNextP'] = df['closeShifted'].rolling(
        window=periodsToAnalyseAfterCandle, min_periods=0
    ).min()

    df['maxHighNextPSL'] = df['closeShiftedSL'].rolling(
        window=periodsToAnalyseAfterCandleSL, min_periods=0
    ).max()

    df['minLowNextPSL'] = df['closeShiftedSL'].rolling(
        window=periodsToAnalyseAfterCandleSL, min_periods=0
    ).min()

    # find swing point
    df['minCloseAround'] = df['close'].rolling(
        window=periodsToAnalyseCentered, min_periods=0, center=True
    ).min()

    df['maxCloseAround'] = df['close'].rolling(
        window=periodsToAnalyseCentered, min_periods=0, center=True
    ).max()

    df['minOpenAround'] = df['open'].rolling(
        window=periodsToAnalyseCentered, min_periods=0, center=True
    ).min()

    df['maxOpenAround'] = df['open'].rolling(
        window=periodsToAnalyseCentered, min_periods=0, center=True
    ).max()

    df['currentCandleOC'] = np.where(
        df['close'] > df['open'],
        1,
        0
    )
    # </editor-fold>

    # <editor-fold desc=" ===== Buying/Selling/CLosing Signals ============ ">
    # Buy
    df['buyingSignalToShift'] = np.where(
        ((df['currentCandleOC'] == 1) &
         (df['open'] == df['minOpenAround']) &
         ((df['maxHighNextP'] / df['open']) - 1 >= thresholdPerThsd) &
         (1 - (df['minLowNextPSL'] / df['open']) < maxSLPerThsd)
         ),
        1,
        0
    )

    df['buyingSignalTmp'] = np.where(
        ((df['currentCandleOC'] == 0) &
         (df['close'] == df['minCloseAround']) &
         ((df['maxHighNextP'] / df['close']) - 1 >= thresholdPerThsd) &
         (1 - (df['minLowNextPSL'] / df['close']) < maxSLPerThsd)
         ),
        1,
        0
    )

    df['buyingSignal'] = np.where(
        (df['buyingSignalTmp'] == 1) |
        (df['buyingSignalToShift'].shift(-1) == 1),
        1,
        0
    )

    # Sell
    df['sellingSignalToShift'] = np.where(
        ((df['currentCandleOC'] == 0) &
         (df['open'] == df['maxOpenAround']) &
         (1 - (df['minLowNextP'] / df['open']) >= thresholdPerThsd) &
         ((df['maxHighNextPSL'] / df['open']) - 1 < maxSLPerThsd)
         ),
        1,
        0
    )

    df['sellingSignalTmp'] = np.where(
        ((df['currentCandleOC'] == 1) &
         (df['close'] == df['maxCloseAround']) &
         (1 - (df['minLowNextP'] / df['close']) >= thresholdPerThsd) &
         ((df['maxHighNextPSL'] / df['close']) - 1 < maxSLPerThsd)
         ),
        1,
        0
    )

    df['sellingSignal'] = np.where(
        (df['sellingSignalTmp'] == 1) |
        (df['sellingSignalToShift'].shift(-1) == 1),
        1,
        0
    )

    # </editor-fold>

    # Keep only default fields
    df = df[defaultColumnsList]

    # print(df)
    df.to_csv(outputFile, index=False)
    print_time_lapsed(file_name=outputFile)
    # </editor-fold>

print_time_lapsed(final=True)

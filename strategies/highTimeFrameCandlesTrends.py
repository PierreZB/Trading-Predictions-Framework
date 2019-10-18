# <editor-fold desc=" ===== Import Libraries ============================== ">
import numpy as np
from scripts.project_settings import *

pd.set_option('display.expand_frame_repr', False)
pd.set_option('display.max_rows', 500)
# </editor-fold>

# <editor-fold desc=" ===== Load data ================================= ">
# Define strategy scope
instrumentStrategy = 'EUR_USD'
granularityHighFrameStrategy = 'H4'
granularityLowFrameStrategy = 'M10'
fromStrategy = '20140101'
toStrategy = '20191130'

# Generate file path
highTimeFrameRawExtractFile = str(
    str(instrumentStrategy) + '_' + str(granularityHighFrameStrategy) + '_' +
    str(fromStrategy) + '_' + str(toStrategy)
)

lowTimeFrameRawExtractFile = str(
    str(instrumentStrategy) + '_' + str(granularityLowFrameStrategy) + '_' +
    str(fromStrategy) + '_' + str(toStrategy)
)

outputStrategyFile = lowTimeFrameRawExtractFile

inputHighFrameFile = (
        str(dataRawExtracts) + '/' +
        str(highTimeFrameRawExtractFile) + str('.csv')
)

inputLowFrameFile = (
        str(dataRawExtracts) + '/' +
        str(lowTimeFrameRawExtractFile) + str('.csv')
)

outputFile = (
        str(dataStrategies) + '/' +
        str(outputStrategyFile) + str('.csv')
)

# Load data in data frames
dfHighFrame = sort_deduplicate_reindex_data_frame(
    data_frame=df, index_field='ID', csv_source_file=inputHighFrameFile
)
dfLowFrame = sort_deduplicate_reindex_data_frame(
    data_frame=df, index_field='ID', csv_source_file=inputLowFrameFile
)
# </editor-fold>

# <editor-fold desc=" ===== Process High Frame ============================ ">
"""
We will first calculate temporary fields to determine if the candle shows 
a significant trend; then we write the buying and selling signals accordingly.
A significant trend will have 4 main conditions:
    1- |open - close| > X pips
        => A large candle body implies a real trend during that period
        => This condition is useless when using a Take Profit, only the  
        condition nº4 will be important then
    2- (high OR low - open) / (low OR high - open) >= thresholdRiskRatio
        => Optimise the risk ratio
    3- |open - low OR high| <= thresholdOpenCloseDiff / thresholdRiskRatio
        => Ensure the "lowest" point won't be beyond your Stop Loss
    4- |high OR low - open| >= thresholdMaxOpenDiff
        => Ensure you can reach your Take Profit trigger
        => If you don't use a Take Profit, it makes more sense to focus on 
        the condition nº1 as this is the one that will define your level 
        of gains
Note: when writing "high OR low" this depends on the trend being up or down
"""
# Set thresholds to define a significant trend
thresholdOpenCloseDiff = 30 / 10_000
thresholdMaxOpenDiff = 50 / 10_000
thresholdRiskRatio = 1.6

# Candle Trend: Close < Open = 1, else -1
dfHighFrame['candleTrend'] = np.where(
    dfHighFrame['close'] > dfHighFrame['open'], 1, -1
)

# Significant candle body; open - close difference >= threshold
dfHighFrame['significantCandleBody'] = np.where(
    abs(
        dfHighFrame['close'] - dfHighFrame['open']
    ) >= thresholdOpenCloseDiff,
    1,
    0
)

# Significant High Low ratio;
dfHighFrame['significantHighLowRatio'] = np.where(
    abs(
        np.where(
            dfHighFrame['candleTrend'] == 1,
            dfHighFrame['high'],
            dfHighFrame['low']
        ) - dfHighFrame['open']
    ) /
    (abs(
        np.where(
            dfHighFrame['candleTrend'] == 1,
            dfHighFrame['low'],
            dfHighFrame['high']
        ) - dfHighFrame['open']
    ) + 0.00001)
    >= thresholdRiskRatio,
    1,
    0
)

# Significant Open to min (low OR high) - not going too low;
dfHighFrame['significantOpenMin'] = np.where(
    abs(
        dfHighFrame['open'] -
        np.where(
            dfHighFrame['candleTrend'] == 1,
            dfHighFrame['low'],
            dfHighFrame['high']
        )
    )
    <= thresholdOpenCloseDiff / thresholdRiskRatio,
    1,
    0
)

# Significant Open to max (high OR low) - maximise benefit;
dfHighFrame['significantOpenMax'] = np.where(
    abs(
        np.where(
            dfHighFrame['candleTrend'] == 1,
            dfHighFrame['high'],
            dfHighFrame['low']
        ) -
        dfHighFrame['open']
    )
    >= thresholdMaxOpenDiff,
    1,
    0
)

# Calculate the buying and selling signals
dfHighFrame['buyingSignalHighFrame'] = np.where(
    (dfHighFrame['candleTrend'] == 1) &
    (dfHighFrame['significantCandleBody'] == 1) &
    (dfHighFrame['significantHighLowRatio'] == 1) &
    (dfHighFrame['significantOpenMin'] == 1) &
    (dfHighFrame['significantOpenMax'] == 1),
    1,
    0
)

dfHighFrame['sellingSignalHighFrame'] = np.where(
    (dfHighFrame['candleTrend'] == -1) &
    (dfHighFrame['significantCandleBody'] == 1) &
    (dfHighFrame['significantHighLowRatio'] == 1) &
    (dfHighFrame['significantOpenMin'] == 1) &
    (dfHighFrame['significantOpenMax'] == 1),
    1,
    0
)

dfHighFrame['closingSignalHighFrame'] = np.where(
    (dfHighFrame['buyingSignalHighFrame'].shift(1) == 1) |
    (dfHighFrame['sellingSignalHighFrame'].shift(1) == 1),
    1,
    0
)

# Keep only rows with signals
dfHighFrame = dfHighFrame[
    (dfHighFrame['buyingSignalHighFrame'] == 1) |
    (dfHighFrame['sellingSignalHighFrame'] == 1) |
    (dfHighFrame['closingSignalHighFrame'] == 1)
]

# Create a key field to map the Buy and Sell signals to the Low Frame
dfHighFrame['mergeKey'] = (
        dfHighFrame['instrument'].astype(str) + '|' +
        dfHighFrame['dateYYYYMMDD'].astype(str) + '|' +
        dfHighFrame['hour'].astype(str).str.zfill(2) +
        dfHighFrame['minute'].astype(str).str.zfill(2) +
        dfHighFrame['second'].astype(str).str.zfill(2)
)

# Keep only relevant fields: key + signal fields
dfHighFrameBuyCloseSignals = dfHighFrame[[
    'mergeKey',
    'buyingSignalHighFrame',
    'sellingSignalHighFrame',
    'closingSignalHighFrame'
]]

# </editor-fold>

# <editor-fold desc=" ===== Map High Frame Buy and Sell Signals =========== ">
dfLowFrame['mergeKey'] = (
        dfLowFrame['instrument'].astype(str) + '|' +
        dfLowFrame['dateYYYYMMDD'].astype(str) + '|' +
        dfLowFrame['hour'].astype(str).str.zfill(2) +
        dfLowFrame['minute'].astype(str).str.zfill(2) +
        dfLowFrame['second'].astype(str).str.zfill(2)
)

dfMerged = pd.merge(
    dfLowFrame, dfHighFrameBuyCloseSignals, on='mergeKey', how='left'
)

# Fill the signals with the mapped High Frame signals
# Note that we need to shift(-1) so the signal appears just before
# the time we actually need to open
# (See scripts.Actions_Transformation_Model.xlsx if this is not clear)
dfMerged['buyingSignal'] = np.where(
    (dfMerged['buyingSignalHighFrame'].shift(-1) == 1),
    1,
    dfMerged['buyingSignal'].fillna(0)
)

dfMerged['sellingSignal'] = np.where(
    (dfMerged['sellingSignalHighFrame'].shift(-1) == 1),
    1,
    dfMerged['sellingSignal'].fillna(0)
)

# To avoid confusion, we will only retain the closing signal if there is
# no other signal at the same time (buy or sell)
dfMerged['closingSignal'] = np.where(
    # (dfMerged['closingSignalHighFrame'].shift(-1) == 1),
    (dfMerged['closingSignalHighFrame'].shift(-1) == 1) &
    (dfMerged['buyingSignal'] == 0) &
    (dfMerged['sellingSignal'] == 0),
    1,
    dfMerged['closingSignal'].fillna(0)
)

dfMerged = dfMerged.drop(
    columns=[
        'Unnamed: 0',
        'mergeKey',
        'buyingSignalHighFrame',
        'sellingSignalHighFrame',
        'closingSignalHighFrame'
    ]
)

# </editor-fold>

# <editor-fold desc=" ===== Export Output ============================= ">

dfMerged = round_ohlc_to_five(dfMerged, ohlc=True, signals=True)

dfMerged.to_csv(outputFile)
print(
    'Time lapsed: ' +
    str(outputFile) + " " + str(datetime.now() - startTime)
)

# </editor-fold>

print_time_lapsed(final=True)

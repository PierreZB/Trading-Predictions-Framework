# <editor-fold desc=" ===== Import ======================================== ">
from scripts.project_settings import *
from ta import *
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.preprocessing import QuantileTransformer
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import confusion_matrix, classification_report

# Change pandas display options to show full tables
pd.set_option('display.expand_frame_repr', False)
pd.set_option('display.max_rows', 25)
# </editor-fold>

# <editor-fold desc=" ===== Parameters ==================================== ">
# Type of target (buySell, sellHoldBuy, buyOnly, sellOnly)
targetType = 'buySell'

# Number of variables allowed for each level of correlation
# correlLevel = (MaxCorrelRange, MinCorrelRange, MaxNumberOfVariablesAllowed)
correlLevel1 = (1.00, 0.85, 7)
correlLevel2 = (0.85, 0.75, 5)
correlLevel3 = (0.75, 0.50, 3)

# training data set will represent x% of the original data set
# note: the first x% rows will be used for training and the rest for testing
# this is NOT a random selection
trainingDataSet = 0.9

# When running tests I recommended to limit the number of rows in the data set
# set to 0 to load all rows
rowsLimit = 0  # 10_000

# list of files to process
strategyBacktestingFileList = [
    'EURUSD_H1_20050101_20191026_macdRsiV01_0001-0036-0078-0027-0042_TP99999_SL99999'
]
# </editor-fold>

# <editor-fold desc=" ===== Load data ===================================== ">
for strategyBacktestingFile in strategyBacktestingFileList:

    # Define file paths
    inputFile = (
            str(dataStrategyBacktesting) + '/' +
            str(strategyBacktestingFile) + str(".csv")
    )

    outputFile = (
            str(dataModelsRaw) + '/' +
            str(strategyBacktestingFile.rsplit("_", 2)[0]) +
            '_' + str(targetType) + 'Target'
    )

    df = pd.read_csv(inputFile, sep=",", encoding='utf-8', engine='c')

    df = df.sort_values(
        by=[str('ID')], ascending=True, na_position='first'
    )
    df = df.drop_duplicates(subset='ID')
    df = df.reset_index(drop=True)
    df = df.round({
        # 'volume': 0,
        'open': 5,
        'high': 5,
        'low': 5,
        'close': 5
    })

    if rowsLimit != 0:
        df = df.head(rowsLimit)

    # </editor-fold>

    # <editor-fold desc=" ===== Cleanse data ============================== ">
    # Remove any record prior to 2005-01-01 (bad quality data prior to 2005)
    df['timestamp'] = pd.to_datetime(
        pd.Series(df['timestamp']), format="%Y-%m-%dT%H:%M:%S"
    )

    # df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
    df = df[(
            (df['timestamp'] >= pd.Timestamp('2005-01-01 00:00:00+00:00')) &
            (df['timestamp'] < pd.Timestamp('2020-01-01 00:00:00+00:00'))
    )]

    df['timestamp'] = df['timestamp'].dt.tz_convert('Europe/London')

    # </editor-fold>

    # <editor-fold desc=" ===== Transform data ============================ ">

    if targetType == 'buySell':
        # Convert signalLabel labels to binary 0/1 values
        df['target'] = (df['signalLabel'].values == 'openBuy').astype(np.uint8)
    elif targetType == 'sellHoldBuy':
        # Keep all 3 positions: sell (0), hold (1), buy (2)
        df['target'] = 1

        df['target'] = np.where(
            (df['buyingSignal'] == 1) &
            (df['sellingSignal'] == 0) &
            (df['closingSignal'] == 0) &
            (df['signalLabel'].values == 'openBuy'),
            2,
            df['target']
        )

        df['target'] = np.where(
            (df['sellingSignal'] == 1) &
            (df['buyingSignal'] == 0) &
            (df['closingSignal'] == 0) &
            (df['signalLabel'].values == 'openSell'),
            0,
            df['target']
        )
    elif targetType == 'buyOnly':
        # Keep buying related signals only: close (0), hold (1), open (2)
        df['target'] = 1

        df['target'] = np.where(
            (df['buyingSignalText'] == 'closeBuy'),
            0,
            df['target']
        )

        df['target'] = np.where(
            (df['buyingSignalText'] == 'openBuy'),
            2,
            df['target']
        )
    elif targetType == 'sellOnly':
        # Keep selling related signals only: close (0), hold (1), open (2)
        df['target'] = 1

        df['target'] = np.where(
            (df['sellingSignalText'] == 'closeSell'),
            0,
            df['target']
        )

        df['target'] = np.where(
            (df['sellingSignalText'] == 'openSell'),
            2,
            df['target']
        )

    # Drop columns which are useless for this case study
    df = df.drop([
        'buyingSignal', 'sellingSignal', 'closingSignal',
        'referencePriceHigher', 'referencePriceLower',
        'pnlPips', 'pnlPercent',
        'buyingSignalText', 'sellingSignalText',
        'statsNumberOfPeriods', 'statsBuyingPosition', 'statsSellingPosition',
        'statsNoActionTaken', 'statsHitTakeProfit', 'statsHitStopLoss',
        'statsHitTakeProfitAndStopLoss'
    ], axis=1)

    # re-arrange columns so that
    # 1st = ID, 2nd = timestamp, 3rd = target, others = metrics
    coreColumns = list(df)
    coreColumns.insert(2, coreColumns.pop(coreColumns.index('target')))
    df = df.loc[:, coreColumns]

    # Generate indicators
    # Time indicators
    df['year'] = pd.DatetimeIndex(df['timestamp']).year
    df['month'] = pd.DatetimeIndex(df['timestamp']).month
    df['week'] = pd.DatetimeIndex(df['timestamp']).week
    df['day'] = pd.DatetimeIndex(df['timestamp']).day
    df['weekday'] = pd.DatetimeIndex(df['timestamp']).weekday
    df['hour'] = pd.DatetimeIndex(df['timestamp']).hour

    print_time_lapsed(file_name='Data loaded and prepared')

    # ========================== Add all indicators ==========================
    """
    # add all ta indicators
    df = add_all_ta_features(
        df, "open", "high", "low", "close", "volume", fillna=True
    )
    # """

    # Define time frames list for indicators loops below
    timeFramesList = [
        3, 6, 14, 20, 24, 30, 36, 40, 48, 60, 66, 78, 90,
        100, 150, 200, 250, 300, 350, 400, 450, 500, 600
    ]

    # ====================== ADX ======================
    # ADXValues = [6, 7, 8]
    ADXValues = timeFramesList
    for index, A in enumerate(ADXValues):
        # dfADX_A = 'adx' + '|' + str(A).zfill(3)
        # df[dfADX_A] = adx(
        #     df['high'], df['low'], df['close'], n=A, fillna=False
        # )

        dfADXPOS_A = 'adx_pos' + '|' + str(A).zfill(3)
        df[dfADXPOS_A] = adx_pos(
            df['high'], df['low'], df['close'], n=A, fillna=False
        )

        dfADXNEG_A = 'adx_neg' + '|' + str(A).zfill(3)
        df[dfADXNEG_A] = adx_neg(
            df['high'], df['low'], df['close'], n=A, fillna=False
        )
    print_time_lapsed(file_name='ADX')

    # ====================== AROON ======================
    # AroonValues = [6, 12, 14, 20]
    AroonValues = timeFramesList
    for index, A in enumerate(AroonValues):
        dfAroonUp_A = 'aroon_up' + '|' + str(A).zfill(3)
        df[dfAroonUp_A] = aroon_up(df['close'], n=A, fillna=False)

        dfAroonDown_A = 'aroon_down' + '|' + str(A).zfill(3)
        df[dfAroonDown_A] = aroon_down(df['close'], n=A, fillna=False)

        dfAroonInd_A = 'aroon_ind' + '|' + str(A).zfill(3)
        df[dfAroonInd_A] = df[dfAroonUp_A] - df[dfAroonDown_A]
    print_time_lapsed(file_name='AROON')

    # ====================== CLOSE/EMA ======================
    # closeEMAValues = [12, 14, 20]
    closeEMAValues = timeFramesList
    for index, A in enumerate(closeEMAValues):
        dfCloseEMA_A = 'close_ema' + '|' + str(A).zfill(3)
        df[dfCloseEMA_A] = (
                df['close'] / ema_indicator(df['close'], n=A, fillna=False)
        )
    print_time_lapsed(file_name='CLOSE/EMA')

    # ====================== CMF ======================
    # CMFValues = [6, 12, 14, 20]
    CMFValues = timeFramesList
    for index, A in enumerate(CMFValues):
        dfCMF_A = 'cmf' + '|' + str(A).zfill(3)
        df[dfCMF_A] = chaikin_money_flow(
            df['high'], df['low'], df['close'], df['volume'], n=A, fillna=False
        )
    print_time_lapsed(file_name='CMF')

    # ====================== MACD ======================
    # MACDValues = [3, 6, 12, 14, 20, 24, 36]
    MACDValues = timeFramesList
    MACD_cartesian_product = [(a, b) for a in MACDValues for b in MACDValues]
    for index, MACD_A_B in enumerate(MACD_cartesian_product):
        A, B = MACD_A_B
        if A < B:
            dfMACD_A_B = 'macd' + '|' + str(A).zfill(3) + '_' + str(B).zfill(3)
            df[dfMACD_A_B] = macd(
                df['close'], n_fast=A, n_slow=B, fillna=False
            )

            dfMACDSIGN_A_B = (
                    'macd_sign' + '|' + str(A).zfill(3) + '_' + str(B).zfill(3)
            )
            df[dfMACDSIGN_A_B] = macd_signal(
                df['close'], n_fast=A, n_slow=B, fillna=False
            )

            dfMACDDIFF_A_B = (
                    'macd_diff' + '|' + str(A).zfill(3) + '_' + str(B).zfill(3)
            )
            df[dfMACDDIFF_A_B] = macd_diff(
                df['close'], n_fast=A, n_slow=B, fillna=False
            )
    print_time_lapsed(file_name='MACD')

    # ====================== MFI ======================
    # MFIValues = [6, 14, 20]
    MFIValues = timeFramesList
    for index, A in enumerate(MFIValues):
        dfMFI_A = 'mfi' + '|' + str(A).zfill(3)
        df[dfMFI_A] = money_flow_index(
            df['high'], df['low'], df['close'], df['volume'], n=A, fillna=False
        )
    print_time_lapsed(file_name='MFI')

    # ====================== AO ======================
    AOValuesA = [3, 5]
    # AOValuesB = [14, 20]
    AOValuesB = timeFramesList
    AO_cartesian_product = [(a, b) for a in AOValuesA for b in AOValuesB]
    for index, AO_A_B in enumerate(AO_cartesian_product):
        A, B = AO_A_B
        dfAO_A_B = 'ao' + '|' + str(A).zfill(3) + '_' + str(B).zfill(3)
        df[dfAO_A_B] = ao(
            df['high'], df['low'], s=A, len=B, fillna=False
        )
    print_time_lapsed(file_name='AO')

    # ====================== RSI ======================
    # RSIValues = [3, 6, 14]
    RSIValues = timeFramesList
    for index, A in enumerate(RSIValues):
        dfRSI_A = 'rsi' + '|' + str(A).zfill(3)
        df[dfRSI_A] = rsi(df['close'], n=A, fillna=False)
    print_time_lapsed(file_name='RSI')

    # ====================== STOCH ======================
    # STOCHValues = [14, 24, 36]
    STOCHValues = timeFramesList
    for index, A in enumerate(STOCHValues):
        dfSTOCH_A = 'stoch' + '|' + str(A).zfill(3)
        df[dfSTOCH_A] = stoch(
            df['high'], df['low'], df['close'], n=A, fillna=False
        )

    # STOCHSValuesA = [6, 14, 24, 36, 48]
    STOCHSValuesA = timeFramesList
    STOCHSValuesB = [3, 5, 7]
    STOCHS_cartesian_product = [
        (a, b) for a in STOCHSValuesA for b in STOCHSValuesB
    ]
    for index, STOCHS_A_B in enumerate(STOCHS_cartesian_product):
        A, B = STOCHS_A_B
        dfSTOCHS_A_B = (
                'stoch_signal' + '|' + str(A).zfill(3) + '_' + str(B).zfill(3)
        )
        df[dfSTOCHS_A_B] = stoch_signal(
            df['high'], df['low'], df['close'], n=A, d_n=B, fillna=False
        )
    print_time_lapsed(file_name='STOCH')

    # ====================== TSI ======================
    # TSIValuesA = [25]
    TSIValuesA = timeFramesList
    TSIValuesB = [13]
    TSI_cartesian_product = [(a, b) for a in TSIValuesA for b in TSIValuesB]
    for index, TSI_A_B in enumerate(TSI_cartesian_product):
        A, B = TSI_A_B
        dfTSI_A_B = 'tsi' + '|' + str(A).zfill(3)
        df[dfTSI_A_B] = tsi(df['close'], r=A, s=B, fillna=False)
    print_time_lapsed(file_name='TSI')

    # ====================== UO ======================
    UOTuples = [(7, 14, 28), (14, 28, 56), (28, 56, 112)]
    for index, UO_A_B_C in enumerate(UOTuples):
        A, B, C = UO_A_B_C
        dfUO_A_B_C = (
                'uo' + '|' +
                str(A).zfill(3) + '_' + str(B).zfill(3) + '_' + str(C).zfill(3)
        )
        df[dfUO_A_B_C] = uo(
            df['high'], df['low'], df['close'],
            s=A, m=B, len=C, ws=4.0, wm=2.0, wl=1.0,
            fillna=False
        )
    print_time_lapsed(file_name='UO')

    # ====================== WR ======================
    # WRValues = [14, 24, 36]
    WRValues = timeFramesList
    for index, A in enumerate(WRValues):
        dfWR_A = 'wr' + '|' + str(A).zfill(3)
        df[dfWR_A] = wr(
            df['high'], df['low'], df['close'], lbp=A, fillna=False
        )
    print_time_lapsed(file_name='WR')

    # ====================== CCI ======================
    # CCIValues = [14, 20, 24, 36, 48]
    CCIValues = timeFramesList
    for index, A in enumerate(CCIValues):
        dfCCI_A = 'cci' + '|' + str(A).zfill(3)
        df[dfCCI_A] = cci(
            df['high'], df['low'], df['close'], n=A, c=0.015, fillna=False
        )
    print_time_lapsed(file_name='CCI')

    # ====================== DPO ======================
    # DPOValues = [20]
    DPOValues = timeFramesList
    for index, A in enumerate(DPOValues):
        dfDPO_A = 'dpo' + '|' + str(A).zfill(3)
        df[dfDPO_A] = dpo(df['close'], n=A, fillna=False)
    print_time_lapsed(file_name='DPO')

    # ====================== VORTEX ======================
    # VRTXValues = [6, 14, 20]
    VRTXValues = timeFramesList
    for index, A in enumerate(VRTXValues):
        dfVRTXPOS_A = 'vortex_ind_pos' + '|' + str(A).zfill(3)
        df[dfVRTXPOS_A] = vortex_indicator_pos(
            df['high'], df['low'], df['close'], n=A, fillna=False
        )
        dfVRTXNEG_A = 'vortex_ind_neg' + '|' + str(A).zfill(3)
        df[dfVRTXNEG_A] = vortex_indicator_neg(
            df['high'], df['low'], df['close'], n=A, fillna=False
        )
    print_time_lapsed(file_name='VORTEX')

    # ====================== TRIX ======================
    # TRIXValues = [3, 4, 6]
    TRIXValues = timeFramesList
    for index, A in enumerate(TRIXValues):
        dfTRIX_A = 'trix' + '|' + str(A).zfill(3)
        df[dfTRIX_A] = trix(df['close'], n=A, fillna=False)
    print_time_lapsed(file_name='TRIX')

    # ====================== BOLLINGER ======================
    # BBIValuesA = [24, 36, 48]
    BBIValuesA = timeFramesList
    BBIValuesB = [2]
    BBI_cartesian_product = [(a, b) for a in BBIValuesA for b in BBIValuesB]
    for index, BBI_A_B in enumerate(BBI_cartesian_product):
        A, B = BBI_A_B
        dfBBHI_A_B = (
            'bollingerBHI' + '|' + str(A).zfill(3) + '_' + str(B).zfill(3)
        )
        df[dfBBHI_A_B] = bollinger_hband_indicator(
            df['close'], n=A, ndev=B, fillna=False
        )

        dfBBLI_A_B = (
            'bollingerBLI' + '|' + str(A).zfill(3) + '_' + str(B).zfill(3)
        )
        df[dfBBLI_A_B] = bollinger_lband_indicator(
            df['close'], n=A, ndev=B, fillna=False
        )
    print_time_lapsed(file_name='BOLLINGER')

    # ====================== DONCHIAN ======================
    # DCIValues = [12, 14, 20]
    DCIValues = timeFramesList
    for index, DCI_A in enumerate(DCIValues):
        A = DCI_A
        dfDCHI_A = (
            'donchianCHI' + '|' + str(A).zfill(3)
        )
        df[dfDCHI_A] = donchian_channel_hband_indicator(
            df['close'], n=A, fillna=False
        )

        dfDCLI_A = (
            'donchianCLI' + '|' + str(A).zfill(3)
        )
        df[dfDCLI_A] = donchian_channel_lband_indicator(
            df['close'], n=A, fillna=False
        )
    print_time_lapsed(file_name='DONCHIAN')

    # ====================== EMA ======================
    # EMAValues = [5, 12]
    EMAValues = timeFramesList
    for index, A in enumerate(EMAValues):
        dfEMA_A = 'ema' + '|' + str(A).zfill(3)
        df[dfEMA_A] = ema_indicator(df['close'], n=A, fillna=False)
    print_time_lapsed(file_name='EMA')

    # ====================== KST ======================
    df['trend_kst'] = kst(
        df['close'], r1=10, r2=15, r3=20, r4=30, n1=10, n2=10, n3=10, n4=15,
        fillna=False
    )
    df['trend_kst_sig'] = kst_sig(
        df['close'],
        r1=10, r2=15, r3=20, r4=30, n1=10, n2=10, n3=10, n4=15, nsig=9,
        fillna=False
    )
    df['trend_kst_diff'] = df['trend_kst'] - df['trend_kst_sig']
    print_time_lapsed(file_name='KST')

    # ====================== ADI ======================
    df['ADI'] = acc_dist_index(
        df['high'], df['low'], df['close'], df['volume'], fillna=False
    )
    print_time_lapsed(file_name='ADI')

    # ====================== VPT ======================
    df['VPT'] = volume_price_trend(df['close'], df['volume'], fillna=False)
    print_time_lapsed(file_name='VPT')


    # """
    # </editor-fold>

    # <editor-fold desc=" ===== Reshape data frame ======================== ">
    # Keep only records where an opening signal exists
    # and make sure there's no NaN
    df = df[
        ((df['signalLabel'] == 'openBuy') |
         (df['signalLabel'] == 'openSell'))
    ]

    # Remove records containing NaN and Reset Index
    df = df.dropna()
    df = df.reset_index(drop=True)
    # </editor-fold>

    # <editor-fold desc=" ===== Calculate Correlations ==================== ">

    dfCorr = df.corrwith(df['target'])  # calculate correlation with target
    dfCorr = dfCorr.drop('target')  # drop target vs target correlation row
    dfCorr = dfCorr.abs()  # convert correlation to absolute values
    dfCorr = dfCorr.to_frame().reset_index()  # convert series to data frame

    # rename columns for clarity
    dfCorr = dfCorr.rename(columns={"index": "variable", 0: "correlation"})

    # In case of multiple versions of the same indicator,
    # we will want to keep only the best one
    dfCorrConcat = pd.DataFrame([])
    corrLvlRanges = [(1.00, 0.85, 7), (0.85, 0.75, 5), (0.75, 0.50, 5)]
    # corrLvlRanges = [(1, 0.9)]
    for index, corrLvlRange in enumerate(corrLvlRanges):
        corrRangeUp, corrRangeDown, corrHead = corrLvlRange

        dfCorrTmp1 = dfCorr
        dfCorrTmp1['indicatorGroup'] = (
            dfCorr['variable'].apply(lambda st: st.rsplit("|", 1)[0])
        )
        dfCorrTmp1 = dfCorrTmp1[
            (dfCorr['correlation'] < corrRangeUp) &
            (dfCorr['correlation'] > corrRangeDown)
        ]

        dfCorrTmp2 = dfCorrTmp1[['correlation', 'indicatorGroup']]
        dfCorrTmp2 = dfCorrTmp2.groupby('indicatorGroup').max()

        dfCorrJoin = pd.merge(dfCorrTmp2, dfCorrTmp1, on='correlation')

        # keep only x greatest correlation values
        dfCorrJoin = (
            dfCorrJoin
            .sort_values(by=['correlation'], ascending=False)
            .head(corrHead)
        )

        # Concatenate the output of each loop
        dfCorrConcat = pd.concat(
            [dfCorrConcat, dfCorrJoin],
            ignore_index=True,
            sort=False
        )

    print('\n' + 'Chosen variables + Correlation with target:' + '\n')
    print(dfCorrConcat)

    indicatorsColumns = dfCorrConcat['variable'].tolist()
    dfKeepColumns = coreColumns + indicatorsColumns

    del dfCorr, dfCorrConcat, corrLvlRanges

    df = df[dfKeepColumns]
    df = df.drop(['signalLabel'], axis=1)

    print('\n')
    print_time_lapsed(file_name='Data frame ready with best indicators')
    # </editor-fold>

    # <editor-fold desc=" ===== Export data =============================== ">

    df.to_csv(str(outputFile + '.csv'), index=False)
    print_time_lapsed(file_name='CSV saved: ' + outputFile)

    # </editor-fold>

    # <editor-fold desc=" ===== Clustering ================================ ">

    # split variables and targets + remove fields that can't be pre-processed
    dfData = df.drop(['ID', 'timestamp', 'target'], axis=1)
    dfTarget = df[['target']]

    # Pre-process variables and convert to numpy arrays
    qt = QuantileTransformer()
    data = qt.fit_transform(dfData)
    target = dfTarget.values

    # Get number of rows in df to split data set
    rowsDf, colsDf = data.shape
    trainRows = round(rowsDf * 0.9)
    testRows = round(rowsDf - trainRows)

    # Split into training and test data sets
    X_train = data[:trainRows, :]
    X_test = data[testRows:, :]
    y_train = target[:trainRows, :]
    y_test = target[testRows:, :]

    y_train = y_train.ravel()
    y_test = y_test.ravel()

    # delete original df
    del df, data, target

    print_time_lapsed(file_name='Pre-process + data split')

    # Neural Network training
    nnMLPC = MLPClassifier(
        hidden_layer_sizes=(50,),
        activation='tanh',
        solver='adam',
        alpha=0.0001,
        max_iter=400,

    )
    nnMLPC.fit(X_train, y_train)
    predictionMLPC = nnMLPC.predict(X_test)

    print('\n')
    print_time_lapsed(file_name='Neural Network Fit & Predict')

    # Check model's performance
    print('\n' + 'Neural Network classification_report:' + '\n')
    print(classification_report(y_test, predictionMLPC))

    print('\n' + 'Neural Network confusion_matrix:' + '\n')
    print(confusion_matrix(y_test, predictionMLPC))

    print('\n')
    print_time_lapsed(file_name='Neural Network Score')
    # </editor-fold>

print_time_lapsed(final=True)

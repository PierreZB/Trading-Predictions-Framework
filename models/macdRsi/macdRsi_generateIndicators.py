# <editor-fold desc=" ===== Import ======================================== ">
from scripts.project_settings import *
from ta import *
from datetime import datetime
import numpy as np
import pandas as pd

# Change pandas display options to show full tables
pd.set_option('display.expand_frame_repr', False)
pd.set_option('display.max_rows', 25)
# </editor-fold>

# <editor-fold desc=" ===== Load data ===================================== ">
targetType = 'true3'

strategyBacktestingFileList = [
    'EURUSD_H1_20050101_20191026_macdRsiV02_0001-0036-0078-0027-00420200-0080-0040-0040_TP99999_SL99999'
]


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

    if targetType == 'binary':
        # Convert signalLabel labels to binary 0/1 values
        df['target'] = (df['signalLabel'].values == 'openBuy').astype(np.uint8)
    elif targetType == 'true3':
        # Keep all 3 positions: buy (2), sell (0), hold (1)
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
    cols = list(df)
    cols.insert(2, cols.pop(cols.index('target')))
    df = df.loc[:, cols]

    # Generate indicators
    # Time indicators
    df['year'] = pd.DatetimeIndex(df['timestamp']).year
    df['month'] = pd.DatetimeIndex(df['timestamp']).month
    df['week'] = pd.DatetimeIndex(df['timestamp']).week
    df['day'] = pd.DatetimeIndex(df['timestamp']).day
    df['weekday'] = pd.DatetimeIndex(df['timestamp']).weekday
    df['hour'] = pd.DatetimeIndex(df['timestamp']).hour

    print_time_lapsed(file_name='Data loaded and prepared')

    # =========================== Price evolution ===========================
    priceDeltaValues = [
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 16, 20, 24, 36, 48, 72, 96
    ]
    for index, A in enumerate(priceDeltaValues):
        dfPriceDelta_A = 'priceDelta' + str(A).zfill(3)
        df[dfPriceDelta_A] = df['close'].shift(-A) / df['close'] - 1
        # df[dfPriceDelta_A] = 0
        # df[dfPriceDelta_A] = np.where(
        #    (df['close'].shift(-A) / df['close'] - 1) > 0.0004,
        #     1,
        #     df[dfPriceDelta_A]
        # )
        # df[dfPriceDelta_A] = np.where(
        #     (df['close'].shift(-A) / df['close'] - 1) < -0.0004,
        #     -1,
        #     df[dfPriceDelta_A]
        # )
    print_time_lapsed(file_name='priceDelta')

    # ============================ Add indicators ============================
    # """
    # add all ta indicators
    df = add_all_ta_features(
        df, "open", "high", "low", "close", "volume", fillna=True
    )
    # """

    # Define time frames list for indicators loops below
    timeFramesList = [
        3, 6, 14, 24, 36, 48, 78, 100, 150, 200, 300, 400
    ]

    # ====================== ADX ======================
    # ADXValues = [6, 7, 8]
    ADXValues = timeFramesList
    for index, A in enumerate(ADXValues):
        # dfADX_A = 'adx' + '_' + str(A).zfill(3)
        # df[dfADX_A] = adx(
        #     df['high'], df['low'], df['close'], n=A, fillna=False
        # )

        dfADXPOS_A = 'adx_pos' + '_' + str(A).zfill(3)
        df[dfADXPOS_A] = adx_pos(
            df['high'], df['low'], df['close'], n=A, fillna=False
        )

        dfADXNEG_A = 'adx_neg' + '_' + str(A).zfill(3)
        df[dfADXNEG_A] = adx_neg(
            df['high'], df['low'], df['close'], n=A, fillna=False
        )
    print_time_lapsed(file_name='ADX')

    # ====================== AROON ======================
    # AroonValues = [6, 12, 14, 20]
    AroonValues = timeFramesList
    for index, A in enumerate(AroonValues):
        dfAroonUp_A = 'aroon_up' + '_' + str(A).zfill(3)
        df[dfAroonUp_A] = aroon_up(df['close'], n=A, fillna=False)

        dfAroonDown_A = 'aroon_down' + '_' + str(A).zfill(3)
        df[dfAroonDown_A] = aroon_down(df['close'], n=A, fillna=False)

        dfAroonInd_A = 'aroon_ind' + '_' + str(A).zfill(3)
        df[dfAroonInd_A] = df[dfAroonUp_A] - df[dfAroonDown_A]
    print_time_lapsed(file_name='AROON')

    # ====================== CLOSE/EMA ======================
    # closeEMAValues = [12, 14, 20]
    closeEMAValues = timeFramesList
    for index, A in enumerate(closeEMAValues):
        dfCloseEMA_A = 'close_ema' + '_' + str(A).zfill(3)
        df[dfCloseEMA_A] = (
                df['close'] / ema_indicator(df['close'], n=A, fillna=False)
        )
    print_time_lapsed(file_name='CLOSE/EMA')

    # ====================== CMF ======================
    CMFValues = [6, 12, 14, 20]
    CMFValues = timeFramesList
    for index, A in enumerate(CMFValues):
        dfCMF_A = 'cmf' + '_' + str(A).zfill(3)
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
            dfMACD_A_B = 'macd' + '_' + str(A).zfill(3) + '_' + str(B).zfill(3)
            df[dfMACD_A_B] = macd(
                df['close'], n_fast=A, n_slow=B, fillna=False
            )

            dfMACDSIGN_A_B = (
                    'macd_sign' + '_' + str(A).zfill(3) + '_' + str(B).zfill(3)
            )
            df[dfMACDSIGN_A_B] = macd_signal(
                df['close'], n_fast=A, n_slow=B, fillna=False
            )

            dfMACDDIFF_A_B = (
                    'macd_diff' + '_' + str(A).zfill(3) + '_' + str(B).zfill(3)
            )
            df[dfMACDDIFF_A_B] = macd_diff(
                df['close'], n_fast=A, n_slow=B, fillna=False
            )
    print_time_lapsed(file_name='MACD')

    # ====================== MFI ======================
    # MFIValues = [6, 14, 20]
    MFIValues = timeFramesList
    for index, A in enumerate(MFIValues):
        dfMFI_A = 'mfi' + '_' + str(A).zfill(3)
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
        dfAO_A_B = 'ao' + '_' + str(A).zfill(3) + '_' + str(B).zfill(3)
        df[dfAO_A_B] = ao(
            df['high'], df['low'], s=A, len=B, fillna=False
        )
    print_time_lapsed(file_name='AO')

    # ====================== RSI ======================
    # RSIValues = [3, 6, 14]
    RSIValues = timeFramesList
    for index, A in enumerate(RSIValues):
        dfRSI_A = 'rsi' + '_' + str(A).zfill(3)
        df[dfRSI_A] = rsi(df['close'], n=A, fillna=False)
    print_time_lapsed(file_name='RSI')

    # ====================== STOCH ======================
    # STOCHValues = [14, 24, 36]
    STOCHValues = timeFramesList
    for index, A in enumerate(STOCHValues):
        dfSTOCH_A = 'stoch' + '_' + str(A).zfill(3)
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
                'stoch_signal' + '_' + str(A).zfill(3) + '_' + str(B).zfill(3)
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
        dfTSI_A_B = 'tsi' + '_' + str(A).zfill(3)
        df[dfTSI_A_B] = tsi(df['close'], r=A, s=B, fillna=False)
    print_time_lapsed(file_name='TSI')

    # ====================== UO ======================
    UOTuples = [(7, 14, 28), (14, 28, 56), (28, 56, 112)]
    for index, UO_A_B_C in enumerate(UOTuples):
        A, B, C = UO_A_B_C
        dfUO_A_B_C = (
                'uo' + '_' +
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
        dfWR_A = 'wr' + '_' + str(A).zfill(3)
        df[dfWR_A] = wr(
            df['high'], df['low'], df['close'], lbp=A, fillna=False
        )
    print_time_lapsed(file_name='WR')

    # ====================== CCI ======================
    # CCIValues = [14, 20, 24, 36, 48]
    CCIValues = timeFramesList
    for index, A in enumerate(CCIValues):
        dfCCI_A = 'cci' + '_' + str(A).zfill(3)
        df[dfCCI_A] = cci(
            df['high'], df['low'], df['close'], n=A, c=0.015, fillna=False
        )
    print_time_lapsed(file_name='CCI')

    # ====================== DPO ======================
    # DPOValues = [20]
    DPOValues = timeFramesList
    for index, A in enumerate(DPOValues):
        dfDPO_A = 'dpo' + '_' + str(A).zfill(3)
        df[dfDPO_A] = dpo(df['close'], n=A, fillna=False)
    print_time_lapsed(file_name='DPO')

    # ====================== VORTEX ======================
    # VRTXValues = [6, 14, 20]
    VRTXValues = timeFramesList
    for index, A in enumerate(VRTXValues):
        dfVRTXPOS_A = 'vortex_ind_pos' + '_' + str(A).zfill(3)
        df[dfVRTXPOS_A] = vortex_indicator_pos(
            df['high'], df['low'], df['close'], n=A, fillna=False
        )
        dfVRTXNEG_A = 'vortex_ind_neg' + '_' + str(A).zfill(3)
        df[dfVRTXNEG_A] = vortex_indicator_neg(
            df['high'], df['low'], df['close'], n=A, fillna=False
        )
    print_time_lapsed(file_name='VORTEX')

    # ====================== TRIX ======================
    # TRIXValues = [3, 4, 6]
    TRIXValues = timeFramesList
    for index, A in enumerate(TRIXValues):
        dfTRIX_A = 'trix' + '_' + str(A).zfill(3)
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
            'bollingerBHI' + '_' + str(A).zfill(3) + '_' + str(B).zfill(3)
        )
        df[dfBBHI_A_B] = bollinger_hband_indicator(
            df['close'], n=A, ndev=B, fillna=False
        )

        dfBBLI_A_B = (
            'bollingerBLI' + '_' + str(A).zfill(3) + '_' + str(B).zfill(3)
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
            'donchianCHI' + '_' + str(A).zfill(3)
        )
        df[dfDCHI_A] = donchian_channel_hband_indicator(
            df['close'], n=A, fillna=False
        )

        dfDCLI_A = (
            'donchianCLI' + '_' + str(A).zfill(3)
        )
        df[dfDCLI_A] = donchian_channel_lband_indicator(
            df['close'], n=A, fillna=False
        )
    print_time_lapsed(file_name='DONCHIAN')

    # ====================== EMA ======================
    # EMAValues = [5, 12]
    EMAValues = timeFramesList
    for index, A in enumerate(EMAValues):
        dfEMA_A = 'ema' + '_' + str(A).zfill(3)
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

    df = df.drop(['signalLabel'], axis=1)

    # Remove records containing NaN and Reset Index
    df = df.dropna()
    df = df.reset_index(drop=True)

    # Export the data set for manual analysis in Orange3
    df.to_csv(str(outputFile + '.csv'), index=False)
    print_time_lapsed(file_name=outputFile)

    # </editor-fold>

print_time_lapsed(final=True)

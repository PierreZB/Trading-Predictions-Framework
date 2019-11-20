import datetime as dt
import numpy as np
import requests
from pandas.io.json import json_normalize
from scripts.project_settings import *
from scripts.oanda_api_headers_private import headers
# from scripts.oanda_api_headers.py import headers

# <editor-fold desc=" ===== Extraction Settings =========================== ">
'''----------------------------------------------------------------
Variables defining the scope of data to extract
Note that for now, you can only load granularity from H5
This is due to the fact that the API call is restricted to 500 recs
and the script is currently written to extract 1 day of data at a time
(S5 to M2 will not load the complete data set)
----------------------------------------------------------------'''

# TODO [3] extract the list of instruments available on the platform
instruments_load_list = ['GBP_USD']  # 'GBP_USD', 'AUD_NZD', 'XCU_USD', 'BCO_USD'

# 'S5', 'S10', 'S15', 'S30', 'M1', 'M2', 'M5',
# 'M10', 'M15', 'M30', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H8', 'H12', 'D',
# 'W', 'M'
granularity_load_list = [
    'M15', 'M30', 'H1', 'H6', 'H12', 'D', 'W'
]

# Date range - data is extracted 1 day at a time
year = 2019
dateFrom = dt.date(year, 1, 1)
dateTo = dt.date(year, 10, 26)
# </editor-fold>

# TODO [2] analyse existing data to avoid querying already existing data

# Generate list of date to load, as strings
numDays = abs((dateTo - dateFrom).days)
datesLoadList = [
    (dateFrom + dt.timedelta(days=x))
    for x in range(0, numDays + 1)
    ]

""" # Generate the list of values we want to extract with a cartesian product
I was having an issue with this script:
I wanted to be able to concatenate and export as one file all the data related
to the same instrument and same granularity (therefore, for one instrument
and one granularity, concatenate the different dates, and only then export 
the output)

However, I needed a way to establish the fact that a new set of 
instrument / granularity has begun to cleanse the temporary data frames, 
and also confirm that a specific date is the last one to concatenate before 
exporting the file.

I could have used a triple nested for, but it made the script look quite bad 
because of the indentation.

So I decided to make sure the extractList would be sorted by default this way:
Indicator, Granularity, Dates
And also, I added a flag in the each tuple in that list to flag 
the first date (1) the last date (-1) and any other date in between (0).

It might not be hte most elegant solution yet, 
but so far it's still the best I could think of!

Note: this is how the list used to be generated (list comprehension)
extractList = [
    (date, instrument, granularity)
    for date in datesLoadList
    for instrument in instruments_load_list
    for granularity in granularity_load_list
    ]
"""

extractList = []
for instrument in instruments_load_list:
    for granularity in granularity_load_list:
        for date in datesLoadList:
            if date == dateFrom:
                extractList.append((1, date, instrument, granularity))
            elif date == dateTo:
                extractList.append((-1, date, instrument, granularity))
            else:
                extractList.append((0, date, instrument, granularity))

# Loop through all tuples from the cartesian product, and unpack values
for index, dateInstrGran in enumerate(extractList):
    print(
        str(index) + ' ' + str(dateInstrGran) +
        ' (' + str(datetime.now() - startTime) + ')'
    )
    dateFlag, dateAPIFrom, instrument, granularity = dateInstrGran

    # Calculate the dates "to", based on the current "from" date
    dateAPITo = dateAPIFrom + dt.timedelta(days=1)

    # Generate empty data frames when reaching first date in the list
    if dateFlag == 1:
        """  
        # This method to create empty df is in the end taking more space 
        # than 4 statements; so I'll keep it simple...
        data_frames_list = [
            'df_raw', 'df_candles', 'df_parsed', 'df_rawConcat'
        ]
        for dataFrameX in data_frames_list:
            exec(dataFrameX + ' = pd.DataFrame([])')
        del data_frames_list
        """

        df_raw = pd.DataFrame([])
        df_candles = pd.DataFrame([])
        df_parsed = pd.DataFrame([])
        df_rawConcat = pd.DataFrame([])

    # Define the API GET address
    address = (
        'https://api-fxpractice.oanda.com/v3/instruments/' +
        str(instrument) + '/candles?price=A' +
        '&from=' + str(dateAPIFrom) +
        '&to=' + str(dateAPITo) +
        '&granularity=' + str(granularity) +
        '&smooth=True'
    )

    # Call API to retrieve JSON
    response = requests.get(address, headers=headers)
    response2object = response.json()

    # Check if query returned no errors
    if str(response2object)[2:7] != 'error':

        # Normalise the JSON response
        df_raw = json_normalize(
            response2object, record_path=['candles'],
            meta=['instrument', 'granularity'], sep='.'
        )

        # Check size of the normalised JSON
        df_rawCount = df_raw['instrument'].count()

        # if the table has more than 0 records then process, else next loop
        if df_rawCount > 0:

            # Extract the candles
            df_candles = pd.DataFrame(
                (d for idx, d in df_raw['ask'].iteritems())
                ).fillna(0)

            # concat both data sets created previously
            df_parsed = pd.concat(
                [df_raw.drop('ask', axis=1), df_candles], axis=1
                )

            # Remove values from df
            df_raw.drop(df_raw.index, inplace=True)
            df_candles.drop(df_candles.index, inplace=True)
            df_raw = pd.DataFrame()
            df_candles = pd.DataFrame()

            # Generate date and time fields
            df_parsed['timestamp'] = pd.to_datetime(
                pd.Series(df_parsed['time']),
                format="%Y-%m-%dT%H:%M:%S.000000000Z"
                ).dt.tz_localize('UTC')

            df_parsed['dateYYYYMMDD'] = (
                df_parsed['timestamp'].dt.strftime('%Y%m%d').astype(int)
                )
            df_parsed['timeHHMMSS'] = (
                df_parsed['timestamp'].dt.strftime('%H%M%S').astype(str)
                )

            df_parsed['year'] = df_parsed['time'].str[:4]
            df_parsed['month'] = df_parsed['time'].str[5:-23]
            df_parsed['day'] = df_parsed['time'].str[8:-20]
            df_parsed['hour'] = df_parsed['time'].str[11:-17]
            df_parsed['minute'] = df_parsed['time'].str[14:-14]
            df_parsed['second'] = df_parsed['time'].str[17:-11]

            # Create an ID field
            df_parsed['ID'] = (
                df_parsed['instrument'] + '|' +
                df_parsed['granularity'] + '|' +
                df_parsed['year'] +
                df_parsed['month'] +
                df_parsed['day'] + '|' +
                df_parsed['hour'] +
                df_parsed['minute'] +
                df_parsed['second']
                )

            # Create Signal Flags for user Strategy input
            df_parsed['buyingSignal'] = 0
            df_parsed['sellingSignal'] = 0
            df_parsed['closingSignal'] = 0
            df_parsed['referencePriceHigher'] = 0
            df_parsed['referencePriceLower'] = 0

            # Change columns names and order
            df_parsed = df_parsed.rename(
                index=str,
                columns={
                    "o": "open",
                    "h": "high",
                    "l": "low",
                    "c": "close"
                    }
                )

            # Keep only default fields
            df_parsed = df_parsed[defaultColumnsList]

            # Concatenate the output of each loop
            df_rawConcat = pd.concat(
                [df_rawConcat, df_parsed],
                ignore_index=True,
                sort=False
            )

    # When reaching first date in the list
    if dateFlag == -1:
        # Format numbers, sort by ID, remove duplicates, reindex
        df_rawConcat = sort_deduplicate_reindex_data_frame(
            data_frame=df_rawConcat, index_field='ID', csv_source_file=False
        )

        # TODO [3] extract more records at once or loop through another value
        """ 
        These duplicates exist because with a free account, Oanda 
        limits each query to 500 records, therefore I have set the loop
        to extract data looping over DAYS (which BTW implies that you 
        cannot extract granularity lower than M5).
        This Makes duplicates appear most of the time with granularity 
        higher than H1.
        """

        outputFile = (
                str(dataRawExtracts) + "/" +
                str(
                    str(instrument.replace('_', '',)) + "_" +
                    granularity + "_" +
                    str(dateFrom.strftime("%Y%m%d")) + "_" +
                    str(dateTo.strftime("%Y%m%d"))
                ) +
                str(".csv")
        )

        df_rawConcat.to_csv(outputFile, index=False)

        print_time_lapsed(file_name=outputFile)

print_time_lapsed(final=True)

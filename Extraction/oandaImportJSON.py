"""Markdown
Date        | Version   | Author    | Notes
20180901    | v1.0      | PZB       | File creation
20190521    | v1.1      | PZB       | Code optimisation
"""

# import requests
import pandas as pd
import datetime as dt
from pandas.io.json import json_normalize
from typing import List
from headers_private import headers
# from headers import headers
from pathlib import Path
from extractionSettings import (
    instruments as instruments_load_list,
    granularities as granularities_load_list,
    dateFrom,
    dateTo
)

# Define file paths
dataFolder = Path("../Data/")

# Generate empty data frames
dataFramesList = ['df_raw', 'df_candles', 'df_parsed', 'df_rawConcat']  # type: List[str]
for dataFrameX in dataFramesList:
    exec(dataFrameX + ' = pd.DataFrame([])')
    dataFrameX = pd.DataFrame([])

# Generate list of date to load, as strings
numDays = abs((dateTo - dateFrom).days)
datesLoadList = [
    (dateFrom + dt.timedelta(days=x))
    for x in range(0, numDays + 1)
    ]

# Generate the list of values we want to extract with a cartesian product
extractList = [
    (date, instrument, granularity)
    for date in datesLoadList
    for instrument in instruments_load_list
    for granularity in granularities_load_list
    ]

# Loop through all tuples from the cartesian product, and unpack values
for index, dateInstrGran in enumerate(extractList):
    dateAPIFrom, instrument, granularity = dateInstrGran

    # Calculate the dates "to", based on the current "from" date
    dateAPITo = dateAPIFrom + dt.timedelta(days=1)

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

        # Check size of the nromalised JSON
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
                )
            df_parsed['dateYYYMMDD'] = (
                df_parsed['timestamp'].dt.strftime('%Y%m%d')
                )
            df_parsed['timeHHMMSS'] = (
                df_parsed['timestamp'].dt.strftime('%H%M%S')
                )

            df_parsed['year'] = df_parsed['time'].str[:4]
            df_parsed['month'] = df_parsed['time'].str[5:-23]
            df_parsed['day'] = df_parsed['time'].str[8:-20]
            df_parsed['hour'] = df_parsed['time'].str[11:-17]
            df_parsed['minute'] = df_parsed['time'].str[14:-14]
            df_parsed['second'] = df_parsed['time'].str[14:-14]

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
            df_parsed = df_parsed[[
                'ID',
                'instrument',
                'granularity',
                'timestamp',
                'volume',
                'open',
                'high',
                'low',
                'close',
                'complete',
                'dateYYYMMDD',
                'timeHHMMSS',
                'year',
                'month',
                'day',
                'hour',
                'minute',
                'second'
                ]]

            # Concatenate the output of each loop
            df_rawConcat = pd.concat(
                [df_rawConcat, df_parsed],
                ignore_index=True,
                sort=False
            )

# Format numbers
df_rawConcat.round({
    'volume': 0,
    'open': 5,
    'high': 5,
    'low': 5,
    'close': 5
    })

# Export output
# print(df_rawConcat)
df_rawConcat.to_csv(dataFolder / "df_rawConcat.csv")
df_rawConcat.to_json(dataFolder / "df_rawConcat.json", orient='index')

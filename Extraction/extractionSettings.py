import datetime as dt

'''----------------------------------------------------------------
Variables defining the scope of data to extract
Note that for now, you can only load granularities from H5
This is due to the fact that the API call is trstricted to 500 recs
and the script is currently written to extract 1 day of data at a time
(S5 to M2 will not load the complete data set)
----------------------------------------------------------------'''

# I am still looking for a way to extract the list of
# instruments available on the platform
instruments = ['EUR_USD']

# S5, S10, S15, S30, M1, M2, M5, M10, M15, M30,
# H1, H2, H3, H4, H5, H6, H8, H12, D, W, M
granularities = ['H1']

# Date range - data is extracted 1 day at a time
dateFrom = dt.date(2018, 8, 27)
dateTo = dt.date(2018, 10, 2)

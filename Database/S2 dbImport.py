import pandas as pd
from sqlalchemy import create_engine


#   Read raw extract with pandas and import to MYSQL
df = pd.read_csv("Data/df_rawConcat.csv")

#	Validate data types
print (df.dtypes)

#	Use SQL Alchemy to create a connector to MYSQL and use pandas to import data.
engine = create_engine('mysql+mysqlconnector://root:my-secret-pw@localhost/PythonToMysql')
df.to_sql(name='TP Framework',con=engine,index=False,if_exists='append')
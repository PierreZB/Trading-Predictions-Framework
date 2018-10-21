import mysql.connector
from mysql.connector import errorcode


#   Creating Database Tables
DB_NAME = 'PythonToMysql'

#   Prepare a list of tables to be imported to the database.
TABLES = {}

TABLES['TP Framework'] = (
    "CREATE TABLE `TP Framework` ("
    "  ``               VARCHAR(100) NOT NULL PRIMARY KEY,"
    "  `ID`             VARCHAR(100) NOT NULL PRIMARY KEY,"
    "  `instrument`     VARCHAR(20),"
    "  `granularity`    VARCHAR(5),"
    "  `timestamp`      VARCHAR(100),"
    "  `volume`         INT,"
    "  `open`           FLOAT,"
    "  `high`           FLOAT,"
    "  `low`            FLOAT,"
    "  `close`          FLOAT,"
    "  `complete`       VARCHAR(10),"
    "  `dateYYYMMDD`    DATE,"
    "  `timeHHMMSS`     FLOAT,"
    "  `year`           FLOAT,"
    "  `month`          FLOAT,"
    "  `day`            FLOAT,"
    "  `hour`           FLOAT,"
    "  `minute`         FLOAT,"
    "  `second`         FLOAT"
    ") ENGINE=InnoDB")


#   Update database connection credentials
cnx = mysql.connector.connect(user='root', password='my-secret-pw')
cursor = cnx.cursor()

def create_database(cursor):
    try:
        cursor.execute(
            "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(DB_NAME))
    except mysql.connector.Error as err:
        print("Failed creating database: {}".format(err))
        exit(1)

try:
    cursor.execute("USE {}".format(DB_NAME))
except mysql.connector.Error as err:
    print("Database {} does not exists.".format(DB_NAME))
    if err.errno == errorcode.ER_BAD_DB_ERROR:
        create_database(cursor)
        print("Database {} created successfully.".format(DB_NAME))
        cnx.database = DB_NAME
    else:
        print(err)
        exit(1)

for table_name in TABLES:
    table_description = TABLES[table_name]
    try:
        print("Creating table {}: ".format(table_name), end='')
        cursor.execute(table_description)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
            print("already exists.")
        else:
            print(err.msg)
    else:
        print("OK")

cursor.close()
cnx.close()



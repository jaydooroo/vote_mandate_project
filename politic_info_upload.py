import sqlite3
import pandas as pd

conn = sqlite3.connect('total_info.db')

# Load Data File
df_senate_data = pd.read_csv('1976-2020-senate.csv')

df_house_data = pd.read_csv('1976-2020-house.csv')

df_nominate = pd.read_csv('HSall_members.csv')



# Data Clean up

print(df_senate_data.columns.str.strip())
print(df_senate_data.columns)
df_nominate.columns.str.strip()
print(df_nominate.columns)
df_house_data.columns.str.strip()
# Create/connect to a SQLite database

print(df_senate_data['candidate'])
# for value in df_senate_data['candidate']:
#     print(value)

# Load data file to SQLite
df_senate_data.to_sql('from1976to2020_senate', conn, if_exists='replace')
df_nominate.to_sql('HSall_members', conn, if_exists='replace')
df_house_data.to_sql('from1976to2020_house',conn, if_exists='replace')
# close connection
conn.close()

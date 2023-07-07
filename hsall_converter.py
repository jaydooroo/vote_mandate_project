import sqlite3
import pandas as pd
from difflib import SequenceMatcher
import numpy as np
import math


class hsall_converter:

    def __init__(self, conn):
        self.conn = conn

    def upload_df_to_database(self, df: pd.DataFrame, name: str):
        df.to_sql(name, self.conn, if_exists='replace')

    def convert_HSall_database(self):
        query = """
          SELECT *
          FROM HSall_members;
          """

        df_hsall = pd.read_sql_query(query, self.conn)
        error_df = self.hsall_interprete_names(df_hsall)

        df_hsall = df_hsall.drop(['index'], axis=1)

        if len(error_df) > 0:
            self.upload_df_to_database(error_df, 'HSall_undefined_names')
        self.upload_df_to_database(df_hsall, 'name_modified_HSall')

        return df_hsall, error_df

    def hsall_interprete_names(self, df):

        error_df = pd.DataFrame()
        for index, row in df.iterrows():
            name = row['bioname']
            last_name_arr = name.split(',', 1)
            first_name_arr = last_name_arr[1].split() if len(last_name_arr) > 1 else None
            name_arr = [last_name_arr[0]]
            name_arr = name_arr + first_name_arr

            length = len(name_arr)

            new_name_arr = []

            for i in range(length):
                if '(' in name_arr[i] or ')' in name_arr[i]:
                    pass
                    # new_name = name_arr[i].replace('(', "")
                    # new_name = new_name.replace(')', "")
                    # df.at[index, 'nickname'] = str(new_name).upper()

                elif "JR." == str(name_arr[i]).upper() or "SR." == str(name_arr[i]).upper() or "III" == str(
                        name_arr[i]).upper() \
                        or "II" == str(name_arr[i]).upper() or "JR" == str(name_arr[i]).upper() or "SR" == str(
                    name_arr[i]).upper():
                    # df.at[index, 'suffix'] = str(name_arr[i]).replace('.', "").upper()
                    pass
                else:
                    if ',' in name_arr[i]:
                        name_element = name_arr[i].replace(',', "")
                    else:
                        name_element = name_arr[i]
                    new_name_arr.append(name_element)

            if len(new_name_arr) == 1:
                error_df.append(row)
            else:
                df.at[index, 'last_name'] = str(new_name_arr[0]).upper()
                df.at[index, 'first_name'] = str(new_name_arr[1]).upper()

        return error_df
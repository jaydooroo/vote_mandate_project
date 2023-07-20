import sqlite3
import pandas as pd
from difflib import SequenceMatcher
import numpy as np
import math


class president_converter:

    def __init__(self, conn):
        self.conn = conn

    # upload input df format of data to db as a Table
    # if same name exists in the db. Replace it.
    def upload_df_to_database(self, df: pd.DataFrame, name: str):
        df.to_sql(name, self.conn, if_exists='replace')

    def retrieve_df_from_db(self, table_name):
        query = """
        SELECT *
        FROM {}
        """.format(table_name)

        df = pd.read_sql_query(query, self.conn)

        return df

    # dems_votes_year and gop_votes_year are added and shows only major candidates of each election(dems and gop candidates)
    def convert_database(self):
        query = """  
                DROP TABLE IF EXISTS name_modified_president;
                
                CREATE TABLE name_modified_president AS
                SELECT year, office, candidate, party_detailed, candidatevotes, 
                CAST((CASE WHEN party_detailed  = 'DEMOCRAT' THEN candidatevotes END) AS REAL) AS dems_votes_year, 
                CAST ((CASE WHEN party_detailed = 'REPUBLICAN' THEN candidatevotes END) AS REAL) AS gop_votes_year
				FROM(
                    SELECT year, office, candidate, party_detailed, sum(candidatevotes) as candidatevotes
				    FROM (
                        SELECT year, office, candidate, party_detailed, sum(candidatevotes) as candidatevotes
                        FROM from1976to2020_president
                        GROUP BY year, party_detailed
					    HAVING MAX(candidatevotes)
					)
                    GROUP By year, candidate
                    HAVING MAX(candidatevotes) 
                );

                ALTER TABLE name_modified_president ADD COLUMN totalvotes;
                ALTER TABLE name_modified_president ADD COLUMN state_po;

                UPDATE name_modified_president
                SET dems_votes_year = (
                    SELECT subquery.dems_votes_year
                    FROM(
                        SELECT SUM(dems_votes_year) as dems_votes_year, year
                        FROM name_modified_president
                        GROUP BY year
                    ) AS subquery
                    WHERE subquery.year = name_modified_president.year),
		            
		            gop_votes_year = (
		            SELECT subquery.gop_votes_year 
	                FROM(
                        SELECT SUM(gop_votes_year) as gop_votes_year, year
                        FROM name_modified_president
                        GROUP BY year
                    ) AS subquery
                    WHERE subquery.year = name_modified_president.year),
                    
		            totalvotes = (
		            SELECT subquery.totalvotes
		            FROM (
		                SELECT year, SUM(candidatevotes) as totalvotes
		                FROM name_modified_president
		                GROUP BY year
		            ) AS subquery
		            WHERE subquery.year = name_modified_president.year),
		            
		            state_po = 'USA';
					
				
				CREATE TABLE temp_name_modified_president AS
				SELECT *
				FROM name_modified_president
				WHERE party_detailed  = 'DEMOCRAT' or party_detailed = 'REPUBLICAN';
				
				DROP TABLE IF EXISTS name_modified_president;
				
				ALTER TABLE temp_name_modified_president RENAME TO name_modified_president;
					
		        """
        cursor = self.conn.cursor()

        cursor.executescript(query)

    # automatically assign names from hsall db to the names in the current name_modified_presdient database
    # using similarity.
    def auto_correct_names(self, df_error_names: pd.DataFrame, df_correct_names: pd.DataFrame, limit_similarity):

        for index, row in df_error_names.iterrows():

            if row['office'] == 'US PRESIDENT':
                office = 'President'
                last_name = row['last_name']
                first_name = row['first_name']

                congress_no = ((row['year'] + 1 - 1789) / 2) + 1

                df_error_names.at[index, 'congress'] = congress_no

                correct_rows = df_correct_names.loc[
                    (df_correct_names['congress'] == congress_no) & (df_correct_names['chamber'] == office)]

                for inner_index, inner_row in correct_rows.iterrows():

                    correct_name = inner_row['bioname']
                    error_name = row['candidate']

                    avg_similarity = 0
                    full_similarity = 0

                    if inner_row['first_name'] is not None and first_name is not None:
                        first_similarity = SequenceMatcher(None, inner_row['first_name'], first_name).ratio()
                    if inner_row['last_name'] is not None and last_name is not None:
                        last_similarity = SequenceMatcher(None, inner_row['last_name'], last_name).ratio()

                    if first_similarity is not None and last_similarity is not None:
                        avg_similarity = (first_similarity * 0.3 + last_similarity * 0.7)

                    if correct_name is not None and error_name is not None:
                        full_similarity = SequenceMatcher(None, correct_name, error_name).ratio()

                    similarity = max(avg_similarity, full_similarity)

                    if similarity is not None and similarity > limit_similarity:
                        df_error_names.at[index, 'candidate'] = inner_row['bioname']
                        df_error_names.at[index, 'first_name'] = inner_row['first_name']
                        df_error_names.at[index, 'last_name'] = inner_row['last_name']
                        df_error_names.at[index, 'bioguide_id'] = inner_row['bioguide_id']
                        df_error_names.at[index, 'match'] = 1

        df_error_names = df_error_names.replace({np.nan: None})
        return df_error_names

    # Interprete names and set first and last name according to the names.
    def interpret_names(self, df):

        error_df = pd.DataFrame()

        for index, row in df.iterrows():
            name = row['candidate']
            if name is not None:
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

        return df

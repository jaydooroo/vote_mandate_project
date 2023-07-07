import sqlite3
import pandas as pd
from difflib import SequenceMatcher
import numpy as np
import math

class ultimate_converter:

    def __init__(self, conn):
        self.conn = conn

    def upload_df_to_database(self, df: pd.DataFrame, name: str):
        df.to_sql(name, self.conn, if_exists='replace')

    def merge_nokken_poole_with_votes(self):
        query = """
            DROP TABLE IF EXISTS combined_vote_result;

             CREATE TABLE combined_vote_result AS    
	        SELECT year,CAST(congress as INTEGER) as congress, state, state_po, bioguide_id, candidate,
	        CAST((CASE WHEN office = 'US SENATE' THEN 'Senate' WHEN office = 'US HOUSE' THEN 'House' END) as TEXT) as chamber,
	        district, special, stage, party, CAST((CAST(candidatevotes as REAL) / totalvotes)as REAL )as vote_share, 
	        CAST((CASE WHEN democratvotes IS NOT NULL THEN democratvotes/totalvotes END ) as REAL)as dems_vote_share_district, 
	        CAST((CASE WHEN republicanvotes IS NOT NULL THEN republicanvotes/totalvotes END) as REAL ) as gop_vote_share_district,
	        CAST((CASE WHEN dems_total_votes_state IS NOT NULL THEN dems_total_votes_state/total_votes_state END) as REAL) as dems_vote_share_state,
	        CAST((CASE WHEN gop_total_votes_state IS NOT NULL THEN gop_total_votes_state/total_votes_state END) as REAL) as gop_vote_share_state
	        FROM 
            (SELECT * 
            FROM name_modified_house
            UNION
		    SELECT * 
            FROM name_modified_senate);

            DROP TABLE IF EXISTS merged_nokken_pool;

            CREATE TABLE merged_nokken_pool AS
            SELECT nokken.congress, nokken.chamber, nokken.state_icpsr, CAST(nokken.district_code as INTEGER) as district, nokken.state_abbrev,
            nokken.bioname, nokken.bioguide_id, nokken.nokken_poole_dim1, abs(nokken.nokken_poole_dim1) as abs_nominate_dim1, 
            CAST(vote.special as INTEGER) as special, vote.stage, vote.party, vote.vote_share, vote.dems_vote_share_district, vote.gop_vote_share_district, 
            vote.dems_vote_share_state, vote.gop_vote_share_state
            FROM name_modified_HSall nokken
            LEFT JOIN combined_vote_result vote
            ON (nokken.bioguide_id = vote.bioguide_id OR nokken.bioname = vote.candidate) AND nokken.congress = vote.congress AND nokken.chamber = vote.chamber 
            AND nokken.state_abbrev = vote.state_po;

        """

        cursor = self.conn.cursor()

        cursor.executescript(query)

    def add_subterm_senate(self):
        query = """
        ALTER TABLE merged_nokken_pool ADD subterm INTEGER;

        UPDATE merged_nokken_pool
        SET subterm = 1
        WHERE vote_share IS NOT NULL AND chamber = 'Senate'; 


        """

        cursor = self.conn.cursor()
        cursor.executescript(query)

        query = """
            SELECT * 
            FROM merged_nokken_pool;

        """

        df = pd.read_sql_query(query, self.conn)
        df = df.replace({np.nan: None})

        dict_df = {}

        for index, row in df.iterrows():

            if row['chamber'] == 'Senate':
                congress = row['congress']
                subterm = row['subterm']
                state = row['state_abbrev']
                bioguide_id = row['bioguide_id']
                bioname = row['bioname']

                temp_key = str(congress) + str(state) + str(bioguide_id) + str(bioname)

                dict_df[temp_key] = index

                # previous congress key
                cf_key = str(congress - 1) + str(state) + str(bioguide_id) + str(bioname)

                # check if current subterm (current row)is not empty -> current row has all the vote share data
                # previous cf_key exist -> same person in the same state exist in the previous congress
                if subterm is None and cf_key in dict_df:
                    cf_index = dict_df[cf_key]
                    cf_subterm = df.loc[cf_index, 'subterm']

                    if cf_subterm is not None and cf_subterm < 3:
                        df.at[index, 'subterm'] = cf_subterm + 1
                        df.at[index, 'vote_share'] = df.loc[cf_index, 'vote_share']
                        df.at[index, 'party'] = df.loc[cf_index, 'party']
                        df.at[index, 'special'] = df.loc[cf_index, 'special']
                        df.at[index, 'stage'] = df.loc[cf_index, 'stage']
                        df.at[index, 'dems_vote_share_district'] = df.loc[cf_index, 'dems_vote_share_district']
                        df.at[index, 'gop_vote_share_district'] = df.loc[cf_index, 'gop_vote_share_district']
                        df.at[index, 'dems_vote_share_state'] = df.loc[cf_index, 'dems_vote_share_state']
                        df.at[index, 'gop_vote_share_state'] = df.loc[cf_index, 'gop_vote_share_state']

        self.upload_df_to_database(df, 'merged_nokken_pool')

    def add_recent_avg_senate_vote_share(self):

        #  adding most recent dems and gop voteshare as well as avg voteshare for both
        #  senate only.
        query = """

        BEGIN TRANSACTION;

        DROP TABLE IF EXISTS most_recent_senate_vote_share_state;

        CREATE TABLE most_recent_senate_vote_share_state AS
        SELECT congress, state_abbrev, chamber, 
        dems_vote_share_district as recent_dems_vote_share_senate, 
        gop_vote_share_district as recent_gop_vote_share_senate,
        AVG(dems_vote_share_district)  as dems_avg_vote_share, 
        AVG(gop_vote_share_district) as gop_avg_vote_share
        FROM merged_nokken_pool
        WHERE chamber = 'Senate'
        GROUP BY congress, state_abbrev
        HAVING min(subterm);

        DROP TABLE IF EXiSTS temp_merged_nokken_pool;

        CREATE TABLE temp_merged_nokken_pool AS 
        SELECT nokken.congress, nokken.chamber, nokken.state_icpsr, nokken.district, nokken.state_abbrev,
        nokken.bioname, nokken.bioguide_id, nokken.nokken_poole_dim1, nokken.abs_nominate_dim1,
        nokken.special, nokken.stage, nokken.party, nokken.vote_share, 
        nokken.dems_vote_share_district, nokken.gop_vote_share_district, 
        nokken.dems_vote_share_state, nokken.gop_vote_share_state,
        recent.recent_dems_vote_share_senate, recent.recent_gop_vote_share_senate, 
        recent.dems_avg_vote_share, recent.gop_avg_vote_share,
        nokken.subterm
        FROM merged_nokken_pool nokken
        LEFT JOIN most_recent_senate_vote_share_state recent 
        ON nokken.congress = recent.congress and nokken.state_abbrev = recent.state_abbrev and nokken.chamber = recent.chamber;   

        DROP TABLE merged_nokken_pool;

        ALTER TABLE temp_merged_nokken_pool RENAME TO merged_nokken_pool;

        COMMIT;
        """
        cursor = self.conn.cursor()
        cursor.executescript(query)
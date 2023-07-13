import sqlite3
import pandas as pd
from difflib import SequenceMatcher
import numpy as np
import math


#  converter class that is used after modifying house, senate and president db.
# it is used to merge and add more columns in the merged db.
class ultimate_converter:

    def __init__(self, conn):
        self.conn = conn

    # upload input df format of data to db as a Table
    # if same name exists in the db. Replace it.
    def upload_df_to_database(self, df: pd.DataFrame, name: str):
        df.to_sql(name, self.conn, if_exists='replace')

    # merge hsall db which has nokken pool data with house and senate data
    # join is used to merge. join through bioguide or canadidate name, state and congress.
    def merge_nokken_poole_with_h_s(self):
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
            FROM name_modified_senate
            );

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

    # add presidential election vote share for democratic and republican to merged dataset(merged_nokken_pool)
    def add_pres_vote_share(self):
        query = """
        
        ALTER TABLE merged_nokken_pool ADD COLUMN dems_pres_vote_share;
        ALTER TABLE merged_nokken_pool ADD COLUMN gop_pres_vote_share;

        
     UPDATE merged_nokken_pool
		SET dems_pres_vote_share = (
		
		SELECT dems_pres_vote_share
		FROM
		(
		SELECT congress,dems_votes_year/totalvotes as dems_pres_vote_share
		FROM name_modified_president
		)as subquery
		WHERE subquery.congress = merged_nokken_pool.congress or (subquery.congress + 1)= merged_nokken_pool.congress
		),
		gop_pres_vote_share = (
		
		SELECT gop_pres_vote_share
		FROM
		(
		SELECT congress,gop_votes_year/totalvotes as gop_pres_vote_share
		FROM name_modified_president
		)as subquery
		WHERE subquery.congress = merged_nokken_pool.congress or (subquery.congress + 1)= merged_nokken_pool.congress
		)
        """

        cursor = self.conn.cursor()
        cursor.executescript(query)


    # add subterm column into the merged_nokken_pool table.
    # subterm is only for senate.
    # senator seves for three congress since they have 6 years term.
    # it calculates if the senators are serving first,second or third congress term and assign it to subterm column.
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

    # add recent vote share for senate as well as avg vote share.
    # recent vote share means that the most recent voteshare for senator election in the same state.
    # It just use row that has lowest subterm varaible in the same state to calculate it.

    # avg senate vote share is the average vote share of the according year and state.
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
        AVG(dems_vote_share_district)  as dems_avg_vote_share_senate, 
        AVG(gop_vote_share_district) as gop_avg_vote_share_senate
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
        recent.dems_avg_vote_share_senate, recent.gop_avg_vote_share_senate,
        nokken.subterm
        FROM merged_nokken_pool nokken
        LEFT JOIN most_recent_senate_vote_share_state recent 
        ON nokken.congress = recent.congress and nokken.state_abbrev = recent.state_abbrev and nokken.chamber = recent.chamber;   

        DROP TABLE merged_nokken_pool;

        ALTER TABLE temp_merged_nokken_pool RENAME TO merged_nokken_pool;
        
        UPDATE merged_nokken_pool
        SET recent_dems_vote_share_senate = (
	    SELECT subquery.recent_dems_vote_share_senate
	    FROM (
	    SELECT congress, chamber, state_abbrev, bioname,recent_dems_vote_share_senate, subterm
	    FROM merged_nokken_pool
	    GROUP BY congress, state_abbrev
	    HAVING min(subterm)
	    ) as subquery
	    WHERE subquery.state_abbrev = merged_nokken_pool.state_abbrev and subquery.congress = merged_nokken_pool.congress
	
	    ),
	    recent_gop_vote_share_senate = (
	
		SELECT subquery.recent_gop_vote_share_senate
	    FROM (
	    SELECT congress, chamber, state_abbrev, bioname,recent_gop_vote_share_senate, subterm
	    FROM merged_nokken_pool
	    GROUP BY congress, state_abbrev
	    HAVING min(subterm)
	    ) as subquery
	    WHERE subquery.state_abbrev = merged_nokken_pool.state_abbrev and subquery.congress = merged_nokken_pool.congress
	    );
	    
	    

ALTER TABLE merged_nokken_pool ADD COLUMN recent_dems_vote_share_house REAL;

ALTER TABLE merged_nokken_pool ADD COLUMN recent_gop_vote_share_house REAL; 

UPDATE merged_nokken_pool
SET recent_dems_vote_share_house = (
	SELECT subquery.dems_vote_share_state
	FROM (
	SELECT dems_vote_share_state, state_abbrev, congress, chamber
	FROM merged_nokken_pool
	WHERE chamber = 'House' and dems_vote_share_state IS NOT NULL
	GROUP BY state_abbrev, congress,chamber
	
	)AS subquery
	WHERE subquery.state_abbrev = merged_nokken_pool.state_abbrev and subquery.congress = merged_nokken_pool.congress
),

recent_gop_vote_share_house = (
	SELECT subquery.gop_vote_share_state
	FROM (
	SELECT gop_vote_share_state, state_abbrev, congress, chamber
	FROM merged_nokken_pool
	WHERE chamber = 'House' and gop_vote_share_state IS NOT NULL
	GROUP BY state_abbrev, congress,chamber 
	
	)AS subquery
	WHERE subquery.state_abbrev = merged_nokken_pool.state_abbrev and subquery.congress = merged_nokken_pool.congress

);
        
        
        COMMIT;
        """
        cursor = self.conn.cursor()
        cursor.executescript(query)
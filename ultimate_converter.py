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
    # Join with only house and senate data.
    def merge_nokken_poole_with_h_s(self):
        query = """
            DROP TABLE IF EXISTS combined_vote_result;

            CREATE TABLE combined_vote_result AS    
	        SELECT year,CAST(congress as INTEGER) as congress, state, state_po, bioguide_id, candidate,
	        CAST((CASE WHEN office = 'US SENATE' THEN 'Senate' WHEN office = 'US HOUSE' THEN 'House' END) as TEXT) as chamber,
	        district, special, stage, party, CAST((CAST(candidatevotes as REAL) / totalvotes)as REAL )as vote_share, 
	        CAST((CASE WHEN democratvotes IS NOT NULL THEN CAST(democratvotes AS REAL)/totalvotes END ) as REAL)as dems_vote_share_district, 
	        CAST((CASE WHEN republicanvotes IS NOT NULL THEN CAST(republicanvotes AS REAL)/totalvotes END) as REAL ) as gop_vote_share_district,
	        CAST((CASE WHEN dems_total_votes_state IS NOT NULL THEN CAST (dems_total_votes_state AS REAL)/total_votes_state END) as REAL) as dems_vote_share_state,
	        CAST((CASE WHEN gop_total_votes_state IS NOT NULL THEN CAST (gop_total_votes_state AS REAL)/total_votes_state END) as REAL) as gop_vote_share_state
	        FROM 
            (SELECT * 
            FROM name_modified_house
            UNION
		    SELECT * 
            FROM name_modified_senate
            );
            
            DROP TABLE IF EXISTS merged_nokken_pool;

            CREATE TABLE merged_nokken_pool AS
            SELECT nokken.congress, vote.year,nokken.chamber, nokken.state_icpsr, CAST(nokken.district_code as INTEGER) as district, nokken.state_abbrev,
            nokken.bioname, nokken.bioguide_id, nokken.nokken_poole_dim1, 
			CASE WHEN nokken.party_code = 100 THEN (-1 * nokken.nokken_poole_dim1)  
			WHEN nokken.party_code = 200 THEN nokken.nokken_poole_dim1 ELSE NULL END as modified_nokken_poole_dim1, 
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
    # the congress year and the next congress year(total 2 congress) belong to one presidential election(Because president term is 4 years)
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
                        df.at[index, 'year'] = df.loc[cf_index, 'year'] + 2
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
    # recent vote share means that the most recent vote share for senator election in the same state.
    # It just uses row that has lowest subterm variable in the same state to calculate it.

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
        SELECT nokken.congress,CAST(nokken.year AS INTEGER) as year, nokken.chamber, nokken.state_icpsr, nokken.district, nokken.state_abbrev,
        nokken.bioname, nokken.bioguide_id, nokken.nokken_poole_dim1, nokken.modified_nokken_poole_dim1,
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
	    ),
	    dems_avg_vote_share_senate = (
	    SELECT dems_avg_vote_share_senate
	    FROM (
	    SELECT congress, chamber, state_abbrev, bioname, dems_avg_vote_share_senate
	    FROM merged_nokken_pool
	    WHERE chamber = 'Senate' 
	    GROUP BY congress, state_abbrev
	    )AS subquery
	    WHERE subquery.congress = merged_nokken_pool.congress AND subquery.state_abbrev = merged_nokken_pool.state_abbrev
        ),

        gop_avg_vote_share_senate = (
	    SELECT gop_avg_vote_share_senate
	    FROM (
	    SELECT congress, chamber, state_abbrev, bioname, gop_avg_vote_share_senate
	    FROM merged_nokken_pool
	    WHERE chamber = 'Senate' 
	    GROUP BY congress, state_abbrev
	    )AS subquery
	    WHERE subquery.congress = merged_nokken_pool.congress AND subquery.state_abbrev = merged_nokken_pool.state_abbrev
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

    # adding fellow senate vote share
    # a variable that equals the party vote share in the other senate race from the same state.
    def add_fellow_senate_vote_share(self):

        query = """
        
        ALTER TABLE merged_nokken_pool ADD COLUMN fellow_senate_vote_share;
        
        UPDATE merged_nokken_pool
        SET fellow_senate_vote_share = (
	    SELECT CASE WHEN merged_nokken_pool.party = 'DEMOCRAT' THEN subquery.dems_vote_share_district 
	    WHEN merged_nokken_pool.party = 'REPUBLICAN' THEN subquery.gop_vote_share_district
	    ELSE NULL END
	    FROM(
	    SELECT congress, state_icpsr, bioname, dems_vote_share_district, gop_vote_share_district
	    FROM merged_nokken_pool
	    WHERE chamber = 'Senate' AND party is not null
		GROUP BY congress, state_icpsr, bioname
	    )AS subquery
	    WHERE subquery.congress = merged_nokken_pool.congress AND subquery.state_icpsr = merged_nokken_pool.state_icpsr AND subquery.bioname != merged_nokken_pool.bioname 
	    AND merged_nokken_pool.chamber = 'Senate'
	    )
        """

        cursor = self.conn.cursor()
        cursor.executescript(query)
    # Add senate and house indication variable.
    def add_senate_house_indication_variable(self):
        query = """
        
        ALTER TABLE merged_nokken_pool ADD COLUMN senate;
        ALTER TABLE merged_nokken_pool ADD COLUMN house;

        UPDATE merged_nokken_pool 
        SET senate = CASE WHEN chamber = 'Senate' THEN 1 ELSE 0 END,
        house = CASE WHEN chamber = 'House' THEN 1 ELSE 0 END
        """

        cursor = self.conn.cursor()
        cursor.executescript(query)

    def add_experience(self):

        query = """
            ALTER TABLE merged_nokken_pool ADD COLUMN exp INTEGER;
            ALTER TABLE merged_nokken_pool ADD COLUMN total_exp INTEGER; 
        """

        cursor = self.conn.cursor()
        cursor.executescript(query)

        query = """
                    SELECT * 
                    FROM merged_nokken_pool
                """

        df = pd.read_sql_query(query, self.conn)
        df = df.replace({np.nan: None})

        exp_dict = {}

        for index, row in df.iterrows():
            state = row['state_abbrev']
            bioguide_id = row['bioguide_id']
            bioname = row['bioname']
            chamber = row['chamber']

            exp_key = str(state) + str(bioguide_id) + str(bioname) + str(chamber)

            if exp_key in exp_dict:
                exp = exp_dict[exp_key]
                exp_dict[exp_key] = exp + 2

            else:
                exp_dict[exp_key] = 2

            df.at[index, 'exp'] = exp_dict[exp_key]

        for index, row in df.iterrows():
            state = row['state_abbrev']
            bioguide_id = row['bioguide_id']
            bioname = row['bioname']
            chamber = row['chamber']

            exp_key = str(state) + str(bioguide_id) + str(bioname) + str(chamber)

            if exp_key in exp_dict:
                df.at[index, 'total_exp'] = exp_dict[exp_key]

        self.upload_df_to_database(df, 'merged_nokken_pool')



        #
        # term_dict = {}
        # total_term_dict = {}
        # # dictionary that counts the number of consecutive terms that politicians serve.
        # # Do not know how to save the terms this way. First we need to count each consecutive terms and save it into a variable in the
        # # dataframe.
        # #  and then we need to deal with it. The main part is to know when the term starts and end.
        # # this is very tricky part to know.
        # #  I feel like we need to save the beginning row of the consecutive terms.
        # #  and then we need to save the maximum consecutive terms into the dictionary -> key should innclude the information of the
        # # beginning of the consecutive terms.
        # # if the origin variable has the beginning information then -> keeps counting the terms otherwise makes a new key value that
        # # starts from the current rows(current row should be the beginning of the terms.)
        # c_count_dict = {}
        # subterm_dict = {}



        # for index, row in df.iterrows():
        #
        #     congress = row['congress']
        #     subterm = row['subterm']
        #     state = row['state_abbrev']
        #     bioguide_id = row['bioguide_id']
        #     bioname = row['bioname']
        #     chamber = row['chamber']
        #
        #     temp_key = str(congress) + str(state) + str(bioguide_id) + str(bioname) + str(chamber)
        #     term_dict[temp_key] = index
        #
        #     #  there is problem in this algorithm
        #     #  it can be applied to house but not senate since the senate serves for three congress year.
        #     #  how can I deal with this problem?
        #     # This only apply for house let's just make it that way.
        #     #  I can't wait to buy galaxy s23. It seems so nice and small and light smartphone I have ever wanted
        #
        #     total_term_key = str(state) + str(bioguide_id) + str(bioname) + str(chamber)
        #
        #     if total_term_key not in total_term_dict:
        #         total_term_dict[total_term_key] = 1
        #     else:
        #         count = total_term_dict[total_term_key]
        #         total_term_dict[total_term_key] = count + 1
        #
        #     cf_key = str(congress - 1) + str(state) + str(bioguide_id) + str(bioname) + str(chamber)
        #
        #     if cf_key in term_dict:
        #
        #         cf_index = term_dict[cf_key]
        #         # cf_c_term = df.loc[cf_index, 'c_term']
        #         origin_c_num = df.loc[cf_index, 'origin_c_num']
        #
        #         # if cf_c_term is not None:
        #         #     df.at[index, 'c_term'] = cf_c_term + 1
        #         if origin_c_num is not None:
        #             df.at[index, 'origin_c_num'] = origin_c_num
        #     else:
        #         # df.at[index, 'c_term'] = 1
        #         df.at[index, 'origin_c_num'] = congress
        #
        #     c_count_key = str(df.loc[index, 'origin_c_num']) + str(bioname) + str(bioguide_id) + str(state) + str(
        #         chamber)
        #
        #     if c_count_key in c_count_dict:
        #         c_count = c_count_dict[c_count_key]
        #         c_count_dict[c_count_key] = c_count + 1
        #     else:
        #         c_count_dict[c_count_key] = 1
        #
        #     if subterm is not None:
        #         subterm_key = str(df.loc[index, 'origin_c_num']) + str(bioname) + str(bioguide_id) + str(state) + str(
        #             chamber)
        #         subterm_dict[subterm_key] = subterm
        #
        # # need to set proper term here by caluculating the count for senators and subterm.
        # #  also need to set the count variable here.
        # # How can we do this?
        # #  we have count right now and do not know when does the first term end.
        # #  we need to calculate using subterm, if the subterm ends with 3 then the calculation is easy.
        # #  the first term should be count % 3 term if 12  and subterm ends with 3 then first term is full 3 confress year.
        # # if the term is 11 then 11 %3 sould be 2 then first term is only 2 congress year.
        # # how about the subterm ends with 2 or 1 then we need to substract the last subterm from count
        # #  for example -> 12 - 2(subterm) and modulo by 3 -> 10 % 3 = 1
        # #  so in the first iteration we need to also store subterm variable if exist.
        # # what if there is no subterm exist in the dataset. =>let's ignore it since we only need the dataaset that has voteshare.
        # #
        # dict_df = {}
        # s_total_terms_dict = {}
        # s_count_dict = {}
        #
        # remained_term_dict = {}
        #
        # for index, row in df.iterrows():
        #
        #     congress = row['congress']
        #     subterm = row['subterm']
        #     state = row['state_abbrev']
        #     bioguide_id = row['bioguide_id']
        #     bioname = row['bioname']
        #     chamber = row['chamber']
        #     # How to make it works well.
        #     #  So should it loop through from the first?
        #     #  or is there any other way to do it?
        #     #  Loop through from the first and check if this has the same origin with the one in the dictionary(count and total_term)
        #     #  there is nothing to do with the house chamber but there are things to do with the senate chamber.
        #     #  So for the house just simply set the total term and count
        #     #  for the senate, it should be different.
        #     #  need to check if the row is the origin row or not if there is subterm information then it should be different.
        #     # need to do calculation and see if the current row is how far from the orrigin congress. if the current congress is far away enough to
        #     #  move on to next term then it should be changed accordingly.
        #     #  if subterm does not exist in the dataset. then just randomly assign it since we do not need the data
        #     #
        #     temp_key = str(congress) + str(state) + str(bioguide_id) + str(bioname) + str(chamber)
        #     dict_df[temp_key] = index
        #
        #     if chamber == 'House':
        #         cf_key = str(congress - 1) + str(state) + str(bioguide_id) + str(bioname) + str(chamber)
        #
        #         if cf_key in dict_df:
        #             cf_index = dict_df[cf_key]
        #             cf_term = df.loc[cf_index, 'term']
        #             if cf_term is not None:
        #                 df.at[index, 'term'] = cf_term + 1
        #         else:
        #             df.at[index, 'term'] = 1
        #
        #         total_term_key = str(state) + str(bioguide_id) + str(bioname) + str(chamber)
        #         if total_term_key in total_term_dict:
        #             df.at[index, 'total_terms'] = total_term_dict[total_term_key]
        #
        #         c_count_key = str(df.loc[index, 'origin_c_num']) + str(bioname) + str(bioguide_id) + str(state) + str(
        #             chamber)
        #         if c_count_key in c_count_dict:
        #             c_count = c_count_dict[c_count_key]
        #             df.at[index, 'consequent_terms'] = c_count
        #
        #     #  How should I deal with senate
        #     #  So if the subterm exist in the subterm_dict then
        #     #  we need to calculate it. and the also consequent _terms should be calculated
        #     #  what are the ways to do it?
        #     #  so both total_term and consequent terms should be calculated using the c_count -> it means congress count
        #     #  Not the term
        #     #  what are the ways to do it then?
        #     #  total _term should be calculated using congress term for current one and the total term that we have
        #     #  total_term newly set the dictionary I guess and calculate the term accordingly?
        #     #  or what? if the current term does not have the subterm it is quite meaningless. However,
        #     #  there is possibility that the candidate later elected again and the consecutive terms have the subterm.
        #     #  In this case, we need to have accurate term variable as well.
        #     #  What if current consequent term has only 3 terms -> it can be up to 2 even two terms can be upto 2 term for senator.
        #     #  How am I supposed to do it?
        #     #  Three terms -> 3 terms-> how should we decide it-> How should we deal with previous one
        #     #  temporary just consider previous one as one if it 3 within 3 terms.
        #     #  so the total term  should be calculated first or later?
        #     #  how am I supposed to do this?
        #     #  First of all, it is really hard to get total term.
        #     #  first we need to caculate the consecutive term and then we need to add up the totalterm
        #     #  I guess we need new dictionary and re loop through again the senate.
        #     #  or we can use dataframe method where it find specific rows and set the values accordingly.
        #     # total_term senate should be accumulated through this loop ->
        #     #  How am I supposed to do with it?
        #
        #     elif chamber == 'Senate':
        #         s_total_term_key = str(state) + str(bioguide_id) + str(bioname) + str(chamber)
        #         s_count_key = str(df.loc[index, 'origin_c_num']) + str(bioname) + str(bioguide_id) + str(state) + str(
        #             chamber)
        #
        #         total_term_key = str(state) + str(bioguide_id) + str(bioname) + str(chamber)
        #         if total_term_key in total_term_dict:
        #             total_c_term = total_term_dict[total_term_key]
        #
        #         c_count_key = str(df.loc[index, 'origin_c_num']) + str(bioname) + str(bioguide_id) + str(state) + str(
        #             chamber)
        #         if c_count_key in c_count_dict:
        #             c_count = c_count_dict[c_count_key]
        #
        #         subterm_key = str(df.loc[index, 'origin_c_num']) + str(bioname) + str(bioguide_id) + str(state) + str(
        #             chamber)
        #         if subterm_key in subterm_dict:
        #             ult_subterm = subterm_dict[subterm_key]
        #
        #         #  term_cal is the number of congress year of the first term.
        #         #  do we have to make another dictionary?
        #         #  what are the ways to solve this problem?
        #         #  term_cal = c_count - ult_subterm
        #         #  term_cal should be contained in a dictionary.
        #         #  1,1,2,2,2,3,3,3,4,4,4,5,5,6
        #         #  set this in the dictionary -> term is 1 and not none substract 1 every time.
        #
        #         remained_term_key = str(df.loc[index, 'origin_c_num']) + str(bioname) + str(bioguide_id) + str(
        #             state) + str(chamber)
        #         # c_count 랑 total term 다시 저장하고 다시 for loop 굴려야함.,
        #
        #         if c_count is not None and ult_subterm is not None and (remained_term_key not in remained_term_dict):
        #             term_cal = (c_count - ult_subterm) % 3
        #             remained_term_dict[remained_term_key] = term_cal
        #         elif remained_term_key not in remained_term_dict:
        #             remained_term_dict[remained_term_key] = -1
        #
        #         # if term_cal should be applied only beginning of the rows.
        #         term_cal = remained_term_dict[remained_term_key]
        #
        #         if term_cal > 0:
        #             df.at[index, 'term'] = 1
        #             remained_term_dict[remained_term_key] = term_cal - 1
        #         elif subterm is not None and subterm > 1:
        #             cf_key = str(congress - 1) + str(state) + str(bioguide_id) + str(bioname) + str(chamber)
        #             if cf_key in dict_df:
        #                 cf_index = dict_df[cf_key]
        #                 cf_term = df.loc[cf_index, 'term']
        #
        #                 if cf_term is not None:
        #                     df.at[index, 'term'] = cf_term
        #
        #         elif subterm is not None and subterm == 1:
        #             cf_key = str(congress - 1) + str(state) + str(bioguide_id) + str(bioname) + str(chamber)
        #             if cf_key in dict_df:
        #                 cf_index = dict_df[cf_key]
        #                 cf_term = df.loc[cf_index, 'term']
        #
        #                 if cf_term is not None:
        #                     df.at[index, 'term'] = cf_term + 1
        #             else:
        #                 df.at[index, 'term'] = 1
        #         else:
        #             cf_key_1 = str(congress - 1) + str(state) + str(bioguide_id) + str(bioname) + str(chamber)
        #             cf_key_3 = str(congress - 3) + str(state) + str(bioguide_id) + str(bioname) + str(chamber)
        #
        #             if cf_key_1 not in dict_df:
        #                 df.at[index, 'term'] = 1
        #             else:
        #                 cf_index_1 = dict_df[cf_key_1]
        #                 cf_term_1 = df.loc[cf_index_1, 'term']
        #                 # 어떻게 해야할까?
        #                 # cf_term == 1 ->  the previous congress term is 1 and term_cal is 0
        #                 #  should be moved on to the next term.
        #                 # if the term is not 1 and term_cal is 0 what should it do.
        #                 # what if term_cal is 0 but originally 0 -> there is no case for this since they
        #                 #  are assigned to be -1 in that case
        #                 # we might be able to track the congress -3 instead in this case and see if
        #                 # it has the same congress or not.
        #                 #  if 1,222 -> in this case does it work? algorithm shold check previous one and also check -3 one
        #                 # if -3 doesn't exist and previous one is 2 then just be 2
        #                 #  if -3 is 1 then just make it 2.
        #                 # if cf_key does not exist -> cf_key does not have to be
        #                 if cf_term_1 == 1 and term_cal == 0:
        #                     df.at[index, 'term'] = 2
        #                 # if cf_key 3 does not exist and cf_term_1 is 2 then set the df with term 2
        #                 elif cf_key_3 not in dict_df:
        #                     if cf_term_1 == 2:
        #                         df.at[index,'term'] = 2
        #                 # if cf_key 3 in dict_df just set i
        #                 else:
        #                     if cf_key_3 in dict_df:
        #                         cf_index_3 = dict_df[cf_key_3]
        #                         cf_term = df.loc[cf_index_3, 'term']
        #
        #                         if cf_term is not None:
        #                             df.at[index, 'term'] = cf_term + 1
        #
        #                     else:
        #                         df.at[index, 'term'] = 1


        # self.upload_df_to_database(df, 'merged_nokken_pool')

        #
        # dict_df = {}
        #
        # for index, row in df.iterrows():
        #
        #     congress = row['congress']
        #     subterm = row['subterm']
        #     state = row['state_abbrev']
        #     bioguide_id = row['bioguide_id']
        #     bioname = row['bioname']
        #     chamber = row['chamber']
        #
        #     temp_key = str(congress) + str(state) + str(bioguide_id) + str(bioname) + str(chamber)
        #
        #     dict_df[temp_key] = index
        #
        #     if chamber == 'House':
        #         cf_key = str(congress - 1) + str(state) + str(bioguide_id) + str(bioname) + str(chamber)
        #
        #         if cf_key in dict_df:
        #             cf_index = dict_df[cf_key]
        #             cf_term = df.loc[cf_index, 'term']
        #             if cf_term is not None:
        #                 df.at[index, 'term'] = cf_term + 1
        #         else:
        #             df.at[index, 'term'] = 1
        #
        #     elif chamber == 'Senate':
        #         if subterm is not None and subterm > 1:
        #             cf_key = str(congress - 1) + str(state) + str(bioguide_id) + str(bioname) + str(chamber)
        #             if cf_key in dict_df:
        #                 cf_index = dict_df[cf_key]
        #                 cf_term = df.loc[cf_index, 'term']
        #
        #                 if cf_term is not None:
        #                     df.at[index, 'term'] = cf_term
        #             else:
        #                 df.at[index, 'term'] = 1
        #
        #         elif subterm is not None and subterm == 1:
        #             cf_key = str(congress - 1) + str(state) + str(bioguide_id) + str(bioname) + str(chamber)
        #             if cf_key in dict_df:
        #                 cf_index = dict_df[cf_key]
        #                 cf_term = df.loc[cf_index, 'term']
        #
        #                 if cf_term is not None:
        #                     df.at[index, 'term'] = cf_term + 1
        #             else:
        #                 df.at[index, 'term'] = 1
        #         else:
        #             cf_key = str(congress - 3) + str(state) + str(bioguide_id) + str(bioname) + str(chamber)
        #             if cf_key in dict_df:
        #                 cf_index = dict_df[cf_key]
        #                 cf_term = df.loc[cf_index, 'term']
        #
        #                 if cf_term is not None:
        #                     df.at[index, 'term'] = cf_term + 1
        #
        #             else:
        #                 df.at[index, 'term'] = 1
        #
        # self.upload_df_to_database(df, 'merged_nokken_pool')

    # Drop all the rows that does not have vote share and save it to the new table "merged_nokken_poole_1976_2020"
    # Add DR (vote share among the subtotal only of votes casts for republican and democrat party vote)
    def create_result_table(self):

        query = """
        DROP TABLE IF EXiSTS merged_nokken_poole_1976_2020;
        
        CREATE TABLE merged_nokken_poole_1976_2020 AS
        SELECT congress,CAST(year as INTEGER) as year, chamber, district, state_abbrev, bioname, bioguide_id, nokken_poole_dim1,modified_nokken_poole_dim1,
        special, stage, party, vote_share as vs, dems_vote_share_district as dems_vs_district, gop_vote_share_district as gop_vs_district,
		dems_vote_share_district/(dems_vote_share_district + gop_vote_share_district) as DR_dems_vs_district,
		gop_vote_share_district / (dems_vote_share_district + gop_vote_share_district) as DR_gop_vs_district,
		dems_vote_share_state as dems_vs_state, gop_vote_share_state as gop_vs_state,
		dems_vote_share_state / (dems_vote_share_state + gop_vote_share_state) as DR_dems_vs_state,
		gop_vote_share_state / (dems_vote_share_state + gop_vote_share_state) as DR_gop_vs_state, 
        recent_dems_vote_share_senate as recent_dems_vs_senate, recent_gop_vote_share_senate as recent_gop_vs_senate, 
		recent_dems_vote_share_senate / (recent_dems_vote_share_senate + recent_gop_vote_share_senate) as DR_recent_dems_vs_senate,
		recent_gop_vote_share_senate / (recent_dems_vote_share_senate + recent_gop_vote_share_senate) as DR_recent_gop_vs_senate,
		recent_dems_vote_share_house as recent_dems_vs_house, recent_gop_vote_share_house as recent_gop_vs_house,
		recent_dems_vote_share_house / (recent_dems_vote_share_house + recent_gop_vote_share_house) as DR_recent_dems_vs_house,
		recent_gop_vote_share_house / (recent_dems_vote_share_house + recent_gop_vote_share_house) as DR_recent_gop_vs_house, 
        dems_avg_vote_share_senate as dems_avg_vs_senate, gop_avg_vote_share_senate as gop_avg_vs_senate, 
		dems_avg_vote_share_senate / (dems_avg_vote_share_senate + gop_avg_vote_share_senate) as DR_dems_avg_vs_senate,
		gop_avg_vote_share_senate / (dems_avg_vote_share_senate + gop_avg_vote_share_senate) as DR_gop_avg_vs_senate,
		dems_pres_vote_share as dems_pres_vs, gop_pres_vote_share as gop_pres_vs, 
		dems_pres_vote_share / (dems_pres_vote_share + gop_pres_vote_share) as DR_dems_pres_vs,
		gop_pres_vote_share / (dems_pres_vote_share + gop_pres_vote_share) as DR_gop_pres_vs,
		fellow_senate_vote_share as fellow_senate_vs, senate, house ,subterm , exp, total_exp
        FROM merged_nokken_pool
        WHERE vote_share IS NOT NULL and (congress >= 95 and congress <= 117 )
        """

        cursor = self.conn.cursor()
        cursor.executescript(query)

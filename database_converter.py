import sqlite3
import pandas as pd
from difflib import SequenceMatcher
import numpy as np
import math


# convert available dataset into modified dataset.
# focused on naming modification
# later make this naming converter and speprate voting calculation into other class
# later we should make merge class, adding_columns(voting share) class

# to completely match politicians names, we need to require users to manually assign the name after they check the name differences.
# in this class, match the name as much as possible -> need to be clear about the total result after running this class(such as name of db that this class have created)
# so that we can make manual assgining names user interface using that database.
class database_converter:

    def __init__(self, conn):
        self.conn = conn

    def upload_df_to_database(self, df: pd.DataFrame, name: str):
        df.to_sql(name, self.conn, if_exists='replace')

    def convert_database(self, office_type):
        if office_type.upper() == 'H':
            original_table = 'from1976to2020_house'
            party_column = 'party'
            modified_table = 'name_modified_house'

        elif office_type.upper() == 'S':
            original_table = 'from1976to2020_senate'
            party_column = 'party_simplified'
            modified_table = 'name_modified_senate'
        else:
            # need to be modified later when I get the proper president database.
            original_table = 'president'

        # Generating democrat, republican, total votes of every election.
        # I put special here - > shoul be modified later I think. special data set-> the out put query below also have special election data sperated from the normal one.
        #  Therefore, the query coming after blow query should be implemented using which election between special and normal
        # applied -> need to decide first which one we should apply.
        senate_query = """
        SELECT year, state, state_po, office, district,special, stage, candidate, {}, candidatevotes, CAST(MAX(totalvotes) AS INTEGER) AS totalvotes,
        CAST(MAX(democratvotes) AS INTEGER) AS democratvotes, CAST(MAX(republicanvotes) AS INTEGER) AS republicanvotes
		FROM (
			    SELECT *, CAST((CASE WHEN {} = 'DEMOCRAT' THEN candidatevotes END) AS INTEGER) AS democratvotes,
				CAST((CASE WHEN {} = 'REPUBLICAN' THEN candidatevotes END) AS INTEGER) AS republicanvotes
			    FROM 
                (
                    SELECT year, state, state_po, office, district,special,stage, candidate, {}, SUM(candidatevotes) as candidatevotes, totalvotes
                    FROM {}
                    GROUP BY year, state_po, district,special,candidate
                    HAVING MAX(candidatevotes))) AS subquery
        GROUP BY year, state_po, district, special
        HAVING MAX(candidatevotes);
        """.format(party_column, party_column, party_column, party_column, original_table)

        df_senate = pd.read_sql_query(senate_query, self.conn)

        self.interprete_names(df_senate)

        print(df_senate.columns)

        self.upload_df_to_database(df_senate, modified_table)

        # Generating democrats, Republican total votes of the state and year of the election

        query = """
                ALTER TABLE {} ADD COLUMN dems_total_votes_state INTEGER;
                
                ALTER TABLE {} ADD COLUMN gop_total_votes_state INTEGER;
                
                ALTER TABLE {} ADD COLUMN total_votes_state INTEGER;

                UPDATE {}
                SET dems_total_votes_state = (
                SELECT subquery.dems_total_votes_state
                FROM (
                SELECT SUM(democratvotes)AS dems_total_votes_state, SUM(republicanvotes) as gop_total_votes_state, SUM(totalvotes) as total_votes_state, state_po, year
                FROM {}
                GROUP BY state_po, year
                )AS subquery
                WHERE subquery.state_po = {}.state_po AND subquery.year = {}.year
                ), gop_total_votes_state = (
                SELECT subquery.gop_total_votes_state
                FROM (
                SELECT SUM(democratvotes)AS dems_total_votes_state, SUM(republicanvotes) as gop_total_votes+_state, SUM(totalvotes) as total_votes_state,state_po, year
                FROM {}
                GROUP BY state_po, year
                )AS subquery
                WHERE subquery.state_po = {}.state_po AND subquery.year = {}.year
                ),total_votes_state = (
                SELECT subquery.total_votes_state
                FROM (
                SELECT SUM(democratvotes)AS dems_total_votes_state, SUM(republicanvotes) as gop_total_votes_state, SUM(totalvotes) as total_votes_state,state_po, year
                FROM {}
                GROUP BY state_po, year
                )AS subquery
                WHERE subquery.state_po = {}.state_po AND subquery.year = {}.year
                );
        """.format(modified_table, modified_table, modified_table, modified_table, modified_table, modified_table,
                   modified_table,
                   modified_table, modified_table, modified_table, modified_table, modified_table, modified_table)

        cursor = self.conn.cursor()

        cursor.executescript(query)
        return df_senate

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

    def interprete_names(self, df):

        for index, row in df.iterrows():
            name = row['candidate']
            name_arr = name.split()
            length = len(name_arr)

            # convert name_arr into normal form names like Jehyeon Lee or James M. Lee
            # by saving and deleting nickname or suffix
            new_name_arr = []
            for i in range(length):
                if '"' in name_arr[i]:
                    new_name = name_arr[i].replace('"', "")
                    # df.at[index, 'nickname'] = str(new_name).upper()
                    nickname = str(new_name).upper()

                elif '(' in name_arr[i] or ')' in name_arr[i]:
                    new_name = name_arr[i].replace('(', "")
                    new_name = new_name.replace(')', "")
                    nickname = str(new_name).upper()
                    # df.at[index, 'nickname'] = str(new_name).upper()

                elif "JR." == str(name_arr[i]).upper() or "SR." == str(name_arr[i]).upper() or "III" == str(
                        name_arr[i]).upper() \
                        or "II" == str(name_arr[i]).upper() or "JR" == str(name_arr[i]).upper() or "SR" == str(
                    name_arr[i]).upper():
                    pass
                    # df.at[index, 'suffix'] = str(name_arr[i]).replace('.', "").upper()
                else:
                    # last name with suffix usually comes with ','.
                    # following code is for removing ',' sign and putting the name into new_name_arr
                    # new_name_arr is for using it later to interpret first and last name.
                    # new_name_arr does not include suffix and nickname.
                    if ',' in name_arr[i]:
                        name_element = name_arr[i].replace(',', "")
                    else:
                        name_element = name_arr[i]
                    new_name_arr.append(name_element)

            # divide it with first name and last name only. excluding middle name since it is very difficult to discern it.
            # if the nickname equal == first name. what should I do?

            if len(new_name_arr) == 1:
                df.at[index, 'last_name'] = str(new_name_arr[0]).upper()
                # if df.loc[index, 'nickname'] is not None:
                if nickname is not None:
                    # df.at[index, 'first_name'] = str(df.loc[index, 'nickname']).upper()
                    df.at[index, 'first_name'] = nickname
            else:
                df.at[index, 'last_name'] = str(new_name_arr[-1]).upper()
                df.at[index, 'first_name'] = str(new_name_arr[0]).upper()

        return df

    # retrieve erroneous names (such as similar names) and return dataframe that has all the rows that has erroneous names.
    # we can modify the level of similarity using limit_similarity argument. (1 is equal 0 is different completely)
    def check_names(self, df, limit_similarity):
        # dictionary: key is year + state_po + party string, value is index
        dict_df = {}

        problematic_rows = set([])

        for index, row in df.iterrows():

            # initializing key and values
            # original name that is going to be compared.

            if row['office'] == 'US SENATE':
                year_term = 6
                party_column = 'party_simplified'
                mark = 's'
            elif row['office'] == 'US HOUSE':
                year_term = 2
                party_column = 'party'
                mark = 'h'
            else:
                year_term = 4
                mark = 'p'

            temp_key = str(row['year']) + row['state_po'] + row[party_column] if row[
                                                                                     party_column] is not None else "none" + mark
            dict_df[temp_key] = index

            compare_key1 = str(row['year'] - year_term) + row['state_po'] + row[party_column] if row[
                                                                                                     party_column] is not None else "none" + mark
            compare_key2 = str(row['year'] - year_term * 2) + row['state_po'] + row[party_column] if row[
                                                                                                         party_column] is not None else "none" + mark
            if compare_key1 in dict_df:
                # name that we are going to compare
                compare_name1 = df.loc[dict_df[compare_key1], 'candidate']
                s1 = SequenceMatcher(None, row['candidate'], compare_name1).ratio()
                if limit_similarity <= s1 < 1:
                    # current index
                    problematic_rows.add(index)
                    # no.1 index
                    problematic_rows.add(dict_df[compare_key1])
            # consider using set that prevent adding duplicate values.

            if compare_key2 in dict_df:
                compare_name2 = df.loc[dict_df[compare_key2], 'candidate']
                current_name = row['candidate']
                s2 = SequenceMatcher(None, current_name, compare_name2).ratio()
                if limit_similarity <= s2 < 1:
                    # add current index
                    problematic_rows.add(index)
                    # add no.2 index( which is current - 12 years index)
                    problematic_rows.add(dict_df[compare_key2])

        result_df = pd.DataFrame(columns=df.columns)

        problematic_rows = sorted(problematic_rows)

        # loop through every index in problematic_rows and find the row and assign it into dataframe.
        if len(problematic_rows) > 0:
            for value in problematic_rows:
                row = df.iloc[value]
                result_df = result_df.append(row)
                # result_df = pd.concat([result_df, pd.DataFrame(row)])
                # result_df = result_df.concat(row)

        return result_df

    #  code that search people who changed parties (similar code with searching similar names)
    # running this function after correcting the names that are similar is recommended.
    def check_party_changes(self, df: pd.DataFrame):
        dict_df = {}

        problematic_rows = set([])

        for index, row in df.iterrows():
            if row['office'] == 'US SENATE':
                year_term = 6
                party_column = 'party_simplified'
                mark = 's'
            elif row['office'] == 'US HOUSE':
                year_term = 2
                party_column = 'party'
                mark = 'h'
            else:
                year_term = 4
                mark = 'p'

            temp_key = str(row['year']) + str(row['state_po']) + str(row['candidate']) + mark
            dict_df[temp_key] = index

            for i in range(1, 4):
                compare_key = str(row['year'] - year_term * i) + str(row['state_po']) + str(row['candidate']) + mark
                if compare_key in dict_df:
                    compare_party = df.loc[dict_df[compare_key], party_column]

                    if compare_party != row[party_column]:
                        problematic_rows.add(index)
                        problematic_rows.add(dict_df[compare_key])

        result_df = pd.DataFrame(columns=df.columns)

        problematic_rows = sorted(problematic_rows)

        if len(problematic_rows) > 0:
            for value in problematic_rows:
                row = df.iloc[value]
                result_df = result_df.append(row)
        return result_df

    # convert erroneous names found in the error_names DB to proper names using HSall dataset which has correct names and bio_id
    #
    def reset_erroneous_names(self, df_error_names: pd.DataFrame, df_correct_names: pd.DataFrame,
                              limit_similarity):
        # df error_names how should we compare and decide if they are the same name or not
        # 1. year -> calculate with congress number, 2. state, 3. first and last name -> set the similarity and decide accordingly
        # if one side has only one name -> compare only that part and see -> store this in to another dataframe and return it.
        # if two names exist but has less similarity -> changes
        # how about comparing the whole name rather than first and last name -> not really sure if this is a good way since they have different order of naming convention.
        # first and last name comparison should be a better way.
        # s1 = SequenceMatcher(None, row['candidate'], compare_name1).ratio()
        # rows that are not assigned with bioguide is the error names that has no similarity in the hsall data -> need to deal with seperately.
        for index, row in df_error_names.iterrows():
            state_po = row['state_po']
            last_name = row['last_name']
            first_name = row['first_name']
            office = 'House' if row['office'] == 'US HOUSE' else 'Senate' if row[
                                                                                 'office'] == 'US SENATE' else 'President'
            congress_no = ((row['year'] + 1 - 1789) / 2) + 1

            df_error_names.at[index, 'congress'] = congress_no

            # president dataset does not have district column
            if office != 'President':
                # in senate dataset, there is only statewide district code.
                district = 0 if row['district'] == 'statewide' else row['district']

                # there is a case there is 0 district which mean there is only one district in the state.
                # in this case Hsall dataset takes that district to number 1 district not 0
                # we are modifying in here to match those numbers.
                if office == 'House' and district == 0:
                    district = 1

                correct_rows = df_correct_names.loc[
                    (df_correct_names['congress'] == congress_no) & (df_correct_names['state_abbrev'] == state_po) & (
                            df_correct_names['chamber'] == office) & (df_correct_names['district_code'] == district)]
            else:
                correct_rows = df_correct_names.loc[
                    (df_correct_names['congress'] == congress_no) & (df_correct_names['state_abbrev'] == state_po) & (
                            df_correct_names['chamber'] == office)]

            for inner_index, inner_row in correct_rows.iterrows():

                first_similarity = None
                last_similarity = None

                if inner_row['first_name'] is not None and first_name is not None:
                    first_similarity = SequenceMatcher(None, inner_row['first_name'], first_name).ratio()
                if inner_row['last_name'] is not None and last_name is not None:
                    last_similarity = SequenceMatcher(None, inner_row['last_name'], last_name).ratio()

                if first_similarity is not None and last_similarity is not None:
                    avg_similarity = (first_similarity * 0.3 + last_similarity * 0.7)
                elif first_similarity is not None:
                    avg_similarity = first_similarity
                elif last_similarity is not None:
                    avg_similarity = last_similarity
                else:
                    avg_similarity = 0

                f_name_match = False
                if last_similarity == 1 and first_name is not None and inner_row['first_name'] is not None:
                    # if first_name == inner_row['first_name'][0]:
                    f_name_match = True

                if avg_similarity > limit_similarity or f_name_match:
                    df_error_names.at[index, 'candidate'] = inner_row['bioname']
                    df_error_names.at[index, 'first_name'] = inner_row['first_name']
                    df_error_names.at[index, 'last_name'] = inner_row['last_name']
                    df_error_names.at[index, 'bioguide_id'] = inner_row['bioguide_id']
                    # df_error_names.at[index, 'nickname'] = inner_row['nickname']
                    # df_error_names.at[index, 'suffix'] = inner_row['suffix']

        df_error_names = df_error_names.replace({np.nan: None})
        return df_error_names

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

    def __del__(self):
        self.conn.close()

import sqlite3
import pandas as pd
from difflib import SequenceMatcher
import numpy as np
import math


class h_s_converter:

    def __init__(self, conn):
        self.conn = conn

    def upload_df_to_database(self, df: pd.DataFrame, name: str):
        df.to_sql(name, self.conn, if_exists='replace')

    def retrieve_df_from_database(self, db_name):

        query = """
                SELECT *
                FROM {};
            """.format(db_name)

        df = pd.read_sql_query(query, self.conn)
        return df

    # Convert the House and Senate databases, adding Democratic and Republican votes(respective districts and states).
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
        # I put special here - > shoul be modified later I think. special data set-> the output query below also have special election data seperated from the normal one.
        #  Therefore, the query coming after blow query should be implemented using which election between special and normal
        # applied -> need to decide first which one we should apply.
        senate_query = """
            SELECT year, state, state_po, office, district,special, stage, candidate, {}, candidatevotes, 
            CAST(( CASE WHEN MAX(totalvotes) IS NULL THEN 0 ELSE MAX(totalvotes) END ) AS INTEGER) AS totalvotes,
            CAST( ( CASE WHEN MAX(democratvotes) IS NULL THEN 0 ELSE MAX(democratvotes) END ) AS INTEGER) AS democratvotes, 
            CAST((CASE WHEN MAX(republicanvotes) IS NULL THEN 0 ELSE MAX(republicanvotes) END) AS INTEGER) AS republicanvotes
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

        df = pd.read_sql_query(senate_query, self.conn)

        self.interpret_names(df)

        print(df.columns)

        self.upload_df_to_database(df, modified_table)

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
                    SELECT SUM(democratvotes)AS dems_total_votes_state, SUM(republicanvotes) as gop_total_votes_state, SUM(totalvotes) as total_votes_state,state_po, year
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

        df = self.retrieve_df_from_database(modified_table)
        return df

    # interprete names to distinguish first and last name.
    def interpret_names(self, df):

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

    # retrieve names that are same person but has different names in different election.
    # we can modify the level of similarity using limit_similarity argument. (1 means exactly same 0 means total difference)
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
    #  running this function after matching the names that are similar is recommended.
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

    # reflect history stored in database. (Name is indicated in history_db_name)
    def reflect_name_correction_history(self, history_db_name):

        query = """
                   SELECT *
                   FROM {}
               """.format(history_db_name)

        history_df = pd.read_sql_query(query, self.conn)
        cursor = self.conn.cursor()

        for index, row in history_df.iterrows():
            query = """
                                  UPDATE {}
                                  SET first_name = '{}', last_name = '{}',candidate = '{}', bioguide_id = '{}', match = 1
                                  WHERE rowid = {};
                          """.format(row['origin_table'], row['first_name'], row['last_name'], row['full_name'],
                                     row['bioguide_id'], int(row['id']))

            cursor.execute(query)
            self.conn.commit()

    # convert erroneous names found in the error_names DB to proper names using HSall dataset which has correct names and bio_id
    # match names that does not match with names in HSALL dataset using similarity.
    # if the name is similar enough (based on limit_similarity, if the similarrity is larger than limit similarity),
    # it changes the names to names in HSALL dataset.
    # INPUT: df_error_names -> dataframe that has names to be modified, df_correct_names -> dataframe that has correct names(should be hsall dataset)
    # limit_similarity: similarity where we want to automatically match the names if the similarity of the names exceed.
    def auto_correct_names(self, df_error_names: pd.DataFrame, df_correct_names: pd.DataFrame,
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
                # in this case Hsall dataset takes that district as number 1 district not 0
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
                    # if it found the match -> need to indicate it so that I can use if it is matched orr not later in the ui.
                    df_error_names.at[index, 'match'] = 1
                    # df_error_names.at[index, 'nickname'] = inner_row['nickname']
                    # df_error_names.at[index, 'suffix'] = inner_row['suffix']

        df_error_names = df_error_names.replace({np.nan: None})
        return df_error_names

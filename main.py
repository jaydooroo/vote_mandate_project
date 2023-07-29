import sqlite3
import pandas as pd

import president_converter as president
import h_s_converter as h_s
import hsall_converter as hsall
import ultimate_converter as ult

from name_app_view import View, DBFrame, TreeviewFrame, SuggestionTreeviewFrame, LabelFrame
from name_app_model import Model
from name_app_controller import Controller

conn = sqlite3.connect('total_info.db')

#
# # house and senate db converter (adding democrat and republican votes to the respective districts and states).
# h_s_converter = h_s.h_s_converter(conn)
#
# # hsall converter. HSALL date is where nominate data exists
# hsall_converter = hsall.hsall_converter(conn)
#
# # Rtrieve hsall from the database.
# df_HSall = hsall_converter.convert_HSall_database()
#
# # retrieve senate data and check incorrect names as well as party changes history.
# df_senate = h_s_converter.convert_database('s')
# df_error_names_senate = h_s_converter.check_names(df_senate, 0.7)
# df_senate_party_changes = h_s_converter.check_party_changes(df_senate)
#
# # correct names automatically.
# df_senate = h_s_converter.auto_correct_names(df_senate, df_HSall, 0.8)
# df_senate = df_senate.drop(['index'], axis=1)
# h_s_converter.upload_df_to_database(df_senate, "name_modified_senate")
#
#
# # retrieve house data and check incorrect names as well as part changes history.
# df_house = h_s_converter.convert_database('h')
# df_error_names_house = h_s_converter.check_names(df_house, 0.7)
# df_house_party_changes = h_s_converter.check_party_changes(df_house)
#
# df_house = h_s_converter.auto_correct_names(df_house, df_HSall, 0.8)
# df_house = df_house.drop(['index'], axis=1)
# h_s_converter.upload_df_to_database(df_house, "name_modified_house")
#
# # upload erroneous or party changed names if exists.
# if len(df_error_names_house) > 0:
#     h_s_converter.upload_df_to_database(df_error_names_house, 'house_error_names')
#
# if len(df_house_party_changes) > 0:
#     h_s_converter.upload_df_to_database(df_house_party_changes, 'list_house_party_change')
#
# if len(df_error_names_senate) > 0:
#     h_s_converter.upload_df_to_database(df_error_names_senate, 'senate_error_names')
#
# if len(df_senate_party_changes) > 0:
#     h_s_converter.upload_df_to_database(df_senate_party_changes, 'list_senate_party_change')
#
#
# # president data converter
# # convert president database to modified version of it.
# p_converter = president.president_converter(conn)
# p_converter.convert_database()
#
# # retrieve modified version of president data
# p_df = p_converter.retrieve_df_from_db("name_modified_president")
#
# # interpret names in president data to discern first and last names
# p_df = p_converter.interpret_names(p_df)
#
# # automatically assign correct names to the president data.
# # the correct names come from HSALL database.
# p_df = p_converter.auto_correct_names(p_df, df_HSall, 0.8)
#
# # upload dataframe to the database.
# p_converter.upload_df_to_database(p_df, "name_modified_president")
#
# # automatically reflect name correction history that was created before using program below.
# h_s_converter.reflect_name_correction_history('names_modified_history')
#
#
# # user interface that is used to assign bioguide_id or correct names manually.
# controller = Controller('total_info.db', 'name_modified_house', 'name_modified_HSall')
# view = View(controller)
# controller.set_view(view)
# controller.run()

# converter that is used to merge and add additional variables
ultimate_converter = ult.ultimate_converter(conn)

ultimate_converter.merge_nokken_poole_with_h_s()
ultimate_converter.add_subterm_senate()
ultimate_converter.add_recent_avg_senate_vote_share()
ultimate_converter.add_pres_vote_share()
ultimate_converter.add_fellow_senate_vote_share()
ultimate_converter.create_result_table()

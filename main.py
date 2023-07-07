import sqlite3
import pandas as pd

import database_converter
import president_converter as president
import h_s_converter as h_s
import hsall_converter as hsall
import ultimate_conterter as ult

from name_app_view import View, DBFrame, TreeviewFrame, SuggestionTreeviewFrame, LabelFrame
from name_app_model import Model
from name_app_controller import Controller

conn = sqlite3.connect('total_info.db')

db_converter = database_converter.database_converter(conn)
h_s_converter = h_s.h_s_converter(conn)
hsall_converter = hsall.hsall_converter(conn)
ultimate_conterter = ult.ultimate_conterter(conn)

df_senate = db_converter.convert_database('s')
df_error_names_senate = db_converter.check_names(df_senate, 0.7)
df_senate_party_changes = db_converter.check_party_changes(df_senate)

df_house = db_converter.convert_database('h')
df_error_names_house = db_converter.check_names(df_house, 0.7)
df_house_party_changes = db_converter.check_party_changes(df_house)

if len(df_error_names_house) > 0:
    db_converter.upload_df_to_database(df_error_names_house, 'house_error_names')

if len(df_house_party_changes) > 0:
    db_converter.upload_df_to_database(df_house_party_changes, 'list_house_party_change')

if len(df_error_names_senate) > 0:
    db_converter.upload_df_to_database(df_error_names_senate, 'senate_error_names')

if len(df_senate_party_changes) > 0:
    db_converter.upload_df_to_database(df_senate_party_changes, 'list_senate_party_change')
#
df_HSall, df_error = db_converter.convert_HSall_database()

df_error_names_house = db_converter.reset_erroneous_names(df_error_names_house, df_HSall, 0.8)

db_converter.upload_df_to_database(df_error_names_house, 'test_error_names_fixed')

controller = Controller('total_info.db', 'test_error_names_fixed', 'name_modified_HSall')
view = View(controller)
controller.set_view(view)
controller.run()

db_converter.merge_nokken_poole_with_votes()
db_converter.add_subterm_senate()
db_converter.add_recent_avg_senate_vote_share()

p_converter = president_converter.president_converter(conn)
p_converter.convert_database()

p_df = p_converter.retrieve_df_from_db("name_modified_president")
p_df = p_converter.interprete_names(p_df)
p_df = p_converter.reset_erroneous_name(p_df, df_HSall, 0.8)
p_converter.upload_df_to_database(p_df, "name_modified_president")

controller = Controller('total_info.db', 'name_modified_president', 'name_modified_HSall')
view = View(controller)
controller.set_view(view)
controller.run()


#
# p_converter.upload_df_to_database(p_df)


# name_ui = ctr.Controller( 'total_info.db', 'test_error_names_fixed', 'name_modified_HSall')
# name_ui.run()


# name_ui = name_correction_ui.name_correction_App()
#
# treeview = name_correction_ui.TreeviewFrame(name_ui, conn, 'test_error_names_fixed', 'name_modified_HSall')
#
#
#
# name_ui.mainloop()

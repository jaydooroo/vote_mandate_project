import sqlite3
import pandas as pd

import database_converter

from name_app_view import View, DBFrame, TreeviewFrame, SuggestionTreeviewFrame, LabelFrame
from name_app_model import Model
from name_app_controller import Controller

conn = sqlite3.connect('total_info.db')
# #
db_converter = database_converter.database_converter(conn)

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

df_HSall, df_error = db_converter.convert_HSall_database()

df_error_names_house = db_converter.reset_erroneous_names(df_error_names_house, df_HSall, 0.8)

db_converter.upload_df_to_database(df_error_names_house, 'test_error_names_fixed')

controller = Controller('total_info.db', 'test_error_names_fixed', 'name_modified_HSall')
view = View(controller)
controller.set_view(view)
controller.run()

# name_ui = ctr.Controller( 'total_info.db', 'test_error_names_fixed', 'name_modified_HSall')
# name_ui.run()


# name_ui = name_correction_ui.name_correction_App()
#
# treeview = name_correction_ui.TreeviewFrame(name_ui, conn, 'test_error_names_fixed', 'name_modified_HSall')
#
#
#
# name_ui.mainloop()

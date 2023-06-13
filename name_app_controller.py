import sqlite3
import tkinter
import pandas as pd
from database_converter import database_converter
from tkinter import *
from tkinter import ttk
import tkinter as tk
from difflib import SequenceMatcher
from name_app_model import Model


class Controller:
    def __init__(self, db_path, error_db_name, correct_db_name):
        self.view = None
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.error_db_name = error_db_name
        self.correct_db_name = correct_db_name
        error_df = self.retrieve_df_from_db(error_db_name)
        correct_df = self.retrieve_df_from_db(correct_db_name)
        self.model = Model(error_df, correct_df)

        self.converter = database_converter(self.conn)
        # self.view = View(self)

    def run(self):
        if self.view is not None:
            self.view.mainloop()

    def set_view(self, view):
        from name_app_view import View, DBFrame, TreeviewFrame, SuggestionTreeviewFrame, LabelFrame
        self.view = view

    def retrieve_df_from_db(self, db_name):
        query = """
                SELECT *
                FROM {};
            """.format(db_name)

        df = pd.read_sql_query(query, self.conn)
        return df

    def retrieve_selected_df(self, db_name, values):
        state_po = values[3]
        congress = int(float(values[2]))
        office = 'House' if values[4] == 'US HOUSE' else 'Senate' if values[4] == 'US SENATE' else 'President'

        query = """
                  SELECT *
                  FROM {}
                  WHERE state_abbrev = '{}' AND congress = '{}' AND chamber = '{}'
          """.format(db_name, state_po, congress, office)
        # full name comparosion, add similarity column and sort by using that column's value.

        df_sug_names = pd.read_sql_query(query, self.conn)
        original_full_name = values[7]

        for index, row in df_sug_names.iterrows():
            full_name = row['bioname']
            similarity = SequenceMatcher(None, full_name, original_full_name).ratio()
            df_sug_names.loc[index, 'similarity'] = similarity

        df_sug_names = df_sug_names.sort_values(by=['similarity'], ascending=False)

        return df_sug_names

    def update_treeview(self, values):
        self.view.update_treeview(values)

    def update_label_entries(self, values):
        self.view.update_label_entries(values)

    def update_names(self, values):
        self.view.update_names(values)

    def upload_values(self, values_dict):
        id = values_dict['id']
        first_name = values_dict['first_name']
        last_name = values_dict['last_name']
        full_name = values_dict['full_name']
        bio_id = values_dict['bio_id']

        if id != "" and bio_id != "":
            query = """
                           UPDATE {}
                           SET first_name = '{}', last_name = '{}', candidate = '{}', bioguide_id = '{}'
                           WHERE rowid = {};
                   """.format(self.error_db_name, first_name, last_name, full_name, bio_id, int(id) + 1)

            cursor = self.conn.cursor()
            cursor.execute(query)
            self.conn.commit()

    def pull_error_df(self):
        return self.model.pull_error_df()

    def pull_correct_df(self):
        return self.model.pull_correct_df()

    def update_db(self, correct_db_name, error_db_name, db_path):
        self.db_path = db_path
        self.correct_db_name = correct_db_name
        self.error_db_name = error_db_name

        self.refresh_all()

    # check if the new_error_df has bioguide_id if there is none, run reset erroneous names method in converter to assign proper names into it.
    # need to set it on database first and retrieve it after that.
    # It could be better to apply this functionality into retrieve df from db method.Need to carefully plan this.

    def refresh_all(self):
        new_correct_df = self.retrieve_df_from_db(self.correct_db_name)
        new_error_df = self.retrieve_df_from_db(self.error_db_name)

        if 'bioguide_id' not in new_error_df:
            new_error_df = self.converter.reset_erroneous_names(new_error_df, new_correct_df, 0.8)
            new_error_df = new_error_df.drop(['index'], axis=1)
            self.converter.upload_df_to_database(new_error_df, self.error_db_name)
        self.model.push_error_df(new_error_df)
        self.model.push_correct_df(new_correct_df)
        self.view.refresh_all()

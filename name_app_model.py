import sqlite3
import tkinter
import pandas as pd
from tkinter import *
from tkinter import ttk
import tkinter as tk


# from name_app_view import View, DBFrame, TreeviewFrame, SuggestionTreeviewFrame, LabelFrame
# from name_app_controller import Controller

class Model:
    def __init__(self, error_df, correct_df):
        self.error_df = error_df
        self.correct_df = correct_df

    def push_error_df(self, error_df):
        self.error_df = error_df

    def push_correct_df(self, correct_df):
        self.correct_df = correct_df

    def pull_error_df(self):
        return self.error_df

    def pull_correct_df(self):
        return self.correct_df

import sqlite3
import pandas as pd


class sas_converter:

    def __init__(self, conn):
        self.conn = conn

    def import_and_upload_sas(self):

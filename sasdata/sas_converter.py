import sqlite3
import pandas as pd
# from sas7bdat import SAS7BDAT


class sas_converter:

    def __init__(self, conn):
        self.conn = conn

    def import_and_upload_sas(self):
        file_loc = "election_returns_icspr.sas7bdat"

        df_sas = pd.read_sas(file_loc)

        df_sas.to_sql('sas_election_returns', self.conn, if_exists='replace')


    def convert_dataframe(self):
        query = """
            
        """


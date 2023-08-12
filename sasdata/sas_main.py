import sqlite3
import pandas as pd
import sas_converter as sas


conn = sqlite3.connect('../total_info.db')

s_converter = sas.sas_converter(conn)

s_converter.import_and_upload_sas()
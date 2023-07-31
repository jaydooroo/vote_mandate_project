# vote_mandate_project

## Description

The main purpose of the vote_mandate_project is to generate variables that are used for election and politician types research. The program uses Python to process data and SQLite to store and manage the datasets.

The program generates the following variables:
 

### nokken_poole_dim1
- **Description**: Nokken-Poole First dimension estimate.

---
### modified_nokken_poole_dim1

- **Description**: It is basically same with Nokken-Poole First dimension estimate, However,
- it is equal to nokken_poole_dim1 for Republicans and equal to (-1)*(nokken_poole_dim1) for Democrats.
- Other party member has NULL value for this variable. 

---
### vote_share
- **Description**: It represents the vote shares for the candidate of the respective election they had.

---
### dems_vote_share_district

- **Description**: It represents the total Democratic party vote shares in the particular district (If many other parties support a single candidate, we combine all the votes and consider it as the major party votes).
---
### gop_vote_share_district
- **Description**: It represents the total Democratic party vote shares in the particular district (If many other parties support a single candidate, we combine all the votes and consider it as the major party votes).
---
### dems_vote_share_state
- **Description**: It represents the total Democratic party vote shares in the particular state (If many other parties support a single candidate, we combine all the votes and consider it as the major party votes).
---

### gop_vote_share_state
- **Description**: It represents the total Republican party vote shares in the particular state (If many other parties support a single candidate, we combine all the votes and consider it as the major party votes).
---
### recent_dems_vote_share_senate
- **Description**: It represents the Democrat vote shares of the Senator with the lowest subterm value (most recent election result of the particular state for a senator).
---
### recent_gop_vote_share_senate

- **Description**: It represents the Republican vote shares of the Senator with the lowest subterm value (most recent election result of the particular state for a senator).
---

### recent_dems_vote_share_house
- **Description**: It represents the Democrat vote shares of the congressman with the most recent election result of the particular state (basically same as dems_vote_share_state for the House election).
---

### recent_gop_vote_share_house
- **Description**: It represents the Republican vote shares of the congressman with the most recent election result of the particular state (basically same as gop_vote_share_state for the House election).
---

### dems_avg_vote_share_senate
- **Description**: It represents the average Democrat vote shares of the two senators for that state/year. 
---

### gop_avg_vote_share_senate
- **Description**: It represents the average Republican vote shares of the two senators for that state/year. 
---

### dems_pres_vote_share
- **Description**: democrat vote shares of the most recent presidential election.
---

### gop_pres_vote_share
- **Description**: republican vote shares of the most recent presidential election.
---
### fellow_senate_vote_share

- **Description**:  variable that equals the party vote share in the other senate race from the same state.  
- Suppose, for example, that senators A and B from Colorado won their most recent elections 52%-47% and 55%-41%, respectively.  
- If A is a Republican but B is a Democrat, then the fellow_senate_share variable should equal 41% for senator A and 47% for senator B.  If A and B are both Democrats then fellow_senate_share should equal 55% for senator A and 52% for senator B.
---
### subterm
- **Description**: subterm for senator
---

The more explanation of each variable is described in codebook-merged_nokken_pool_1976_2020.md file.

There are three big parts of this program.
The big three parts consist of upload, converter, User interface. 

The Upload file is "politic_info_upload.py"
The Converter files are "h_s_converter", "hsall_converter", "president_converter", "ultimate_converter"
The ui part is consist of "name_app_controller", "name_app_model" and "name_app_view".

The main.py file instantiate and calls the classes and runs in the proper order.

---
## UPLOAD (politic_info_upload.py file).
        
The Upload part is responsible for uploading the required CSV files into an SQLite database named total_info.db. This database will serve as the central repository for all the election-related data. The CSV files that are uploaded include:

'1976-2020-senate.csv': Contains data on Senate elections from 1976 to 2020.

'1976-2020-house.csv': Contains data on House elections from 1976 to 2020.

'1976-2020-president.csv': Contains data on Presidential elections from 1976 to 2020.

'HSall_members.csv': Contains data on all members of the House of Representatives and the Senate.


Each CSV file corresponds to a specific table within the database:

Table 'from1976to2020_senate': Holds data on Senate elections.

Table 'from1976to2020_house': Stores data on House elections.

Table 'from1976to2020_president': Stores data on Presidential elections.

Table 'HSall_members': Contains information on all House and Senate members.

The process of uploading involves reading the data from the CSV files and creating the respective tables in the SQLite database. This step is crucial as it sets the foundation for data processing and analysis in the later stages of the project.

---
## CONVERTER (h_s_converter, hsall_converter,president_converter).
        
The Converter part consists of multiple Python scripts designed to prepare and manipulate the data from the uploaded CSV files for compatibility and merging. Each converter script serves a specific purpose:

Frist, h_s_converter convert 
        
### h_s_converter: 
This Python script is designed to convert and correct names in a database, 
specifically for House and Senate elections. It uses the SQLite library and Pandas for data manipulation and analysis.

- **Features**

The script provides the following features:

1. Upload a DataFrame to an SQLite database.
2. Retrieve a DataFrame from an SQLite database.
3. Convert the House and Senate databases, adding Democratic and Republican votes(respective districts and states).
4. Interpret names to discern first and last names.
5. Check for erroneous names in the database based on similarity.
6. Check for party changes in the database.
7. Reflect the name correction history stored in the database.(we can store the correction history using UI)
8. Automatically correct names using a separate database of correct names and bioguide IDs.

- **Usage**

1. Establish a connection to your SQLite database.
2. Create an instance of the h_s_converter class, passing the database connection as a parameter.
3. Use the class methods to perform the desired operations, such as uploading a DataFrame, converting the database, checking names, and correcting names.
4. The results can be stored in a new table or retrieved as a DataFrame for further analysis or processing.

- **Example**

```python
import sqlite3
import pandas as pd

# Import the h_s_converter class from the script
from h_s_converter import h_s_converter

# Establish a connection to the SQLite database
conn = sqlite3.connect('database.db')

# Create an instance of the h_s_converter class
converter = h_s_converter(conn)

# Upload a DataFrame to the database
df = pd.DataFrame(...)
converter.upload_df_to_database(df, 'table_name')

# Convert the House or Senate database
converted_df = converter.convert_database('H')

# Check for erroneous names in the database
error_names_df = converter.check_names(converted_df, 0.9)

# Automatically correct names using a separate database
corrected_df = converter.auto_correct_names(error_names_df, correct_names_df, 0.8)

# Retrieve a DataFrame from the database
retrieved_df = converter.retrieve_df_from_database('table_name')

# Close the database connection
conn.close()
```

### hsall_converter
The hsall_converter class is designed to convert and interpret data from the "HSall_members" database and store the modified data in the "name_modified_HSall" table. It also includes a function to upload a DataFrame to the database.

- **Features**

The script provides the following features:

**'upload_df_to_database(df: pd.DataFrame, name: str)':**

Uploads a DataFrame to the SQLite database with the given name. 
    If the table already exists, it will be replaced.

**'convert_HSall_database()':**

Retrieves data from the "HSall_members" table and interprets names to discern first name and last name.
The modified data is stored in the "name_modified_HSall" table. 
Any names that cannot be interpreted are stored in the "HSall_undefined_names" table.

Returns: The modified DataFrame containing the interpreted names.

- **Usage**

1. Establish a connection to your SQLite database.
2. Create an instance of the h_s_converter class, passing the database connection as a parameter.
3. Use the class methods to perform the desired operations, such as uploading a DataFrame, converting the database, checking names, and correcting names.
4. The results can be stored in a new table or retrieved as a DataFrame for further analysis or processing.

- **Example**

```python
# Initialize SQLite connection
conn = sqlite3.connect('your_database_file.db')

# Create an instance of hsall_converter
converter = hsall_converter(conn)

# Convert and interpret HSall database
modified_df = converter.convert_HSall_database()

# Close the connection
conn.close()
```

### president_converter

The president_converter class is designed to convert and interpret data from a database containing information about US Presidential elections. It performs various operations on the data, including name interpretation, auto-correcting names based on similarity, and creating a modified table containing aggregated election data for major candidates (Democrats and Republicans) for each year.


- **Features**

**'upload_df_to_database(df: pd.DataFrame, name: str)':**
    
Uploads a DataFrame to the SQLite database with the given name. If the table already exists, it will be replaced.

**'retrieve_df_from_db(table_name: str)':**

Retrieves a DataFrame from the SQLite database based on the provided table name.

**'convert_database()':**

Performs various database operations to create a modified table named "name_modified_president" containing aggregated election data for major candidates (Democrats and Republicans) for each year.

**'auto_correct_names(df_error_names: pd.DataFrame, df_correct_names: pd.DataFrame, limit_similarity: float)':**

Automatically assigns names from the HSALL database to the names in the "name_modified_president" database using similarity. The limit_similarity parameter determines the minimum similarity required for the auto-correction.

**'interpret_names(df: pd.DataFrame)':**

Interpret names and sets first and last names according to the names in the DataFrame.

- **Example**

```python
# Initialize SQLite connection
conn = sqlite3.connect('your_database_file.db')

# Create an instance of president_converter
converter = president_converter(conn)

# Convert the database
converter.convert_database()

# Retrieve the modified DataFrame from the database
modified_df = converter.retrieve_df_from_db('name_modified_president')

# Close the connection
conn.close()
```

### ultimate_converter

The ultimate_converter class is designed to perform various data manipulation and merging operations on three different databases containing information about US House, US Senate, and US Presidential elections. It merges the data from these databases and adds additional columns to create a final, comprehensive dataset containing vote share information for different candidates in various elections.


- **Features**

**'upload_df_to_database(df: pd.DataFrame, name: str)':**
    
Uploads a DataFrame to the SQLite database with the given name. If the table already exists, it will be replaced.

**'merge_nokken_poole_with_h_s()':**

Merges the HSALL database with the House and Senate databases using a LEFT JOIN operation based on common fields such as bioguide_id or candidate name, state, congress, and chamber. The result is stored in a new table named "merged_nokken_pool".

**'add_pres_vote_share()':**

Adds presidential election vote share for Democrats and Republicans to the "merged_nokken_pool" table. It calculates the vote share for the most recent presidential election for each congress.

**'add_subterm_senate()':**

Adds a "subterm" column to the "merged_nokken_pool" table. The "subterm" indicates if the senators are serving their first, second, or third term since they have a 6-year term. It calculates the subterm for each senator based on their vote share data.

**'add_recent_avg_senate_vote_share()':**

Adds recent and average vote share for Senate candidates to the "merged_nokken_pool" table. The recent vote share refers to the most recent vote share for senatorial elections in the same state. The average vote share is the average vote share for Senate candidates for each year and state.

**'add_fellow_senate_vote_share()':** 
Adds fellow senate vote share that equals the party vote share in the other senate race from the same state.

**'create_result_table()':**
    
Drops all rows that do not have vote share data and saves the modified dataset to a new table named "merged_nokken_poole_1976_2020". This table will contain the final, comprehensive dataset with vote share information for different candidates in various elections.

- **Example**

```python
# Initialize SQLite connection
conn = sqlite3.connect('your_database_file.db')

# Create an instance of ultimate_converter
converter = ultimate_converter(conn)

# Merge HSALL data with House and Senate data
converter.merge_nokken_poole_with_h_s()

# Add presidential election vote share
converter.add_pres_vote_share()

# Add subterm for Senate candidates
converter.add_subterm_senate()

# Add recent and average vote share for Senate candidates
converter.add_recent_avg_senate_vote_share()

#Add add_fellow_senate_vote_share
converter.add_fellow_senate_vote_share()

# Create the final result table
converter.create_result_table()

# Close the connection
conn.close()
```

The methods in the ultimate_converter class perform complex operations, so make sure you have the required data in the database before executing them

---

## Graphic User Interface for manual name correction (UI)

The UI part of the project provides a user-friendly graphical interface for manually assigning names from the HSall dataset to the names in other datasets. It is particularly useful when automatic name correction in the converter is not sufficient to match all names in the dataset.


The UI consists of three main components:

- name_app_view.py: This component handles the graphical layout and display of the UI elements, including lists of unmatched names and suggested names.

- name_app_model.py: This component deals with data manipulation and processing. It manages the retrieval and storage of data and handles any modifications made during the name correction process.

- name_app_controller.py: This component acts as the bridge between the view and the model. It manages the interactions between the user interface and the underlying data processing functionalities. For example, when a user selects a name from the unmatched list, the controller can fetch and display the corresponding suggested names for manual correction.

The UI allows users to manually assign correct names and bioguide IDs from the HSall dataset to the unmatched names in the other datasets. Users can upload the modified information back to the database and save the history of modifications for future reference.


---
## User's Guide for UI

The UI component of the vote_mandate_project provides a graphical user interface that allows users to manually assign correct names and bioguide IDs from the HSall dataset to the unmatched names in the other datasets (senate, house, president). This guide explains how to use the UI and its functionalities effectively.


![img.png](img.png)
![img_2.png](img_2.png)


### Database Info Section:

correct_db_name : Enter the name of the table in the SQLite database that contains the correct names and bioguide IDs. Typically, this table should be from the HSall dataset.

error_db_name: Enter the name of the table in the SQLite database that contains the names to be compared with the correct names from the HSall dataset. This table should contain data from Senate, House, or Presidential elections.

db location:  Provide the path or location where the SQLite database exists on your system.

### Main Window:
The main window displays a list of unmatched names from the "Error Database Name" table. If you click on any row in the list, the window will show a list of suggested names from the HSall dataset that could potentially match the unmatched name.

### Editor Section:
The editor section displays all the necessary information of the row that is currently selected (clicked) in the main window. It includes information about the candidate, state, and other relevant details.

### Suggested Names:
If you click on a row in the main window, a list of suggested names from the HSall dataset will appear. This list can help you identify and assign the correct name and bioguide ID for the unmatched name. If you click on a row in the suggestion window, it automatically updates the name and bio_id accordingly. 

### Updating Names and Bioguide IDs:
If you click on a row in the main window and list of suggested names, the name boxes and bioguide_id box in the editor section will be updated accordingly. You can use this feature to manually assign the correct information to the unmatched name.

### Upload Button:
The "Upload" button allows you to update the table that has names(error_db_name) to be fixed in the database with the modified information provided in the editor section. Typically, this button is used after manually correcting names and bioguide IDs.

### Refresh Button:
The "Refresh" button retrieves the data from the database again and updates the list of unmatched names in the main window. Use this button if you want to see the latest data from the database.(after 'upload', it is automatically run)

### Save History Check Button:
When you upload the modified information and click the "Save History" button, it saves all the history of modifications in the database. This feature can be helpful for keeping track of changes and for reference in the future.

### Clear All History Button:
The "Clear All History" button clears all the history stored in the history table in the database. Use this button if you want to start fresh without any previous modification records.

### Reflect History Button:
The "Reflect History" button reflects all the past modification history to the current one. This means it will load all the changes and apply them. This can save you time if you need to make further modifications based on previous corrections.

### Delete Current DB History Button:
The "Delete Current DB History" button deletes only the modification history of the current "Error Database Name" table. It does not affect the history of other tables in the database.

This UI provides an efficient and user-friendly way to handle name corrections and bioguide ID assignments manually. Follow the instructions above to make use of the features effectively. If you have any questions or encounter any issues, refer to this guide or consult the documentation for the vote_mandate_project.


  
import sqlite3
import tkinter
import pandas as pd
import database_converter
from tkinter import *
from tkinter import ttk
import tkinter as tk
from difflib import SequenceMatcher
from tkinter import filedialog
from name_app_controller import Controller


class View(tk.Tk):
    def __init__(self, controller: Controller):
        super().__init__()
        self.title('name_correction_ui')
        self.geometry("1200x600")
        self.controller = controller

        main_frame = Frame(self)
        main_frame.pack(fill=BOTH, expand=1)

        # Create a canvas and scrollbar
        canvas = tk.Canvas(main_frame)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        # Configure the canvas scrolling
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Create a frame inside the canvas to hold the content
        content_frame = tk.Frame(canvas)

        # Add the content frame to the canvas
        canvas.create_window((0, 0), window=content_frame, anchor="nw")

        # Add the canvas to the main window
        canvas.pack(side="left", fill="both", expand=True)

        self.db_frame = DBFrame(content_frame, controller)
        self.treeview_frame = TreeviewFrame(content_frame, controller)
        self.suggestion_treeview_frame = SuggestionTreeviewFrame(content_frame, controller)
        self.label_frame = LabelFrame(content_frame, controller)

    def update_treeview(self, values):
        self.suggestion_treeview_frame.update_treeview(values)

    def update_label_entries(self, values):
        self.label_frame.update_entries(values)

    def update_names(self, values):
        self.label_frame.update_names(values)

    def refresh_all(self):
        self.treeview_frame.refresh_treeview()
        self.label_frame.clear_all()
        self.suggestion_treeview_frame.clear_treeview()


class TreeviewFrame(ttk.Frame):
    def __init__(self, container, controller: Controller):
        super().__init__(container)
        self.controller = controller
        self.pack(pady=10)
        self.my_tree = self.__create_widgets()

    def __create_widgets(self):

        tree_scroll = Scrollbar(self)
        tree_scroll.pack(side=RIGHT, fill=Y)
        my_tree = ttk.Treeview(self, yscrollcommand=tree_scroll.set, selectmode="browse")
        my_tree.pack()

        my_tree['columns'] = (
            "index", "year", "congress", "state_po", "office", "district", "first_name", "last_name",
            "full_name", "special", "stage")
        my_tree.column('#0', width=0, stretch=NO)
        my_tree.column("index", anchor=CENTER, width=90)
        my_tree.column("year", anchor=CENTER, width=90)
        my_tree.column("congress", anchor=CENTER, width=90)
        my_tree.column("state_po", anchor=CENTER, width=90)
        my_tree.column("office", anchor=CENTER, width=90)
        my_tree.column('district', anchor=CENTER, width=90)
        my_tree.column('special', anchor=CENTER, width=90)
        my_tree.column("first_name", anchor=W, width=90)
        my_tree.column("last_name", anchor=W, width=90)
        my_tree.column("full_name", anchor=W, width=180)
        my_tree.column("stage", anchor=CENTER, width=90)

        my_tree.heading("#0", text="", anchor=W)
        my_tree.heading("index", text="index", anchor=W)
        my_tree.heading("year", text="year", anchor=W)
        my_tree.heading("congress", text="congress", anchor=W)
        my_tree.heading("state_po", text="state_po", anchor=W)
        my_tree.heading("office", text="office", anchor=W)
        my_tree.heading('district', text="district", anchor=W)
        my_tree.heading('special', text='special', anchor=W)
        my_tree.heading("first_name", text="first_name", anchor=W)
        my_tree.heading("last_name", text="last_name", anchor=W)
        my_tree.heading("full_name", text="full_name", anchor=W)
        my_tree.heading("stage", text="stage", anchor=W)
        my_tree.tag_configure('oddrow', background="white")
        my_tree.tag_configure('evenrow', background="lightblue")

        # need to check if the index is the index in the database or dropped one
        # any rows that is not assigned to real name and bioguide_id.
        # not really sure if this works for in this another class. It is inheriting the parents which is name_correction_App.
        # not really sure that it can access the parent's variable

        error_df = self.controller.pull_error_df()
        self.add_items(error_df, my_tree)

        my_tree.bind('<<TreeviewSelect>>', self.item_selected)

        return my_tree

    def refresh_treeview(self):
        self.clear_items()
        error_df = self.controller.pull_error_df()
        self.add_items(error_df, self.my_tree)

    def clear_items(self):
        self.my_tree.selection_remove(self.my_tree.focus())
        for i in self.my_tree.get_children():
            self.my_tree.delete(i)

    def add_items(self, df: pd.DataFrame, my_tree):
        # There should be at least bioguide_id, year, state_po, first name, last name, candidate and office columns for this to work properly.

        for index, row in df.iterrows():
            bio = row['bioguide_id']
            year = row['year']
            state_po = row['state_po']
            office = row['office']
            first_name = row['first_name']
            last_name = row['last_name']
            full_name = row['candidate']
            if 'special' in df.columns:
                special = row['special']
            else:
                special = None

            if 'district' in df.columns:
                district = row['district']
            else:
                district = None

            if 'stage' in df.columns:
                stage = row['stage']
            else:
                stage = None

            if bio is None and (row['match'] is None or row['match'] != 1):
                congress_no = ((year + 1 - 1789) / 2) + 1
                my_tree.insert("", 'end', iid=index, values=(
                    index, year, congress_no, state_po, office, district, first_name,
                    last_name,
                    full_name, special, stage))
        # else:

    def item_selected(self, event):

        item_no = self.my_tree.selection()

        print(self.my_tree.item(item_no)['values'])
        values = self.my_tree.item(item_no)['values']
        if len(values) > 3:
            self.controller.update_label_entries(values)
            self.controller.update_treeview(values)


class SuggestionTreeviewFrame(ttk.Frame):
    def __init__(self, container, controller: Controller):
        super().__init__(container)
        self.controller = controller

        Label(self, text='Suggestion', width=30).pack()
        self.pack(padx=10, pady=10)

        self.sug_tree = self.__create_widgets()

    def __create_widgets(self):
        tree_scroll = Scrollbar(self)
        tree_scroll.pack(side=RIGHT, fill=Y)
        sug_tree = ttk.Treeview(self, yscrollcommand=tree_scroll.set, selectmode="browse")
        sug_tree.pack()

        sug_tree['columns'] = ("first_name", "last_name", "full_name", "district", "bioguide_id", "similarity")
        sug_tree.column('#0', width=0, stretch=NO)
        sug_tree.column("first_name", anchor=W, width=90)
        sug_tree.column("last_name", anchor=W, width=90)
        sug_tree.column("full_name", anchor=W, width=180)
        sug_tree.column("district", anchor=W, width=90)
        sug_tree.column("bioguide_id", anchor=W, width=90)
        sug_tree.column("similarity", anchor=W, width=110)

        sug_tree.heading("#0", text="", anchor=W)
        sug_tree.heading("first_name", text="first_name", anchor=W)
        sug_tree.heading("last_name", text="last_name", anchor=W)
        sug_tree.heading("full_name", text="full_name", anchor=W)
        sug_tree.heading("district", text="district", anchor=W)
        sug_tree.heading("bioguide_id", text="bioguide_id", anchor=W)
        sug_tree.heading("similarity", text="similarity", anchor=W)
        sug_tree.bind('<<TreeviewSelect>>', self.item_selected)
        return sug_tree

    def update_treeview(self, values):
        df_sug_names = self.controller.retrieve_selected_df(self.controller.correct_db_name, values)

        self.clear_treeview()

        for index, row in df_sug_names.iterrows():
            self.sug_tree.insert("", 'end', iid=index,
                                 values=(row['first_name'], row['last_name'], row['bioname'], row['district_code'],
                                         row['bioguide_id'],
                                         row['similarity']))

    def clear_treeview(self):

        self.sug_tree.selection_remove(self.sug_tree.focus())
        for i in self.sug_tree.get_children():
            self.sug_tree.delete(i)

    def item_selected(self, event):
        item_no = self.sug_tree.selection()
        values = self.sug_tree.item(item_no)['values']

        if len(values) > 3:
            self.controller.update_names(values)

        # self.label_frame.update_names(values)


class LabelFrame(ttk.LabelFrame):

    def __init__(self, container, controller: Controller):
        super().__init__(container)
        # controaller saved
        self.original_val = None
        self.controller = controller
        # initializing widgets
        self['text'] = 'Editor'
        self.pack(padx=10, pady=10)

        # create labels and Boxes
        self.il = Label(self, text="ID")
        self.il.grid(row=1, column=0, padx=2, pady=2)
        self.id_box = Entry(self)
        self.id_box.grid(row=2, column=0, padx=2, pady=2)

        self.yl = Label(self, text="year")
        self.yl.grid(row=1, column=1, padx=2, pady=2)
        self.year_box = Entry(self)
        self.year_box.grid(row=2, column=1, padx=2, pady=2)

        self.cl = Label(self, text="congress")
        self.cl.grid(row=1, column=2, padx=2, pady=2)
        self.congress_box = Entry(self)
        self.congress_box.grid(row=2, column=2, padx=2, pady=2)

        self.sl = Label(self, text="state_po")
        self.sl.grid(row=1, column=3, padx=2, pady=2)
        self.state_box = Entry(self)
        self.state_box.grid(row=2, column=3, padx=2, pady=2)

        self.ol = Label(self, text="office")
        self.ol.grid(row=1, column=4, padx=2, pady=2)
        self.office_box = Entry(self)
        self.office_box.grid(row=2, column=4, padx=2, pady=2)

        self.fl = Label(self, text="first_name")
        self.fl.grid(row=1, column=5, padx=2, pady=2)
        self.first_name_box = Entry(self)
        self.first_name_box.grid(row=2, column=5, padx=2, pady=2)

        self.ll = Label(self, text="last_name")
        self.ll.grid(row=1, column=6, padx=2, pady=2)
        self.last_name_box = Entry(self)
        self.last_name_box.grid(row=2, column=6, padx=2, pady=2)

        # self.ll = Label(self, text="nickname")
        # self.ll.grid(row=1, column=6, padx=2, pady=2)
        # self.last_name_box = Entry(self)
        # self.last_name_box.grid(row=2, column=6, padx=2, pady=2)
        #
        # self.ll = Label(self, text="suffix ")
        # self.ll.grid(row=1, column=6, padx=2, pady=2)
        # self.last_name_box = Entry(self)
        # self.last_name_box.grid(row=2, column=6, padx=2, pady=2)

        self.ful = Label(self, text="full_name")
        self.ful.grid(row=1, column=7, padx=2, pady=2)
        self.full_name_box = Entry(self)
        self.full_name_box.grid(row=2, column=7, padx=2, pady=2)

        self.biol = Label(self, text="bioguide_id")
        self.biol.grid(row=1, column=8, padx=2, pady=2)
        self.bioguide_id_box = Entry(self)
        self.bioguide_id_box.grid(row=2, column=8, padx=2, pady=2)

        self.upload_bt = ttk.Button(self, text='upload', command=self.upload_values)
        # self.upload_bt.place(anchor= 'center')
        self.upload_bt.grid(row=3, column=2, pady=2, padx=2)

        self.refresh_bt = ttk.Button(self, text='refresh', command=self.refresh)
        self.refresh_bt.grid(row=3, column=3, padx=2, pady=2)

        self.clear_history_bt = ttk.Button(self, text='clear all history', command=self.clear_history)
        self.clear_history_bt.grid(row=3, column=4, padx=2, pady=2)

        self.reflect_bt = ttk.Button(self, text='reflect history', command=self.reflect_history)
        self.reflect_bt.grid(row=3, column=5, padx=2, pady=2)

        self.delete_history_bt = ttk.Button(self, text='delete current db history', command=self.delete_history)
        self.delete_history_bt.grid(row = 3, column = 6, padx=2, pady=2)

        # self.autosave_l = Label(self, text="Upload_history_autosave")
        # self.autosave_l.grid(row=2, column=5, pady=2, padx=2)
        # self.autosave_on_img = PhotoImage(file="./icon/on.png")
        # self.autosave_off_img = PhotoImage(file="./icon/off.png")
        # self.autosave_bt = ttk.Button(self,
        #                               image=self.autosave_on_img if self.controller.is_on_autosave else self.autosave_off_img,
        #                               command=self.switch)
        # self.autosave_bt.grid(row=3, column=5, padx= 2, pady= 2)

        self.chk_autosave = tk.IntVar()

        self.save_cbt = Checkbutton(self, text='save_history', variable=self.chk_autosave, onvalue=1, offvalue=0,
                                    command=self.autosave_history)
        self.save_cbt.grid(row=0, column=0, padx=2, pady=2)

        # self.chk_reflect = tk.IntVar()
        # self.reflect_cbt = Checkbutton(self, text='reflect_history', variable=self.chk_reflect, onvalue=1, offvalue=0,
        #                                command=self.auto_reflect_history)
        # self.reflect_cbt.grid(row = 0, column= 1, pady=2, padx=2 )

    def delete_history(self):
        self.controller.delete_history()
        self.controller.refresh_all()

    def reflect_history(self):
        self.controller.reflect_history()
        self.controller.refresh_all()

        # if self.chk_reflect.get() == 1:
        #     self.controller.is_on_reflect = True
        # else:
        #     self.controller.is_on_reflect = False

    def clear_history(self):
        self.controller.clear_history()

    def refresh(self):
        self.controller.refresh_all()

    #     need to add nickname and suffix here.

    def upload_values(self):
        values_dict = {'id': self.id_box.get(), 'office': self.office_box.get(),
                       'first_name': self.first_name_box.get(),
                       'last_name': self.last_name_box.get(), 'full_name': self.full_name_box.get(),
                       'bio_id': self.bioguide_id_box.get(), 'original_name': self.original_val[7]}
        # if self.controller.is_on_autosave:

        self.controller.upload_values(values_dict)
        self.controller.refresh_all()

    def update_entries(self, values):

        self.original_val = values

        self.id_box.delete(0, tk.END)
        self.year_box.delete(0, tk.END)
        self.congress_box.delete(0, tk.END)
        self.state_box.delete(0, tk.END)
        self.office_box.delete(0, tk.END)
        self.first_name_box.delete(0, tk.END)
        self.last_name_box.delete(0, tk.END)
        self.full_name_box.delete(0, tk.END)
        self.bioguide_id_box.delete(0, tk.END)

        if values:
            if values[0] != 'None':
                self.id_box.insert(0, values[0])
            if values[1] != 'None':
                self.year_box.insert(0, values[1])
            if values[2] != 'None':
                self.congress_box.insert(0, values[2])
            if values[3] != 'None':
                self.state_box.insert(0, values[3])
            if values[4] != 'None':
                self.office_box.insert(0, values[4])
            if values[6] != 'None':
                self.first_name_box.insert(0, values[6])
            if values[7] != 'None':
                self.last_name_box.insert(0, values[7])
            if values[8] != 'None':
                self.full_name_box.insert(0, values[8])
            # TODO: need to check if this works of not.
            if 'bioguide_id' in values and len(values) >= 8 and values[9] != 'None':
                self.bioguide_id_box.insert(0, values[9])

    def update_names(self, values):

        self.first_name_box.delete(0, tk.END)
        self.last_name_box.delete(0, tk.END)
        self.full_name_box.delete(0, tk.END)
        self.bioguide_id_box.delete(0, tk.END)

        if values:
            if values[0] != 'None':
                self.first_name_box.insert(0, values[0])
            if values[1] != 'None':
                self.last_name_box.insert(0, values[1])
            if values[2] != 'None':
                self.full_name_box.insert(0, values[2])
            if values[4] != 'None':
                self.bioguide_id_box.insert(0, values[4])

    def clear_all(self):
        self.id_box.delete(0, tk.END)
        self.year_box.delete(0, tk.END)
        self.congress_box.delete(0, tk.END)
        self.state_box.delete(0, tk.END)
        self.office_box.delete(0, tk.END)
        self.first_name_box.delete(0, tk.END)
        self.last_name_box.delete(0, tk.END)
        self.full_name_box.delete(0, tk.END)
        self.bioguide_id_box.delete(0, tk.END)

    def autosave_history(self):
        if self.chk_autosave.get() == 1:
            self.controller.is_on_autosave = True
            self.controller.check_or_create_autosave_table()
            # self.controller.is_on_autosave = False
        else:
            self.controller.is_on_autosave = False
            # self.controller.is_on_autosave = True

    def switch(self):

        if self.controller.is_on_autosave:
            self.autosave_bt.config(image=self.autosave_off_img)
            self.controller.is_on_autosave = False
        else:
            self.autosave_bt.config(image=self.autosave_on_img)
            self.controller.is_on_autosave = True


class DBFrame(ttk.LabelFrame):

    def __init__(self, container, controller: Controller):
        super().__init__(container)

        # self['text'] = 'Database'
        self.controller = controller
        self.pack(padx=40, pady=40)

        self.correct_db_name = controller.correct_db_name
        self.error_db_name = controller.error_db_name
        self.db_path = controller.db_path

        self.cdb = Label(self, text="correct_db_name")
        self.cdb.grid(row=0, column=0, padx=4, pady=4)
        self.cdb_box = Entry(self)
        self.cdb_box.grid(row=1, column=0, padx=4, pady=4)
        self.cdb_box.insert(0, self.correct_db_name)

        self.edb = Label(self, text="error_db_name")
        self.edb.grid(row=0, column=1, padx=4, pady=4)
        self.edb_box = Entry(self)
        self.edb_box.grid(row=1, column=1, padx=4, pady=4)
        self.edb_box.insert(0, self.error_db_name)

        self.db_path_label = Label(self, text='db location')
        self.db_path_label.grid(row=0, column=2, padx=4, pady=4)
        self.btn_add_dbfile = Button(self, text='choose file', command=self.add_file)
        self.btn_add_dbfile.grid(row=1, column=2, padx=4, pady=4)

        self.btn_apply = Button(self, text='apply', command=self.apply, width=20)
        self.btn_apply.grid(row=3, column=1, padx=10, pady=10)
        # self.btn_apply.place(relx = 0.5, rely=1, anchor=CENTER)

    def apply(self):
        self.error_db_name = self.edb_box.get()
        self.correct_db_name = self.cdb_box.get()
        self.controller.update_db(self.correct_db_name, self.error_db_name, self.db_path)

    def add_file(self):
        file = filedialog.askopenfilename(title='choose file', filetypes=(("db file", "*.db"), ("all files", "*.*")),
                                          initialdir="C:/")
        self.db_path = file

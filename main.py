import tkinter as tk
import os
from util import *
from datetime import datetime
from secparser import Parser

# written with help from chatGPT...
class App:
    def __init__(self, root):
        # Create the text box
        self.ticker = tk.Entry(root)
        self.date1 = tk.Entry(root)
        self.date2 = tk.Entry(root)
        
        # Create the labels
        self.text_label = tk.Label(root, text="Ticker:")
        self.date1_label = tk.Label(root, text="Start date (mm-dd-yyyy):")
        self.date2_label = tk.Label(root, text="End date (mm-dd-yyyy):")

        self.tQ_status = tk.IntVar()
        self.tQ_box = tk.Checkbutton(root, text="10-Q", variable=self.tQ_status)

        self.tK_status = tk.IntVar()
        self.tK_box = tk.Checkbutton(root, text="10-K", variable=self.tK_status)

        self.fetch_all_status = tk.IntVar()
        self.fetch_all_box = tk.Checkbutton(root, text="Fetch all tables (first run)", variable=self.fetch_all_status)
        
        # Place the labels and text boxes in a grid
        self.text_label.grid(row=0, column=0)
        self.ticker.grid(row=0, column=1)
        self.tQ_box.grid(row=0, column=2)
        self.tK_box.grid(row=0, column=3)
        self.date1_label.grid(row=1, column=0)
        self.date1.grid(row=1, column=1)
        self.date2_label.grid(row=2, column=0)
        self.date2.grid(row=2, column=1)
        self.fetch_all_box.grid(row=3, column=0)
        
        # Create the submit button
        self.submit = tk.Button(root, text="Submit", command=self.on_submit)
        self.submit.grid(row=3, column=1)

    def process_data(self, ticker, tQ, tK, start_date, end_date, fetch_all):
        self.parser = Parser(ticker, [tQ, tK], start_date, end_date)
        if fetch_all:
            exit_status = self.parser.get_all_filings()
            if exit_status:
                return exit_status
        table_links = self.parser.get_table_links()
        
        parsed_statements = self.parser.parse_income_statements(table_links)
        return parsed_statements

    def submit_statement(self, statement):
        print(statement)
        self.parser.draw_sankey_diagram(statement)
    
    def on_submit(self):
        # Get the user-entered data
        ticker_str = self.ticker.get()
        if not ticker_str:
            self.no_ticker_label = tk.Label(root, text="No ticker entered!")
            self.no_ticker_label.grid(row=4, column=1)
            return
        date1_str = self.date1.get()
        date2_str = self.date2.get()

        tQ = self.tQ_status.get()
        tK = self.tK_status.get()

        if not tQ and not tK:
            self.no_filing_label = tk.Label(root, text="No filing checked!")
            self.no_filing_label.grid(row=4, column=1)
            return
        
        date1 = None
        date2 = None
        if date1_str:
            date1 = datetime.strptime(date1_str, "%m-%d-%Y")
        else:
            date1 = datetime.strptime("01-01-1960", "%m-%d-%Y")
        if date2_str:
            date2 = datetime.strptime(date2_str, "%m-%d-%Y")
        else:
            date2 = datetime.now()
        
        # Perform some processing on the data
        result = self.process_data(ticker_str, tQ, tK, date1, date2, self.fetch_all_status.get())
        self.result_label = tk.Label(root, text="Parsed the following statements:")
        self.result_label.grid(row=4, column=1)

        for idx, res in enumerate(result):
            self.btn = tk.Button(root, text=res, command=lambda res=res: self.submit_statement(res))
            self.btn.grid(row=5, column=idx)


root_dir = os.getcwd()
if not os.path.exists(root_dir + "company_tickers_swp.json"):
    generate_swapped_tickers()

root = tk.Tk()
root.title("SEC Filing Parser")
app = App(root)
root.mainloop()

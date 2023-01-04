import tkinter as tk
import os
from util import *
from datetime import datetime
from secparser import Parser

def process_data(ticker, tQ, tK, start_date, end_date):
    parser = Parser(ticker, [tQ, tK], start_date, end_date)
    return_str = parser.get_all_filings()
    if return_str:
        return return_str
    return_str = parser.get_table_links()
    if return_str:
        return return_str
    return_str = parser.parse_income_statements()
    if return_str:
        return return_str
    return "Success"

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
        
        # Place the labels and text boxes in a grid
        self.text_label.grid(row=0, column=0)
        self.ticker.grid(row=0, column=1)
        self.tQ_box.grid(row=0, column=2)
        self.tK_box.grid(row=0, column=3)
        self.date1_label.grid(row=1, column=0)
        self.date1.grid(row=1, column=1)
        self.date2_label.grid(row=2, column=0)
        self.date2.grid(row=2, column=1)
        
        # Create the submit button
        self.submit = tk.Button(root, text="Submit", command=self.on_submit)
        self.submit.grid(row=3, column=0, columnspan=2)
    
    def on_submit(self):
        # Get the user-entered data
        ticker_str = self.ticker.get()
        date1_str = self.date1.get()
        date2_str = self.date2.get()

        print(self.tQ_status.get())
        print(self.tK_status.get())
        
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
        result = process_data(ticker_str, self.tQ_status.get(), self.tK_status.get(), date1, date2)
        
        # Create a new label to display the result
        self.result_label = tk.Label(root, text=result)
        self.result_label.grid(row=4, column=0)

root_dir = os.getcwd()
if not os.path.exists(root_dir + "company_tickers_swp.json"):
    generate_swapped_tickers()

root = tk.Tk()
root.title("SEC Filing Parser")
app = App(root)
root.mainloop()

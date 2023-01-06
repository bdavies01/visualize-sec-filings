import requests
import json
import csv

data_headers = {
    "User-Agent": "kskxkkee aidixks@bisjxjsks.com",
    "Accept-Encoding": "gzip, deflate",
    "Host": "www.sec.gov"
}

def generate_swapped_tickers():
	resp = requests.get("https://www.sec.gov/files/company_tickers.json")
	company_tickers = resp.json()

	ct_swapped = {}
	for v in company_tickers.values():
		ticker = v["ticker"]
		del v["ticker"]
		ct_swapped[ticker] = v

	with open("company_tickers_swp.json", "w") as outfile:
		json.dump(ct_swapped, outfile)


def get_cik_from_ticker(ticker):
	with open("company_tickers_swp.json") as infile:
		tickers = json.load(infile)
		cik = tickers[ticker]["cik_str"]
		cik_10d = f"{cik:010d}"
		return cik_10d

# read a given two column csv file and return the "keys", which 
# are the first item in the row, and the "value", which is the
# second item in the row
def read_two_col_csv_file(path_to_file):
	keys = []
	values = []
	index_tracker = 0

	with open(path_to_file, "r") as fp:
		reader = csv.reader(fp)
		for row in reader:
			if len(row) != 0:
				if index_tracker != 0:
					keys.append(row[0])
					values.append(float(row[1]))
				index_tracker += 1
	return [keys, values]
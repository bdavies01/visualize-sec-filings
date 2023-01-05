import requests
import time
import re
import os
import csv
import plotly.graph_objects as go
from bs4 import BeautifulSoup
from datetime import datetime

from util import *

                # MSFT      #TSLA       #AMZN    #KO(coca cola)     #BAC    #AXP(AmEx)
# company_CIKs = ["789019", "1318605", "1018724", "21344", "70858"]    #4962
# company_tickers = ["MSFT", "TSLA", "AMZN", "KO", "BAC"]
# filing_types = ["10-Q", "10-K"] # 10-Q, 10-K, or 8-K

income_statement_str_match = [r".*(statement(s*)_of_((income)|(operation(s*))))(_unaudited)*$", r".*(income_(statement(s*)))(_unaudited)*$"]
cogs_str_match = [r".*(cost)", r".*(expense)"]

# parser for one specific company
class Parser:
    def __init__(self, ticker, filing_types, start_date, end_date):
        self.root_dir = os.getcwd()

        # user entered inputs
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        self.filing_types = [] # this is a list, [10-Q, 10-K]
        if filing_types[0]:
            self.filing_types.append("10-Q")
        if filing_types[1]:
            self.filing_types.append("10-K")

        self.company_dir = self.root_dir + "/" + ticker

    '''
    query SEC for all filings we can find with EDGAR going as far back as possible.
    at this point we are not filtering based on date, as the function says we are
    getting ALL filings. we then store the filings in the "all_filings.csv" file
    '''
    def get_all_filings(self):
        try:
            Company_CIK_Number = get_cik_from_ticker(self.ticker)
            if not os.path.exists(self.company_dir):
                os.mkdir(self.company_dir)
            file_path = self.company_dir + "/" + "all_filings.csv"
            csvOutput = open(file_path, "w")
            csvWriter = csv.writer(csvOutput, quoting = csv.QUOTE_NONNUMERIC)

            csvWriter.writerow(["Company_Name", "Company_CIK_Number", "Account_Number",
                                "Filing_Type", "Filing_Number", "Filing_Date", "Document_Link",
                                "Interactive_Data_Link", "Filing_Number_Link", "Summary_Link_Xml"])

            for Filing_Type in self.filing_types:
                # define our parameters dictionary
                filing_parameters = {'action':'getcompany',
                                'CIK':Company_CIK_Number,
                                'type':Filing_Type,
                                'dateb':'',
                                'owner':'exclude',
                                'start':'',
                                'output':'',
                                'count':'100'}

                # request the url, and then parse the response.
                response = requests.get(url = r"https://www.sec.gov/cgi-bin/browse-edgar",
                                        params = filing_parameters, headers=data_headers)
                # Add 0.1 second time delay to comply with SEC.gov's 10 requests per second limit.
                time.sleep(0.1)
                soup = BeautifulSoup(response.content, 'html.parser')
                # Find the document table that contains filing information.
                main_table = soup.find_all('table', class_='tableFile2')
                # The base URL will be used to construct document links URLs.
                sec_base_url = r"https://www.sec.gov"
                Company_Name_path=str(soup.find('span',{'class':'companyName'}))
                if Company_Name_path != None:
                    try:
                        Company_Name = re.search('<span class="companyName">(.*)<acronym title',
                                                    Company_Name_path).group(1)
                    except AttributeError:
                        print("Could not find company name, \
                                assigning NULL value to company name.")
                        Company_Name = None
                # loop through each row of table and extract filing numbers, links, etc.
                for row in main_table[0].find_all('tr'):
                    # find all the rows under the 'td' element.
                    cols = row.find_all('td')
                    # If no information was detected, move on to the next row.
                    if len(cols) != 0:
                        # Get the text from the table.
                        if cols[0].text.strip() != Filing_Type:
                            print("Nonstandard form detected:", cols[0].text.strip())
                            continue
                        Filing_Type = cols[0].text.strip()
                        Filing_Date = cols[3].text.strip()
                        Filing_Number = cols[4].text.strip()
                        Filing_Number = ''.join(e for e in Filing_Number if e.isalnum())


                        # Get the URL path to the filing number.
                        filing_number_path = cols[4].find('a')
                        if filing_number_path != None:
                            Filing_Number_Link = sec_base_url + filing_number_path['href']
                        else:
                            break

                        # Get the URL path to the document.
                        document_link_path = cols[1].find('a',
                                                            {'href':True, 'id':'documentsbutton'})
                        if document_link_path != None:
                            Document_Link = sec_base_url + document_link_path['href']
                        else:
                            Document_Link = None

                        # Get the account number.
                        try:
                            Account_Number= cols[2].text.strip()
                            Account_Number = re.search('Acc-no:(.*)(34 Act)',
                                                        Account_Number).group(1)
                            Account_Number = ''.join(e for e in Account_Number if e.isalnum())

                        except Exception as e:
                            # no account number means no interactive document
                            # no interactive document means no filing summary
                            # no filing summary means we cant get individual tables
                            # the filing dies here, assign None and move on...
                            Account_Number = None

                        # Get the URL path to the interactive document.
                        interactive_data_path = cols[1].find('a',
                                                                {'href':True, 'id':'interactiveDataBtn'})
                        if interactive_data_path != None:
                            Interactive_Data_Link = sec_base_url + interactive_data_path['href']
                            # If the interactive data link exists, then so does the FilingSummary.xml link.
                            Summary_Link_Xml = Document_Link.replace(f"/{Account_Number}",'')\
                                                            .replace('-','')\
                                                            .replace('index.htm' ,'/FilingSummary.xml')

                        else:
                            # break
                            Interactive_Data_Link = None
                            Summary_Link_Xml = None

                        csvWriter.writerow([Company_Name, Company_CIK_Number, Account_Number,
                                            Filing_Type, Filing_Number, Filing_Date, Document_Link,
                                            Interactive_Data_Link, Filing_Number_Link, Summary_Link_Xml])

        except Exception as e:
            ret_str = f"Could not retrieve the table containing the necessary information.\
                    \nAbording the program.\nIf index list is out of range, make sure \
                    that you entered the correct CIK number(s).\n{e}"
            print(ret_str)
            return ret_str
        csvOutput.close()
    '''

    '''
    def get_links(self, report_name, summary_link_xml):
        response_2 = requests.get(summary_link_xml, headers=data_headers).content
        time.sleep(0.1)
        soup_2 = BeautifulSoup(response_2, 'lxml')

        filing_dir = self.company_dir + "/" + report_name
        if not os.path.exists(filing_dir):
            os.mkdir(filing_dir)

        table_path = filing_dir + "/filing_table_links.csv"

        csvOutput = open(table_path, "w")
        csvWriter = csv.writer(csvOutput, quoting = csv.QUOTE_NONNUMERIC)
        csvWriter.writerow(["Short_Name", "Report_Url"])

        for item in soup_2.find_all('report')[:-1]:
            if item.shortname:
                Short_Name = item.shortname.text
                # Remove special characters
                Short_Name = re.sub(r"[^a-zA-Z0-9]+", ' ', Short_Name)
                # Remove white wite space at the end of the string.
                Short_Name = Short_Name.rstrip()
            else:
                print('Short name could not be retrieved.')
                Short_Name  = None
            # Some tables come only in the xml form.
            if item.htmlfilename:
                Report_Url = summary_link_xml.replace('FilingSummary.xml',
                                                    item.htmlfilename.text)
            elif item.xmlfilename:
                Report_Url = summary_link_xml.replace('FilingSummary.xml',
                                                    item.xmlfilename.text)
            else:
                print('URL to the individual report could not be retrieved.')
                Report_Url = None


            # print(Short_Name)
            # print(Report_Url)
            csvWriter.writerow([Short_Name, Report_Url])
            # print('*'*50 + ' Inserting values into the table .... ' + '*'*50)

        csvOutput.close()

    '''
    having scraped all of the filings from the SEC, for each filing now extract
    the individual web links to the tables within each filing. this is where
    we apply the date filter
    '''
    def get_table_links(self):
        file_path = self.company_dir + "/" + "all_filings.csv"
        report_name = ""
        #date is index 5
        try:
            with open(file_path, "r") as fp:
                reader = csv.reader(fp)
                for row in reader:
                    if len(row) > 0:
                        if row[5] == "Filing_Date":
                            continue
                        date_obj = datetime.strptime(row[5], "%Y-%m-%d")
                        # only process filings that are within date range
                        if self.start_date <= date_obj < self.end_date:
                            summary_link_xml = row[-1]
                            report_name = row[5] + "_" + row[3]
                            self.get_links(report_name, summary_link_xml)
        except Exception as e:
            ret_str = f"Failed to extract table links for file: {report_name}\n{e}"
            print(ret_str)
            return ret_str


    # For each company, look at each form (10-K, 10-Q) we have collected,
    # and extract the relevant data points from it.
    #
    def parse_income_statements(self):
        collected_urls = []

        try:

            folders = [f for f in os.listdir(self.company_dir) if os.path.isdir(os.path.join(self.company_dir, f))]

            for folder in folders:
                filing_folder = self.company_dir + "/" + folder
                file_path = filing_folder + "/filing_table_links.csv"
                match = None

                with open(file_path, "r") as fp:
                    reader = csv.reader(fp)
                    for row in reader:
                        if len(row) > 0:
                            row_fmt = row[0].lower().replace(" ", "_")
                            for match_str in income_statement_str_match:
                                match = re.search(match_str, row_fmt)
                                if match:
                                    collected_urls.append([filing_folder, row[1]])
                                    break
                            if match:
                                break

            for folder_path, url in collected_urls:
                resp = requests.get(url, headers=data_headers)
                time.sleep(0.1)
                print(f"folder path: {folder_path}, url: {url}")
                soup = BeautifulSoup(resp.content, "lxml")
                main_table = soup.find_all("table")
                total_revenue = []
                cost_of_goods_sold = []
                done_opex = False
                gross_profit = []
                opex_categories = {}
                opex_totals = []
                op_inc = []
                tax = []
                get_tax = False
                net_income = []

                for idx, row in enumerate(main_table[0].find_all("tr")):
                    row_title = row.find_all("td", {"class":"pl"})
                    numerical_cols = row.find_all("td", {"class":["nump", "num"]})
                    match = None
                    # we only want the numbers, title doesn't matter if it isn't
                    # attached to anything
                    if len(numerical_cols) != 0: 
                        row_title_str = (row_title[0].text.strip().lower().replace(" ", "_")
                                                                        .replace("(", "")
                                                                        .replace(")","")
                                                                        .replace(",", ""))
                        extracted_text = [numerical_cols[n].text.replace("$","")
                                                                .replace(",","")
                                                                .replace("(","")
                                                                .replace(")","")
                                                                .strip() for n in range(len(numerical_cols))]
                        # the year 2015 has a span with text containing "us-gaap" which messes up casting to a float
                        # so we need to filter for it
                        numbers = []
                        for n in range(len(extracted_text)):
                            if "us-gaap" in extracted_text[n]:
                                split_text = extracted_text[n].split("us-gaap")
                                numbers.append(float(split_text[0]))
                            else:
                                numbers.append(float(extracted_text[n]))

                        for idx, col in enumerate(numerical_cols):
                            if "(" in col.text.strip():
                                numbers[idx] *= -1
                        if not total_revenue:
                            total_revenue = numbers.copy()

                        if not cost_of_goods_sold:
                            # check if no COGS
                            if "operating" in row_title_str: #there is no cogs and we are skipping it
                                cost_of_goods_sold = [0] * len(numerical_cols)
                                gross_profit = total_revenue.copy()
                            for match_str in cogs_str_match:
                                match = re.search(match_str, row_title_str)
                                if match:
                                    for n in range(len(numerical_cols)):
                                        cost_of_goods_sold.append(numbers[n])
                                        gross_profit.append(total_revenue[n] - cost_of_goods_sold[n])

                                    break

                        if not opex_totals:
                            for n in range(len(numerical_cols)):
                                opex_totals.append(0)
                                op_inc.append(0)

                        if match:
                            continue
                        
                        # got gross profit, now we do opex
                        if gross_profit and not done_opex:
                            first_num = numbers[0]
                            if first_num == gross_profit[0]: #company explicitly included gross profit, we know next line is opex
                                continue
                            else:
                                if first_num == opex_totals[0] or first_num == op_inc[0] or first_num == opex_totals[0] + cost_of_goods_sold[0]: # OR MATCH "total operating"
                                    done_opex = True
                                    continue
                                else:
                                    # now doing opex
                                    if not opex_categories.get(row_title_str, 0):
                                        opex_categories[row_title[0].text.strip()] = []
                                    for n in range(len(numerical_cols)):
                                        opex_categories[row_title[0].text.strip()].append(numbers[n])
                                        opex_totals[n] += numbers[n]
                                        op_inc[n] = gross_profit[n] - opex_totals[n]

                        if not tax:
                            if get_tax:
                                tax = numbers.copy()
                                continue
                                
                            match = re.search(r".*(before).*(tax)", row_title_str) #get the number after 'before tax'
                            if match:
                                get_tax = True   

                        if not net_income:
                            match = re.search(r"(.*(net)_((income)|(earning(s*)))(_loss)*$)|((net_)*profit(s*)(_loss)*$)", row_title_str) #i can make this regex look nicer
                            if match:
                                net_income = numbers.copy()

                print("Revenue:", total_revenue)
                print("COGS:", cost_of_goods_sold)
                print("Gross profit:", gross_profit)
                print("OpEx:", opex_categories)
                print("OpInc:", op_inc)
                print("Tax:", tax)
                print("Net income:", net_income, "\n")

                csvOutput = open(folder_path + "/income_stmt_summary.csv", "w")
                csvWriter = csv.writer(csvOutput, quoting = csv.QUOTE_NONNUMERIC)
                csvWriter.writerow(["Revenue"] + list(map(str, total_revenue)))
                csvWriter.writerow(["COGS"] + list(map(str, cost_of_goods_sold)))
                csvWriter.writerow(["Gross profit"] + list(map(str, gross_profit)))
                for key in opex_categories.keys():
                    csvWriter.writerow([key] + list(map(str, opex_categories[key])))
                csvWriter.writerow(["OpInc"] + list(map(str, op_inc)))
                csvWriter.writerow(["Tax"] + list(map(str, tax)))
                csvWriter.writerow(["Net income"] + list(map(str, net_income)))
                # transpose it later
                csvOutput.close()
        except Exception as e:
            ret_str = f"Failed to parse income statements\n{e}"
            print(ret_str)
            return ret_str

    def get_segment_link(self, filing_str):
        files = [f for f in os.listdir(self.company_dir) if os.path.isfile(os.path.join(self.company_dir, f))]

        filing_dir = self.company_dir + "/" + filing_str

        with open(filing_dir + "/filing_table_links.csv", "r") as fp:
            reader = csv.reader(fp)
            for row in reader:
                row_fmt = row[0].lower().replace(" ", "_")
                if "segment" in row_fmt:
                    return row[1]


    # filing_str: string for the name of the filing ex: "2022-04-29_10-Q"
    # only generates for most recent quarter
    # only generates for most recent quarter
    def draw_sankey_diagram(self, filing):
        company_dir = self.root_dir + "/" + self.ticker
        filing_dir = company_dir + "/" + filing

        labels = []
        colors = []

        sources = []
        targets = []
        values = []
        x = []
        y = []

        revenue = -1

        index_tracker = 0
        num_segments = 0

        # have user input the segment values, format is too varied to parse...
        segment_link = self.get_segment_link(self.ticker, filing)
        segment_path = filing_dir + "/" + "segment_information.csv"
        if os.path.exists(segment_path):
            # read it
            print("Already added segment info. Reading from " + segment_path)
            out = read_two_col_csv_file(segment_path)
            print(out[0])
            print(out[1])
            for n in range(len(out[0])):
                num_segments += 1
                labels.append(out[0][n])
                sources.append(n)
                values.append(out[1][n])
            for n in range(len(sources)):
                targets.append(len(sources))
                colors.append("orange")
                x.append(0)
                y.append((n+1)/len(sources))
        else:
            if segment_link:
                print(segment_link)
                last_input = input("Enter segments (y/n)?")
                fp = open(filing_dir + "/" + "segment_information.csv", "w")
                writer = csv.writer(fp, quoting = csv.QUOTE_NONNUMERIC)
                writer.writerow(["Segment Label", "Amount"])
                while last_input != "n" and sum(values) != revenue: #sum values not equal to revenue
                    curr_row = []
                    last_input = input("Enter segment label: ")
                    curr_row.append(last_input)
                    labels.append(last_input)
                    last_input = input("Enter segment value: ")
                    curr_row.append(float(last_input))
                    values.append(float(last_input))
                    sources.append(index_tracker)
                    num_segments += 1
                    last_input = input("Enter more segments (y/n)?")
                    index_tracker += 1
                    writer.writerow(curr_row)
                fp.close()
                for _ in range(len(sources)):
                    targets.append(len(sources))
                    colors.append("orange")
                    x.append(0)
                    y.append((n+1)/len(sources))
            else:
                print("Couldn't find segment table")
        
        last_idx = len(sources) # cache how many segments we added
        index_tracker = 0
        # labels.append("Revenue")
        # colors.append("green")

        category_tracker = 0

        csv_dict = {}
        csv_items = 0

        with open(filing_dir + "/" + "income_stmt_summary.csv", "r") as fp:
            reader = csv.reader(fp)
            for row in reader:
                csv_items += 1
                csv_dict[row[0]] = float(row[1])

        print(csv_dict)
        csv_keywords = ["Revenue", "COGS", "Gross profit", "OpInc", "Tax", "Net income"]
        insertion_idx = 0
        total_opex = 0
        opinc = 0
        opex_ctr = 0

        for idx, k in enumerate(csv_dict.keys()):
            if k == "OpInc":
                opinc = csv_dict[k]
                continue
            if k == "Revenue":
                labels.append("Revenue")
                colors.append("green")
                x.append(0.3)
                y.append(0.48)
                continue
            if k == "Tax":
                x.append(0.9)
                y.append(0.35)
                category_tracker += 1
            if k == "COGS":
                x.append(0.5)
                y.append(min(0.5 + csv_dict[k]/csv_dict["Revenue"], 0.75))
            if k == "Gross profit":
                x.append(0.5)
                # y.append(0.3)
                y.append(max(0.5 - csv_dict[k]/csv_dict["Revenue"], 0.15))
            if k == "Net income":
                x.append(0.9)
                print('x')
                y.append(0.1)
            if k not in csv_keywords:
                opex_ctr += 1
                if "Operating Expenses" not in labels:
                    insertion_idx = idx + num_segments - 1
                    labels.append("Operating Expenses")
                    labels.append("Operating Income")
                    colors.append("red")
                    colors.append("green")
                    x.append(0.68)
                    y.append(0.55)
                    x.append(0.68)
                    y.append(0.15)

                    category_tracker += 2
                    sources.append(last_idx + category_tracker)
                    sources.append(last_idx + category_tracker)
                    category_tracker += 1
                x.append(0.9)
                y.append(0.45 + (opex_ctr * 0.15))
                total_opex += csv_dict[k]

            labels.append(k)
            values.append(csv_dict[k])
            sources.append(last_idx + category_tracker)
            if k == "Net income" or k == "Gross profit":
                colors.append("green")
            else:
                colors.append("red")

        values.insert(insertion_idx, total_opex)
        values.insert(insertion_idx+1, opinc)


        for n in range(last_idx+1, len(labels)):
            targets.append(n)


        # print("labels:", labels)
        # print("values:", values)
        # print("sources:", sources)
        # print("targets:", targets)
        # print("colors:", colors)
        print("x:", x)
        print("y:", y)

        sk_node = dict(
            pad = 15,
            thickness = 20,
            line = dict(color = "black", width = 0.5),

            label = labels,
            color = colors,
            x = x,
            # y = y,
        )

        sk_link = dict(
            source = sources, # indices correspond to labels, eg A1, A2, A1, B1, ...
            target = targets,
            value = values,
        )

        fig = go.Figure(data=[go.Sankey(
            node = sk_node,
            link = sk_link)])

        fig.update_layout(title_text=self.ticker, font_size=20, autosize=True)
        fig.show()


# get_all_filings()
# get_table_links()
# parse_income_statements("TSLA")
# get_segment_link("MSFT", "2022-04-26_10-Q")
# draw_sankey_diagram("TSLA", "2022-04-25_10-Q")
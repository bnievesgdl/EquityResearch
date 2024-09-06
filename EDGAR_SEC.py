"""
SEC EDGAR Financial Data Extractor

This module provides functionality to extract financial data from SEC EDGAR 10-K filings
for a given stock ticker. It retrieves the latest 10-K filing, extracts key financial
information from income statements, cash flow statements, and balance sheets, and saves
the data to CSV files.

Usage:
    python EDGAR_SEC.py [ticker]

The script will process the ticker specified in DEFAULT_TICKER by default. Provide a different ticker as a
command-line argument to process a different company.
"""

import requests
import pandas as pd
import json
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from config import SEC_API_HEADERS, DEFAULT_TICKER

headers = SEC_API_HEADERS

def get_cik(ticker):
    """
    Retrieve the CIK (Central Index Key) for a given stock ticker.

    Args:
        ticker (str): The stock ticker symbol.

    Returns:
        int or None: The CIK as an integer, or None if not found.

    Raises:
        requests.RequestException: If there's an error fetching the data from SEC.
    """
    url = "https://www.sec.gov/include/ticker.txt"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    for line in response.text.splitlines():
        t, c = line.split('\t')
        if t.lower() == ticker.lower():
            return int(c)
    return None

def get_latest_10k_url(ticker):
    """
    Get the latest 10-K filing data for a given stock ticker using the SEC's JSON API.

    Args:
        ticker (str): The stock ticker symbol.

    Returns:
        str or None: The accession number of the latest 10-K filing, or None if not found.

    Raises:
        requests.RequestException: If there's an error fetching the data from SEC.
        json.JSONDecodeError: If there's an error parsing the JSON response.
    """
    cik = get_cik(ticker)
    if not cik:
        return None
    
    cik_padded = str(cik).zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = json.loads(response.text)
        
        allForms = pd.DataFrame.from_dict(data['filings']['recent'])
        form10k = allForms[allForms['form'] == '10-K']
        
        if not form10k.empty:
            latest_10k = form10k.iloc[0]
            filing_date = latest_10k['filingDate']
            accession_number = latest_10k['accessionNumber']
            logger.info(f"Latest 10-K filing date: {filing_date}")
            logger.info(f"Accession number: {accession_number}")
        else:
            logger.error("No 10-K filings found.")
            return None

        companyFacts_url = f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json'
        companyFacts = requests.get(companyFacts_url, headers=headers)
        companyFacts.raise_for_status()
        
        facts_data = companyFacts.json().get('facts', {})
        
        income_statement = process_income_statement(facts_data, filing_date, accession_number)
        cash_flow_statement = process_cash_flow_statement(facts_data, filing_date, accession_number)
        balance_sheet = process_balance_sheet(facts_data, filing_date, accession_number)
        
        income_statement.to_csv(f"{ticker}_income_statement.csv")
        cash_flow_statement.to_csv(f"{ticker}_cash_flow_statement.csv")
        balance_sheet.to_csv(f"{ticker}_balance_sheet.csv")
        
        logger.info(f"Financial statements saved as CSV files for {ticker}")
        
        return accession_number
    except requests.RequestException as e:
        logger.error(f"Error fetching data for {ticker}: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON data for {ticker}: {e}")
        return None

def get_value_for_accession(item_data, accession_number):
    """
    Extract the value for the specific accession number from the item data.

    Args:
        item_data (dict): The data for a specific financial item.
        accession_number (str): The accession number to look for.

    Returns:
        float or None: The value for the given accession number, or None if not found.
    """
    if 'units' in item_data and 'USD' in item_data['units']:
        for entry in item_data['units']['USD']:
            if entry['accn'] == accession_number:
                return entry['val']
    return None

def process_financial_statement(facts_data, items, filing_date, accession_number):
    """
    Process financial statement data for a given set of items.

    Args:
        facts_data (dict): The complete facts data from SEC.
        items (dict): A dictionary mapping item labels to their GAAP codes.
        filing_date (str): The filing date of the 10-K.
        accession_number (str): The accession number of the 10-K.

    Returns:
        pandas.DataFrame: A DataFrame containing the processed financial data.
    """
    data = {}
    for label, item_key in items.items():
        taxonomy, concept = item_key.split(':')
        if taxonomy in facts_data and concept in facts_data[taxonomy]:
            value = get_value_for_accession(facts_data[taxonomy][concept], accession_number)
            if value is not None:
                data[label] = [value]
            else:
                logger.info(f"No value found for {label} with accession number {accession_number}")
        else:
            logger.info(f"Item {label} not found in the data")
    
    return pd.DataFrame(data)

def process_income_statement(facts_data, filing_date, accession_number):
    """
    Process income statement data from the facts data.

    Args:
        facts_data (dict): The complete facts data from SEC.
        filing_date (str): The filing date of the 10-K.
        accession_number (str): The accession number of the 10-K.

    Returns:
        pandas.DataFrame: A DataFrame containing the processed income statement data.
    """
    income_items = {
        'Revenue': 'us-gaap:Revenues',
        'Cost of Revenue': 'us-gaap:CostOfRevenue',
        'Gross Profit': 'us-gaap:GrossProfit',
        'Operating Expenses': 'us-gaap:OperatingExpenses',
        'Operating Income': 'us-gaap:OperatingIncomeLoss',
        'Net Income': 'us-gaap:NetIncomeLoss',
    }
    return process_financial_statement(facts_data, income_items, filing_date, accession_number)

def process_cash_flow_statement(facts_data, filing_date, accession_number):
    """
    Process cash flow statement data from the facts data.

    Args:
        facts_data (dict): The complete facts data from SEC.
        filing_date (str): The filing date of the 10-K.
        accession_number (str): The accession number of the 10-K.

    Returns:
        pandas.DataFrame: A DataFrame containing the processed cash flow statement data.
    """
    cash_flow_items = {
        'Cash from Operating Activities': 'us-gaap:NetCashProvidedByUsedInOperatingActivities',
        'Cash from Investing Activities': 'us-gaap:NetCashProvidedByUsedInInvestingActivities',
        'Cash from Financing Activities': 'us-gaap:NetCashProvidedByUsedInFinancingActivities',
        'Net Change in Cash': 'us-gaap:NetIncreaseDecreaseInCash',
    }
    return process_financial_statement(facts_data, cash_flow_items, filing_date, accession_number)

def process_balance_sheet(facts_data, filing_date, accession_number):
    """
    Process balance sheet data from the facts data.

    Args:
        facts_data (dict): The complete facts data from SEC.
        filing_date (str): The filing date of the 10-K.
        accession_number (str): The accession number of the 10-K.

    Returns:
        pandas.DataFrame: A DataFrame containing the processed balance sheet data.
    """
    balance_sheet_items = {
        'Total Assets': 'us-gaap:Assets',
        'Total Liabilities': 'us-gaap:Liabilities',
        'Total Equity': 'us-gaap:StockholdersEquity',
        'Cash and Cash Equivalents': 'us-gaap:CashAndCashEquivalentsAtCarryingValue',
        'Total Current Assets': 'us-gaap:AssetsCurrent',
        'Total Current Liabilities': 'us-gaap:LiabilitiesCurrent',
    }
    return process_financial_statement(facts_data, balance_sheet_items, filing_date, accession_number)

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TICKER
    latest_10k_accession = get_latest_10k_url(ticker)
    if latest_10k_accession:
        logger.info(f"Latest 10-K accession number for {ticker}: {latest_10k_accession}")
    else:
        logger.error(f"Failed to process latest 10-K for {ticker}")


# SEC EDGAR Financial Data Extractor

## Overview

This project provides a Python-based tool for extracting financial data from SEC EDGAR 10-K filings for given stock tickers. It retrieves the latest 10-K filing, extracts key financial information from income statements, cash flow statements, and balance sheets, and saves the data to CSV files.

## Features

- Retrieves the latest 10-K filing for a given stock ticker
- Extracts key financial data from:
  - Income Statements
  - Cash Flow Statements
  - Balance Sheets
- Saves extracted data to CSV files
- Includes unit tests for reliability

## Requirements

- Python 3.7+
- pandas
- requests

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/EquityResearch.git
   cd EquityResearch
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

To use the SEC EDGAR Financial Data Extractor:

1. Ensure you have set up your SEC API headers in `config.py`:
   ```python
   SEC_API_HEADERS = {
       "User-Agent": "Your Name (your@email.com)"
   }
   DEFAULT_TICKER = "AAPL"  # Change this to your preferred default ticker
   ```

2. Run the script with a stock ticker:
   ```
   python EDGAR_SEC.py AAPL
   ```
   Replace `AAPL` with the ticker of your choice.

3. The script will generate three CSV files in the current directory:
   - `{ticker}_income_statement.csv`
   - `{ticker}_cash_flow_statement.csv`
   - `{ticker}_balance_sheet.csv`

## Running Tests

To run the unit tests:

1. Ensure you're in the `EquityResearch` directory.
2. Run the following command:
   ```
   python -m unittest tests.test_EDGAR_SEC
   ```

## Project Structure
EquityResearch/
├── EDGAR_SEC.py
├── config.py
├── requirements.txt
├── README.md
└── tests/
└── test_EDGAR_SEC.py


## Contributing

Contributions to this project are welcome. Please fork the repository and submit a pull request with your changes.

## Disclaimer

This tool is for educational and research purposes only. Always verify the extracted data against the official SEC filings. The authors are not responsible for any investment decisions made based on this data.
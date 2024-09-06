import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from EDGAR_SEC import (
    get_cik, get_latest_10k_url, get_value_for_accession,
    process_financial_statement, process_income_statement,
    process_cash_flow_statement, process_balance_sheet
)

class TestEDGARSEC(unittest.TestCase):

    @patch('EDGAR_SEC.requests.get')
    def test_get_cik(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "aapl\t0000320193\nmsft\t0000789019"
        mock_get.return_value = mock_response

        self.assertEqual(get_cik('AAPL'), 320193)
        self.assertEqual(get_cik('MSFT'), 789019)
        self.assertIsNone(get_cik('INVALID'))

    @patch('EDGAR_SEC.get_cik')
    @patch('EDGAR_SEC.requests.get')
    def test_get_latest_10k_url(self, mock_get, mock_get_cik):
        mock_get_cik.return_value = 320193
        mock_response = MagicMock()
        mock_response.text = '{"filings": {"recent": [{"form": "10-K", "filingDate": "2023-01-01", "accessionNumber": "0000320193-23-000001"}]}}'
        mock_get.return_value = mock_response

        result = get_latest_10k_url('AAPL')
        self.assertEqual(result, "0000320193-23-000001")

    def test_get_value_for_accession(self):
        item_data = {
            'units': {
                'USD': [
                    {'accn': '0000320193-23-000001', 'val': 1000},
                    {'accn': '0000320193-22-000001', 'val': 900}
                ]
            }
        }
        self.assertEqual(get_value_for_accession(item_data, '0000320193-23-000001'), 1000)
        self.assertIsNone(get_value_for_accession(item_data, 'INVALID'))

    def test_process_financial_statement(self):
        facts_data = {
            'us-gaap': {
                'Revenue': {'units': {'USD': [{'accn': '0000320193-23-000001', 'val': 1000}]}},
                'NetIncome': {'units': {'USD': [{'accn': '0000320193-23-000001', 'val': 200}]}}
            }
        }
        items = {'Revenue': 'us-gaap:Revenue', 'Net Income': 'us-gaap:NetIncome'}
        result = process_financial_statement(facts_data, items, '2023-01-01', '0000320193-23-000001')
        
        expected = pd.DataFrame({'Revenue': [1000], 'Net Income': [200]})
        pd.testing.assert_frame_equal(result, expected)

    # ... existing code ...

    def test_process_income_statement(self):
        facts_data = {
            'us-gaap': {
                'Revenues': {'units': {'USD': [{'accn': '0000320193-23-000001', 'val': 1000}]}},
                'NetIncomeLoss': {'units': {'USD': [{'accn': '0000320193-23-000001', 'val': 200}]}}
            }
        }
        result = process_income_statement(facts_data, '2023-01-01', '0000320193-23-000001')
        
        expected = pd.DataFrame({'Revenue': [1000], 'Net Income': [200]})
        pd.testing.assert_frame_equal(result, expected)

    def test_process_cash_flow_statement(self):
        facts_data = {
            'us-gaap': {
                'NetCashProvidedByUsedInOperatingActivities': {'units': {'USD': [{'accn': '0000320193-23-000001', 'val': 500}]}},
                'NetIncreaseDecreaseInCash': {'units': {'USD': [{'accn': '0000320193-23-000001', 'val': 100}]}}
            }
        }
        result = process_cash_flow_statement(facts_data, '2023-01-01', '0000320193-23-000001')
        
        expected = pd.DataFrame({'Cash from Operating Activities': [500], 'Net Change in Cash': [100]})
        pd.testing.assert_frame_equal(result, expected)

    def test_process_balance_sheet(self):
        facts_data = {
            'us-gaap': {
                'Assets': {'units': {'USD': [{'accn': '0000320193-23-000001', 'val': 2000}]}},
                'Liabilities': {'units': {'USD': [{'accn': '0000320193-23-000001', 'val': 1000}]}}
            }
        }
        result = process_balance_sheet(facts_data, '2023-01-01', '0000320193-23-000001')
        
        expected = pd.DataFrame({'Total Assets': [2000], 'Total Liabilities': [1000]})
        pd.testing.assert_frame_equal(result, expected)

if __name__ == '__main__':
    unittest.main()

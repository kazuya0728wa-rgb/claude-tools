import sys
import config
from spreadsheet_client import SpreadsheetClient

def clear():
    print("Clearing test data for rows 2 to 11...")
    client = SpreadsheetClient()
    # BC列とBD列をクリア
    try:
        client.sheet.update(range_name='BC2:BD11', values=[['', ''] for _ in range(10)])
        print("Cleared successfully.")
    except Exception as e:
        print(f"Failed to clear: {e}")

if __name__ == "__main__":
    clear()

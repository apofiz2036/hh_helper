import os
from pathlib import Path
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

load_dotenv()

# Google API
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
]

CREDS = Credentials.from_service_account_file(
    "service_account.json", 
    scopes=SCOPES,
)

SPREADSHEET_URL= "https://docs.google.com/spreadsheets/d/1OYDM-k9xUs7CSykw58ZUdOJEzNSqqXvJPpqHqwxOU5A"

COLUMN_1 = 0 #TODO

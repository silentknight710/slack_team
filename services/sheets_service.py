from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pickle
from typing import List
from models.schemas import TeamMember
from datetime import datetime

class GoogleSheetsService:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    
    def __init__(self):
        self.creds = None
        self.spreadsheet_id = os.getenv('GOOGLE_SHEETS_ID')
        self.range_name = 'Team!A2:F'  # Adjust based on your sheet structure
        
    def _get_credentials(self):
        """Get or refresh Google API credentials"""
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH'),
                    self.SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)

    async def _get_sheet_values(self):
        """Fetch values from the Google Sheet asynchronously."""
        self._get_credentials()
        service = build('sheets', 'v4', credentials=self.creds)
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=self.spreadsheet_id, range=self.range_name).execute()
        values = result.get('values', [])
        return values

    async def get_team_data(self) -> List[TeamMember]:
        values = await self._get_sheet_values()
        team_members = []
        for row in values:
            try:
                # Make sure row is subscriptable (i.e., it's a list/tuple)
                if not isinstance(row, (list, tuple)):
                    print(f"Skipping invalid row: {row}")
                    continue
                    
                # Convert tasks string to list
                tasks = [task.strip() for task in row[3].split(',')]
                
                # Convert deadlines string to list of datetime objects
                deadlines = [
                    datetime.strptime(date.strip(), '%Y-%m-%d')
                    for date in row[4].split(',')
                ]
                
                member = TeamMember(
                    name=row[0],
                    email=row[1],
                    role=row[2],
                    tasks=tasks,
                    deadlines=deadlines,
                    progress=float(row[5])
                )
                team_members.append(member)
            except IndexError:
                print(f"Row missing required columns: {row}")
            except ValueError as e:
                print(f"Invalid data format in row: {row} - {str(e)}")
        
        return team_members

 

def _is_date_column(self, column_name: str) -> bool:
    """Check if column name is a date in YYYY-MM-DD format"""
    import re
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'
    return bool(re.match(date_pattern, str(column_name)))

    
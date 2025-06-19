# Team Progress Management AI Slack Service

This application provides a Slack-integrated service for managing team progress, generating reports, and automating team communications.

## Features

- Slack bot integration for easy command access
- Automated team progress monitoring
- Email report generation
- Google Sheets integration for data management
- AI-powered email content generation using Gemini
- FastAPI backend for scalability

## Setup

1. **Environment Setup**:
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

2. **Environment Variables**:
Create a `.env` file with the following variables:
```env
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token

# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_PATH=path/to/credentials.json
GOOGLE_SHEETS_ID=your-spreadsheet-id

# Email Configuration
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-specific-password

# Gemini AI Configuration
GEMINI_API_KEY=your-gemini-api-key
```

3. **Slack App Setup**:
   - Create a new Slack App at https://api.slack.com/apps
   - Enable Socket Mode
   - Add the following bot scopes:
     - `app_mentions:read`
     - `chat:write`
     - `channels:read`
     - `groups:read`
   - Install the app to your workspace
   - Copy the Bot Token and App Token

4. **Google Sheets Setup**:
   - Create a project in Google Cloud Console
   - Enable Google Sheets API
   - Create credentials and download the JSON file
   - Share your Google Sheet with the service account email

## Running the Service

1. **Start the Service**:
```bash
python main.py
```

2. **Using the Slack Bot**:
   - Invite the bot to your channel
   - Mention the bot with commands:
     - `@bot status` - Check monitoring status
     - `@bot report` - Generate progress report
     - `@bot start` - Start monitoring
     - `@bot stop` - Stop monitoring

3. **API Endpoints**:
   - `POST /api/start-monitoring` - Start monitoring
   - `GET /api/status` - Check status
   - `POST /api/generate-report` - Generate report
   - `GET /api/formatted-emails` - Get formatted emails

## Deployment

### Local Deployment
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Production Deployment
For production deployment, consider using:
- Gunicorn as the WSGI server
- Nginx as a reverse proxy
- Supervisor for process management
- SSL/TLS for secure communication

Example Gunicorn command:
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## Project Structure
```
.
├── main.py                 # FastAPI application entry point
├── agents/                 # CrewAI agents
│   ├── spreadsheet_agent.py
│   ├── progress_agent.py
│   └── report_agent.py
├── services/              # Service modules
│   ├── sheets_service.py
│   ├── email_service.py
│   ├── slack_service.py
│   └── gemini_service.py
├── models/                # Data models
│   └── schemas.py
└── requirements.txt       # Dependencies
```

## Security Considerations

1. **Environment Variables**:
   - Never commit `.env` file
   - Use secure secret management in production

2. **API Security**:
   - Implement rate limiting
   - Use proper authentication
   - Enable CORS only for trusted domains

3. **Data Security**:
   - Encrypt sensitive data
   - Implement proper access controls
   - Regular security audits

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
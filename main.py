from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from crewai import Crew, Agent, Task
from services.sheets_service import GoogleSheetsService
from services.email_service import EmailService
from services.slack_service import SlackService
from models.schemas import TeamMember, ProgressReport
from agents.spreadsheet_agent import SpreadsheetAgent
from typing import List, Dict
import asyncio
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Team Progress Management AI")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Slack client directly
slack_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

# Initialize services
sheets_service = GoogleSheetsService()
email_service = EmailService()
slack_service = SlackService()
spreadsheet_agent = SpreadsheetAgent()

# Global state to track monitoring status
monitoring_active = False

# Slack Events API endpoint
@app.post("/slack/events")
async def slack_events(request: Request):
    """Handle Slack Events API requests including URL verification"""
    try:
        body = await request.json()
        
        # Handle URL verification challenge
        if body.get("type") == "url_verification":
            return {"challenge": body.get("challenge")}
        
        # Handle actual events
        if body.get("type") == "event_callback":
            event = body.get("event", {})
            
            # Handle app mentions
            if event.get("type") == "app_mention":
                await handle_app_mention(event)
            
            return {"status": "ok"}
        
        return {"status": "ok"}
        
    except Exception as e:
        print(f"Error handling Slack event: {str(e)}")
        return {"status": "error", "message": str(e)}

async def send_slack_message(channel: str, text: str):
    """Send a message to Slack using the Web API"""
    try:
        print(f"DEBUG: Attempting to send message to channel: {channel}")
        print(f"DEBUG: Message content: {text[:100]}...")
        
        response = slack_client.chat_postMessage(
            channel=channel,
            text=text
        )
        print(f"DEBUG: Message sent successfully: {response.get('ok')}")
        return response
    except SlackApiError as e:
        print(f"ERROR: Slack API Error: {e.response['error']}")
        print(f"ERROR: Full error response: {e.response}")
        # Try to send error message to channel if possible
        try:
            slack_client.chat_postMessage(
                channel=channel,
                text=f"❌ Bot error: {e.response['error']}"
            )
        except:
            pass
        raise e
    except Exception as e:
        print(f"ERROR: General error sending message: {str(e)}")
        raise e

async def generate_and_send_report(channel: str):
    """Generate and send a detailed progress report to Slack"""
    try:
        # Get team members from the sheets service
        team_members = await sheets_service.get_team_data()
        # Get formatted emails from the agent
        formatted_emails = await spreadsheet_agent.get_formatted_emails(team_members)
        
        if not formatted_emails:
            await send_slack_message(channel, "⚠️ No team members found in the spreadsheet. Please check your Google Sheets data.")
            return
            
        # Format report using Slack blocks
        report_blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 Team Progress Report"
                }
            },
            {"type": "divider"}
        ]
        
        for email, content in formatted_emails:
            report_blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{email}*\n{content}"
                }
            })
        
        # Add summary section
        report_blocks.append({"type": "divider"})
        report_blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"📈 *Total Team Members*: {len(formatted_emails)}"
            }
        })
        
        # Send formatted report to Slack
        slack_client.chat_postMessage(
            channel=channel,
            blocks=report_blocks
        )
        
    except Exception as e:
        await send_slack_message(channel, f"❌ Report error: {str(e)}")
        print(f"Error in generate_and_send_report: {str(e)}")

async def handle_app_mention(event):
    """Handle when the bot is mentioned in a channel"""
    global monitoring_active  # Needed to modify the global variable
    
    try:
        text = event.get("text", "").lower()
        channel = event.get("channel")
        
        if "report1" in text or "report" in text:
            # Show processing message
            
            await generate_and_send_report(channel)
            
        elif "status" in text:
            status = "active" if monitoring_active else "inactive"
            await send_slack_message(channel, f"🔄 Current monitoring status: **{status}**")
            
        elif "stop" in text:
            monitoring_active = False
            await send_slack_message(channel, "⏹️ Monitoring stopped successfully!")
            
        elif "start" in text:
            monitoring_active = True
            await send_slack_message(channel, "🚀 Monitoring started successfully!")
            await start_monitoring_internal()
            
        elif "team" in text or "members" in text:
            try:
                # Get team members directly from Google Sheets
                team_data = await sheets_service.get_team_data()
                member_list = "\n".join([f"• {member.email}" for member in team_data])
                await send_slack_message(channel, f"👥 **Team Members**:\n{member_list}")
            except Exception as e:
                await send_slack_message(channel, f"❌ Error fetching team members: {str(e)}")
                
        else:
            help_text = """🤖 **Available Commands:**
• `@bot status` - Check monitoring status
• `@bot report` - Get detailed team progress report  
• `@bot team` - List all team members
• `@bot start` - Start monitoring
• `@bot stop` - Stop monitoring
• `@bot help` - Show this help message"""
            await send_slack_message(channel, help_text)
            
    except Exception as e:
        print(f"Error in handle_app_mention: {str(e)}")
        try:
            await send_slack_message(channel, f"❌ Error processing your request: {str(e)}")
        except:
            pass

# FastAPI endpoints
@app.post("/api/start-monitoring")
async def start_monitoring():
    """Start the team progress monitoring process"""
    global monitoring_active
    if monitoring_active:
        raise HTTPException(status_code=400, detail="Monitoring is already active")
    
    try:
        await start_monitoring_internal()
        return {"message": "Monitoring started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting monitoring: {str(e)}")

async def start_monitoring_internal():
    """Internal function to start monitoring"""
    global monitoring_active
    monitoring_active = True
    
    try:
        # Create CrewAI agents
        progress_agent = Agent(
            role="Progress Checker",
            goal="Check team members' progress and send reminder emails",
            backstory="I am an AI agent responsible for monitoring team progress and ensuring timely updates."
        )
        
        report_agent = Agent(
            role="Report Generator", 
            goal="Generate comprehensive progress reports for managers",
            backstory="I am an AI agent specialized in analyzing team progress and creating detailed reports."
        )
        
        # Create tasks with expected_output
        progress_task = Task(
            description="Check team progress and send reminder emails",
            agent=progress_agent,
            expected_output="A summary of team members who need progress updates and confirmation that reminder emails were sent"
        )
        
        report_task = Task(
            description="Generate daily progress report",
            agent=report_agent,
            expected_output="A comprehensive daily progress report containing team member status, overall progress percentage, and recommendations"
        )
        
        # Create and run the crew
        crew = Crew(
            agents=[progress_agent, report_agent],
            tasks=[progress_task, report_task],
            verbose=True
        )
        
        # Start the monitoring process in the background
        asyncio.create_task(run_monitoring_cycle(crew))
        
    except Exception as e:
        monitoring_active = False  # Reset status on error
        raise e

@app.get("/api/status")
async def get_status():
    """Get the current monitoring status"""
    return {"status": "active" if monitoring_active else "inactive"}

@app.post("/api/generate-report")
async def generate_report():
    """Manually trigger report generation"""
    try:
        team_data = await sheets_service.get_team_data()
        report = await generate_progress_report(team_data)
        await email_service.send_report(report)
        return {"message": "Report generated and sent successfully"}
    except Exception as e:
        print(f"Error in generate_report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test-slack")
async def test_slack():
    try:
        response = slack_client.auth_test()
        
        # Extract only the safe, serializable data
        safe_response = {
            "ok": response.get("ok"),
            "url": response.get("url"),
            "team": response.get("team"),
            "user": response.get("user"),
            "team_id": response.get("team_id"),
            "user_id": response.get("user_id"),
            "bot_id": response.get("bot_id")
        }
        
        return {"status": "success", "bot_info": safe_response}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/formatted-emails")
async def get_formatted_emails():
    """Get formatted email content for all team members"""
    try:
        team_members = await sheets_service.get_team_data()
        formatted_emails = await spreadsheet_agent.get_formatted_emails(team_members)
        return {
            "status": "success", 
            "data": formatted_emails
        }
    except Exception as e:
        print(f"Error in get_formatted_emails: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_monitoring_cycle(crew: Crew):
    """Run the monitoring cycle periodically"""
    while monitoring_active:
        try:
            result = crew.kickoff()
            await asyncio.sleep(24 * 60 * 60)  # Wait 24 hours
        except Exception as e:
            print(f"Error in monitoring cycle: {str(e)}")
            await asyncio.sleep(60)

async def generate_progress_report(team_data: List[TeamMember]) -> ProgressReport:
    """Generate a progress report from team data"""
    if not team_data:
        raise ValueError("No team data available")
        
    overall_progress = sum(member.progress for member in team_data) / len(team_data)
    
    return ProgressReport(
        date=datetime.now(),
        team_members=team_data,
        overall_progress=overall_progress,
        summary=f"Team is {overall_progress:.1f}% complete with their tasks",
        blockers=[],
        recommendations=[]
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
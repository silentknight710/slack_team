from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os
from typing import List, Optional
from models.schemas import SlackMessage, ProgressReport

class SlackService:
    def __init__(self):
        self.client = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))
        self.default_channel = os.getenv('SLACK_DEFAULT_CHANNEL')
    
    async def send_notification(self, message: str, channel: Optional[str] = None):
        """Send a simple notification to a Slack channel"""
        try:
            response = self.client.chat_postMessage(
                channel=channel or self.default_channel,
                text=message
            )
            return response
        except SlackApiError as e:
            print(f"Error sending Slack message: {str(e)}")
            raise
    
    async def send_progress_report(self, report: ProgressReport):
        """Send a formatted progress report to Slack"""
        blocks = self._create_report_blocks(report)
        
        try:
            response = self.client.chat_postMessage(
                channel=self.default_channel,
                text=f"Daily Progress Report - {report.date.strftime('%Y-%m-%d')}",
                blocks=blocks
            )
            return response
        except SlackApiError as e:
            print(f"Error sending progress report to Slack: {str(e)}")
            raise
    
    def _create_report_blocks(self, report: ProgressReport) -> List[dict]:
        """Create formatted blocks for the progress report"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📊 Daily Progress Report - {report.date.strftime('%Y-%m-%d')}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Overall Progress:* {report.overall_progress}%"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary:*\n{report.summary}"
                }
            }
        ]
        
        # Add team member updates
        for member in report.team_members:
            blocks.extend([
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{member.name}* ({member.role})\n"
                               f"Progress: {member.progress}%\n"
                               f"Tasks: {', '.join(member.tasks)}"
                    }
                }
            ])
        
        # Add blockers
        if report.blockers:
            blocks.extend([
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*🚧 Blockers:*\n" + "\n".join([f"• {blocker}" for blocker in report.blockers])
                    }
                }
            ])
        
        # Add recommendations
        if report.recommendations:
            blocks.extend([
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*💡 Recommendations:*\n" + "\n".join([f"• {rec}" for rec in report.recommendations])
                    }
                }
            ])
        
        return blocks
    
    async def send_reminder(self, team_member_name: str, tasks: List[str]):
        """Send a reminder to a team member about their tasks"""
        message = f"Hey {team_member_name}! 👋\n\n"
        message += "Here's a friendly reminder about your tasks:\n"
        message += "\n".join([f"• {task}" for task in tasks])
        message += "\n\nPlease update your progress when you get a chance!"
        
        try:
            response = self.client.chat_postMessage(
                channel=self.default_channel,
                text=message
            )
            return response
        except SlackApiError as e:
            print(f"Error sending reminder to Slack: {str(e)}")
            raise 
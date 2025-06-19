from crewai import Agent
from services.sheets_service import GoogleSheetsService
from services.email_service import EmailService
from services.slack_service import SlackService
from models.schemas import TeamMember, ProgressReport
from datetime import datetime
from typing import List

class ProgressAgent:
    def __init__(self):
        self.sheets_service = GoogleSheetsService()
        self.email_service = EmailService()
        self.slack_service = SlackService()
    
    def create_agent(self) -> Agent:
        """Create the progress checking agent"""
        return Agent(
            role="Progress Checker",
            goal="Monitor team progress and ensure timely updates",
            backstory="""I am an AI agent specialized in monitoring team progress and ensuring 
            that all team members are on track with their tasks. I analyze task progress, 
            deadlines, and team member updates to maintain project momentum.""",
            verbose=True,
            allow_delegation=False,
            tools=[
                self.check_team_progress,
                self.send_progress_reminders,
                self.update_progress_data
            ]
        )
    
    async def check_team_progress(self, team_members: List[TeamMember]) -> List[TeamMember]:
        """Check the progress of all team members"""
        updated_members = []
        for member in team_members:
            # Check if any tasks are approaching deadline
            approaching_deadlines = [
                task for task, deadline in zip(member.tasks, member.deadlines)
                if (deadline - datetime.now()).days <= 2
            ]
            
            if approaching_deadlines:
                # Send reminder for approaching deadlines
                await self.slack_service.send_reminder(member.name, approaching_deadlines)
            
            # Send progress check email
            await self.email_service.send_progress_check(member)
            updated_members.append(member)
        
        return updated_members
    
    async def send_progress_reminders(self, team_members: List[TeamMember]):
        """Send reminders to team members who haven't updated their progress"""
        for member in team_members:
            if member.progress == 0.0:  # Assuming 0.0 means no progress update
                await self.slack_service.send_reminder(
                    member.name,
                    member.tasks
                )
    
    async def update_progress_data(self, team_members: List[TeamMember]) -> List[TeamMember]:
        """Update progress data based on team member responses"""
        # In a real implementation, this would parse email responses
        # and update the progress data accordingly
        return team_members
    
    async def generate_progress_summary(self, team_members: List[TeamMember]) -> ProgressReport:
        """Generate a summary of team progress"""
        overall_progress = sum(member.progress for member in team_members) / len(team_members)
        
        # Identify blockers
        blockers = []
        for member in team_members:
            if member.progress < 30 and any(
                (deadline - datetime.now()).days <= 2
                for deadline in member.deadlines
            ):
                blockers.append(f"{member.name} is behind on tasks with approaching deadlines")
        
        # Generate recommendations
        recommendations = []
        if overall_progress < 50:
            recommendations.append("Consider redistributing tasks to balance workload")
        if blockers:
            recommendations.append("Schedule one-on-one meetings with team members who are behind")
        
        return ProgressReport(
            date=datetime.now(),
            team_members=team_members,
            overall_progress=overall_progress,
            summary=f"Team is {overall_progress}% complete with their tasks",
            blockers=blockers,
            recommendations=recommendations
        ) 
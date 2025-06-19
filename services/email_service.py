import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from typing import List
from models.schemas import EmailTemplate, ProgressReport, TeamMember

class EmailService:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.username = os.getenv('EMAIL_USERNAME')
        self.password = os.getenv('EMAIL_PASSWORD')
    
    async def send_progress_check(self, team_member: TeamMember):
        """Send a progress check email to a team member"""
        template = self._create_progress_check_template(team_member)
        await self._send_email(template)
    
    async def send_report(self, report: ProgressReport):
        """Send the progress report to the manager"""
        template = self._create_report_template(report)
        await self._send_email(template)
    
    def _create_progress_check_template(self, team_member: TeamMember) -> EmailTemplate:
        """Create a progress check email template"""
        subject = f"Daily Progress Check - {team_member.name}"
        
        body = f"""
        Hello {team_member.name},
        
        This is a friendly reminder to update your progress on the following tasks:
        
        {self._format_tasks(team_member.tasks, team_member.deadlines)}
        
        Please provide an update on your progress by replying to this email.
        
        Best regards,
        Your AI Assistant
        """
        
        return EmailTemplate(
            subject=subject,
            body=body,
            recipient=team_member.email
        )
    
    def _create_report_template(self, report: ProgressReport) -> EmailTemplate:
        """Create a progress report email template"""
        subject = f"Daily Team Progress Report - {report.date.strftime('%Y-%m-%d')}"
        
        body = f"""
        Team Progress Report
        
        Overall Progress: {report.overall_progress}%
        
        Summary:
        {report.summary}
        
        Team Member Updates:
        {self._format_team_updates(report.team_members)}
        
        Blockers:
        {self._format_list(report.blockers)}
        
        Recommendations:
        {self._format_list(report.recommendations)}
        
        Best regards,
        Your AI Assistant
        """
        
        return EmailTemplate(
            subject=subject,
            body=body,
            recipient=os.getenv('MANAGER_EMAIL')
        )
    
    async def _send_email(self, template: EmailTemplate):
        """Send an email using the provided template"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = template.recipient
            msg['Subject'] = template.subject
            
            if template.cc:
                msg['Cc'] = ', '.join(template.cc)
            
            msg.attach(MIMEText(template.body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                recipients = [template.recipient] + (template.cc or [])
                server.send_message(msg, self.username, recipients)
                
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            raise
    
    def _format_tasks(self, tasks: List[str], deadlines: List[str]) -> str:
        """Format tasks and deadlines for email"""
        return '\n'.join([
            f"- {task} (Deadline: {deadline})"
            for task, deadline in zip(tasks, deadlines)
        ])
    
    def _format_team_updates(self, team_members: List[TeamMember]) -> str:
        """Format team member updates for email"""
        return '\n\n'.join([
            f"{member.name} ({member.role}):\n"
            f"Progress: {member.progress}%\n"
            f"Tasks: {', '.join(member.tasks)}"
            for member in team_members
        ])
    
    def _format_list(self, items: List[str]) -> str:
        """Format a list of items for email"""
        return '\n'.join([f"- {item}" for item in items]) 
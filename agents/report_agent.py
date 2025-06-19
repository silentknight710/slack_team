from crewai import Agent
from services.sheets_service import GoogleSheetsService
from services.email_service import EmailService
from services.slack_service import SlackService
from models.schemas import TeamMember, ProgressReport
from datetime import datetime
from typing import List

class ReportAgent:
    def __init__(self):
        self.sheets_service = GoogleSheetsService()
        self.email_service = EmailService()
        self.slack_service = SlackService()
    
    def create_agent(self) -> Agent:
        """Create the report generation agent"""
        return Agent(
            role="Report Generator",
            goal="Generate comprehensive progress reports for managers",
            backstory="""I am an AI agent specialized in analyzing team progress and creating 
            detailed reports. I identify patterns, blockers, and opportunities for improvement 
            to help managers make informed decisions.""",
            verbose=True,
            allow_delegation=False,
            tools=[
                self.analyze_team_progress,
                self.generate_report,
                self.distribute_report
            ]
        )
    
    async def analyze_team_progress(self, team_members: List[TeamMember]) -> dict:
        """Analyze team progress and identify key metrics"""
        analysis = {
            "overall_progress": 0.0,
            "role_progress": {},
            "blockers": [],
            "recommendations": []
        }
        
        # Calculate overall progress
        total_progress = sum(member.progress for member in team_members)
        analysis["overall_progress"] = total_progress / len(team_members)
        
        # Calculate progress by role
        role_progress = {}
        for member in team_members:
            if member.role not in role_progress:
                role_progress[member.role] = []
            role_progress[member.role].append(member.progress)
        
        for role, progress_list in role_progress.items():
            analysis["role_progress"][role] = sum(progress_list) / len(progress_list)
        
        # Identify blockers
        for member in team_members:
            if member.progress < 30 and any(
                (deadline - datetime.now()).days <= 2
                for deadline in member.deadlines
            ):
                analysis["blockers"].append(
                    f"{member.name} ({member.role}) is behind on tasks with approaching deadlines"
                )
        
        # Generate recommendations
        if analysis["overall_progress"] < 50:
            analysis["recommendations"].append(
                "Consider redistributing tasks to balance workload"
            )
        
        for role, progress in analysis["role_progress"].items():
            if progress < 40:
                analysis["recommendations"].append(
                    f"Provide additional support to {role} team members"
                )
        
        return analysis
    
    async def generate_report(self, analysis: dict, team_members: List[TeamMember]) -> ProgressReport:
        """Generate a comprehensive progress report"""
        # Create a detailed summary
        summary = f"""Team Progress Report for {datetime.now().strftime('%Y-%m-%d')}

Overall Progress: {analysis['overall_progress']:.1f}%

Progress by Role:
{self._format_role_progress(analysis['role_progress'])}

Key Findings:
{self._format_findings(analysis)}

Next Steps:
{self._format_recommendations(analysis['recommendations'])}
"""
        
        return ProgressReport(
            date=datetime.now(),
            team_members=team_members,
            overall_progress=analysis["overall_progress"],
            summary=summary,
            blockers=analysis["blockers"],
            recommendations=analysis["recommendations"]
        )
    
    async def distribute_report(self, report: ProgressReport):
        """Distribute the report to relevant stakeholders"""
        # Send report via email
        await self.email_service.send_report(report)
        
        # Send report to Slack
        await self.slack_service.send_progress_report(report)
    
    def _format_role_progress(self, role_progress: dict) -> str:
        """Format role progress for the report"""
        return "\n".join([
            f"- {role}: {progress:.1f}%"
            for role, progress in role_progress.items()
        ])
    
    def _format_findings(self, analysis: dict) -> str:
        """Format key findings for the report"""
        findings = []
        
        # Add overall progress finding
        if analysis["overall_progress"] < 50:
            findings.append("Team is behind schedule overall")
        elif analysis["overall_progress"] > 80:
            findings.append("Team is making excellent progress")
        
        # Add role-specific findings
        for role, progress in analysis["role_progress"].items():
            if progress < 40:
                findings.append(f"{role} team is struggling to meet deadlines")
            elif progress > 90:
                findings.append(f"{role} team is exceeding expectations")
        
        return "\n".join([f"- {finding}" for finding in findings])
    
    def _format_recommendations(self, recommendations: List[str]) -> str:
        """Format recommendations for the report"""
        return "\n".join([f"- {rec}" for rec in recommendations]) 
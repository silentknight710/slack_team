from crewai import Agent
from services.sheets_service import GoogleSheetsService
from models.schemas import TeamMember
from datetime import datetime
from services.gemini_service import GeminiService
from typing import List, Dict, Tuple, Any

class SpreadsheetAgent:
    def __init__(self):
        self.sheets_service = GoogleSheetsService()
        self.gemini_service = GeminiService()
    
    # ... existing methods ...

    async def get_formatted_emails(self, team_members: List[TeamMember]) -> List[Tuple[str, str]]:
        email_contents = []
        for member in team_members:
            try:
                # Ensure member is a TeamMember object with required attributes
                if not all(hasattr(member, attr) for attr in ['name', 'email', 'role', 'progress']):
                    print(f"Skipping invalid member: {member}")
                    continue
                    
                email_content = self.generate_personalized_email(member)
                email_contents.append((member.email, email_content))
            except Exception as e:
                print(f"Error processing member {getattr(member, 'email', 'unknown')}: {str(e)}")
        
        return email_contents


    def generate_personalized_email(self, member: TeamMember) -> str:
        """Generate a personalized email for a team member"""
        try:
            if not hasattr(self.gemini_service, 'llm'):
                print("WARNING: Gemini service not properly initialized")
                
                
            prompt = self._create_prompt(member)
            response = self.gemini_service.llm.invoke(prompt)
            return response.content
        except Exception as e:
            print(f"Error generating personalized email: {str(e)}")
            

    def _create_prompt(self, member: TeamMember) -> str:
        """Create a detailed prompt for Gemini based on member data."""
        # Calculate days until deadline
        days_until = "Unknown"
        try:
            if member.deadlines and len(member.deadlines) > 0:
                deadline_date = member.deadlines[0]  # Get the first deadline
                days_until = max(0, (deadline_date - datetime.now()).days)
        except:
            days_until = "Unknown"

        # Create the prompt
        return f"""As a project manager, write a personalized email to {member.name} regarding their work progress.
        
Current Status:
- Role: {member.role}
- Tasks: {', '.join(member.tasks)}
- Deadline: {', '.join(d.strftime('%Y-%m-%d') for d in member.deadlines)} ({days_until} days remaining)
- Current Progress: {member.progress}%

Please write a professional but friendly email that:
1. Acknowledges their current progress
2. Shows understanding of their role and tasks
3. Asks for specific updates on their progress
4. Offers support if needed
5. Maintains a motivating tone
6. References their deadline and progress appropriately

The email should be personalized based on their role, progress, and time until deadline.
"""
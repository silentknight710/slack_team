import google.generativeai as genai
from typing import Dict, Any
import os
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI

class GeminiService:
    def __init__(self, api_key: str = None):
        """Initialize Gemini service with API key."""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            verbose=True,
            temperature=0.5,
            google_api_key=self.api_key
        )

    def generate_email(self, member_data: Dict[str, Any]) -> str:
        """
        Generate a personalized email for a team member using their data and historical progress.
        
        Args:
            member_data: Current member's data from spreadsheet
            historical_data: Optional historical data for the member
        """
        # Prepare the prompt for Gemini
        prompt = self._create_prompt(member_data)
        
        # Generate response from Gemini
        response = self.llm.invoke(prompt)
        
        return response.content

    def _create_prompt(self, member_data: Dict[str, Any]) -> str:
        """Create a detailed prompt for Gemini based on member data."""
        # Handle deadlines as a list
        deadlines = member_data.get('deadlines', [])
        # Convert deadlines to string if they are datetime objects
        formatted_deadlines = []
        days_until_deadline = []
        current_date = datetime.now()
        for deadline in deadlines:
            if isinstance(deadline, datetime):
                formatted_deadlines.append(deadline.strftime('%Y-%m-%d'))
                days = (deadline - current_date).days
            else:
                formatted_deadlines.append(str(deadline))
                try:
                    deadline_date = datetime.strptime(str(deadline), '%Y-%m-%d')
                    days = (deadline_date - current_date).days
                except:
                    days = 'Unknown'
            days_until_deadline.append(f"{days} days")

        # Handle tasks as a list
        tasks = member_data.get('tasks', [])
        formatted_tasks = ', '.join(tasks) if isinstance(tasks, list) else str(tasks)

        # Create the prompt
        prompt = f"""As a project manager, write a personalized email to {member_data.get('email', 'the team member')} regarding their work progress.
        
Current Status:
- Role: {member_data.get('role', 'N/A')}
- Tasks: {formatted_tasks}
- Deadlines: {', '.join(formatted_deadlines)} ({', '.join(map(str, days_until_deadline))})
- Current Progress: {member_data.get('progress', 'N/A')}

Historical Context:
{self._format_historical_data(member_data) if member_data else 'No historical data available'}

Please write a professional but friendly email that:
1. Acknowledges their current progress
2. Shows understanding of their role and tasks
3. Asks for specific updates on their progress
4. Offers support if needed
5. Maintains a motivating tone
6. References their deadlines and progress appropriately

The email should be personalized based on their role, progress, and time until deadlines.
"""
        return prompt

    def _format_historical_data(self, member_data: Dict[str, Any]) -> str:
        """Format historical data for the prompt."""
        if not member_data:
            return "No historical data available"
        
        formatted_data = "Previous Progress:\n"
        for date, progress in member_data.items():
            formatted_data += f"- {date}: {progress}\n"
        return formatted_data 
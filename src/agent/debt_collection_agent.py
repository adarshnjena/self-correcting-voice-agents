import os
import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ScriptSection(BaseModel):
    """A section of the debt collection script."""
    section_id: str
    name: str
    description: str
    content: str
    next_sections: List[str]

class DebtCollectionScript(BaseModel):
    """The full debt collection script, organized in sections."""
    script_id: str
    version: str
    description: str
    sections: Dict[str, ScriptSection]
    
    def get_starting_section(self) -> Optional[ScriptSection]:
        """Get the introduction section of the script."""
        for section in self.sections.values():
            if section.section_id == "introduction":
                return section
        return next(iter(self.sections.values())) if self.sections else None
    
    def to_prompt(self) -> str:
        """Convert the script to a prompt for the agent to follow."""
        script_prompt = f"""
        You are a debt collection agent working to collect a past-due loan.
        Your job is to negotiate with the borrower to establish a repayment plan.
        
        SCRIPT GUIDELINES:
        {self.description}
        
        SCRIPT SECTIONS:
        """
        
        for section in self.sections.values():
            script_prompt += f"""
            --- {section.name} ---
            {section.content}
            """
        
        script_prompt += """
        IMPORTANT RULES:
        - Be respectful and professional at all times
        - Do not make threats or use aggressive language
        - Listen to the borrower's concerns
        - Try to find a mutually acceptable payment plan
        - Document any agreements made during the call
        - Follow legal compliance guidelines for debt collection
        """
        
        return script_prompt

def load_base_script() -> DebtCollectionScript:
    """
    Load the base debt collection script from the config file if it exists,
    otherwise return the default script.
    """
    script_path = os.path.join("config", "base_script.json")
    if os.path.exists(script_path):
        try:
            with open(script_path, "r") as file:
                script_data = json.load(file)
            return DebtCollectionScript(**script_data)
        except Exception as e:
            logger.error(f"Error loading script from {script_path}: {e}")
    
    # Return default script if file doesn't exist or there's an error
    return _create_default_script()

def save_script(script: DebtCollectionScript, filename: str) -> bool:
    """
    Save the script to a JSON file.
    
    Args:
        script: The script to save
        filename: The filename to save to (in the config directory)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        os.makedirs("config", exist_ok=True)
        file_path = os.path.join("config", filename)
        
        # Convert the script to a dictionary and then to JSON
        script_dict = script.model_dump()
        
        # Handle nested ScriptSection objects
        script_json = json.dumps(script_dict, indent=2)
        
        with open(file_path, "w") as file:
            file.write(script_json)
            
        logger.info(f"Script saved to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving script: {e}")
        return False

def _create_default_script() -> DebtCollectionScript:
    """Create the default debt collection script."""
    sections = {
        "introduction": ScriptSection(
            section_id="introduction",
            name="Introduction",
            description="Begin the call by identifying yourself and the company",
            content="""
            Hello, my name is [Agent Name] calling from [Company Name]. 
            Am I speaking with [Customer Name]? 
            
            I'm calling regarding your loan account ending in [Last 4 Digits], which is currently past due. 
            
            Before we continue, I need to inform you that this call may be recorded for quality assurance purposes.
            """,
            next_sections=["verification"]
        ),
        "verification": ScriptSection(
            section_id="verification",
            name="Identity Verification",
            description="Verify the customer's identity for security and compliance",
            content="""
            For security purposes, could you please confirm your date of birth and the last 4 digits of your SSN?
            
            Thank you for verifying your information.
            """,
            next_sections=["situation_assessment"]
        ),
        "situation_assessment": ScriptSection(
            section_id="situation_assessment",
            name="Situation Assessment",
            description="Understand why the customer has fallen behind on payments",
            content="""
            I see that your account is [X] months past due with a total outstanding balance of $[Amount].
            
            I understand that financial difficulties can happen to anyone. Could you help me understand what has prevented you from making your payments?
            
            [Listen carefully to the customer's explanation]
            """,
            next_sections=["payment_discussion", "hardship_options"]
        ),
        "payment_discussion": ScriptSection(
            section_id="payment_discussion",
            name="Payment Discussion",
            description="Discuss payment options and negotiate a repayment plan",
            content="""
            Thank you for explaining your situation. We have several options to help you get back on track.
            
            The full outstanding amount is $[Amount]. Would you be able to make a payment today?
            
            [If customer can make a payment]
            That's great. How much would you be able to pay today?
            
            [If customer cannot make a payment]
            I understand. Let's discuss a payment plan that might work better for your current situation.
            """,
            next_sections=["payment_plan", "hardship_options"]
        ),
        "payment_plan": ScriptSection(
            section_id="payment_plan",
            name="Payment Plan Setup",
            description="Establish a formal payment plan based on customer's ability to pay",
            content="""
            Based on what you've shared, I'd like to suggest a payment plan:
            
            Option 1: [Payment plan details]
            Option 2: [Alternative payment plan details]
            
            Which option would work better for you?
            
            [Discuss and adjust based on customer feedback]
            
            Once we have agreed on a plan, I'll send a confirmation email with all the details.
            """,
            next_sections=["confirmation"]
        ),
        "hardship_options": ScriptSection(
            section_id="hardship_options",
            name="Hardship Options",
            description="Present options for customers experiencing significant financial hardship",
            content="""
            I understand you're going through a difficult time. We have special hardship programs that might help in your situation:
            
            1. Temporary reduced payment plan
            2. Interest rate reduction
            3. Payment deferral for [X] months
            
            Would any of these options help your current situation?
            """,
            next_sections=["payment_plan", "escalation"]
        ),
        "escalation": ScriptSection(
            section_id="escalation",
            name="Escalation Process",
            description="Process for when standard options don't meet customer needs",
            content="""
            I understand our standard options may not work for your situation. I'd like to connect you with our financial hardship specialist who has additional tools to assist you.
            
            Would it be okay if I transfer you, or would you prefer they call you back at a more convenient time?
            """,
            next_sections=["confirmation"]
        ),
        "confirmation": ScriptSection(
            section_id="confirmation",
            name="Confirmation and Next Steps",
            description="Confirm the agreement and explain next steps",
            content="""
            Let me confirm what we've agreed to today:
            
            [Summarize the agreement]
            
            You'll receive a confirmation email within 24 hours with these details.
            
            Is there anything else I can help you with today?
            """,
            next_sections=["closing"]
        ),
        "closing": ScriptSection(
            section_id="closing",
            name="Closing",
            description="End the call professionally",
            content="""
            Thank you for your time today, [Customer Name]. We appreciate your commitment to resolving this matter.
            
            If you have any questions or need to make changes to your plan, please don't hesitate to call us at [Phone Number] or email us at [Email].
            
            Have a good day.
            """,
            next_sections=[]
        )
    }
    
    return DebtCollectionScript(
        script_id="base_debt_collection_script",
        version="1.0",
        description="""
        This script provides a framework for debt collection calls. The goal is to establish a 
        repayment plan while being respectful and understanding of the customer's situation.
        Adapt your approach based on the customer's responses and circumstances.
        """,
        sections=sections
    ) 
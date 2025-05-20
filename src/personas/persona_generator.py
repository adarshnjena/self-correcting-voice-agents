import os
import json
import logging
from typing import List, Dict, Any
from pydantic import BaseModel

import openai
from openai import OpenAI

logger = logging.getLogger(__name__)

class DebtorPersona(BaseModel):
    """Model representing a loan defaulter persona for testing."""
    id: str
    name: str
    age: int
    occupation: str
    income: float
    debt_amount: float
    months_behind: int
    reasons_for_default: List[str]
    communication_style: str
    negotiation_style: str
    objections: List[str]
    financial_situation: str
    willingness_to_pay: float  # 0.0-1.0 scale
    
    def to_prompt(self) -> str:
        """Converts persona to a prompt for customer simulation."""
        persona_description = f"""
        You are role-playing as {self.name}, a {self.age} year old {self.occupation} who is currently 
        {self.months_behind} months behind on a loan payment of ${self.debt_amount:.2f}.
        
        Your current financial situation: {self.financial_situation}
        
        Your reasons for defaulting on the loan include:
        {', '.join(self.reasons_for_default)}
        
        When communicating with debt collectors:
        - You have a {self.communication_style} communication style
        - Your negotiation approach is {self.negotiation_style}
        - Your willingness to pay is {int(self.willingness_to_pay * 100)}%
        
        Common objections you might raise:
        {', '.join(self.objections)}
        
        Respond as this character would to a debt collection call. Be authentic to this persona.
        """
        return persona_description

def generate_personas(count: int = 5) -> List[DebtorPersona]:
    """
    Generate a list of diverse loan defaulter personas for testing.
    
    Args:
        count: Number of personas to generate
        
    Returns:
        List of DebtorPersona objects
    """
    try:
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OpenAI API key is required but not provided")
        return generate_personas_with_api(count)
    except Exception as e:
        logger.error(f"Error generating personas: {e}")
        raise ValueError(f"Failed to generate personas: {str(e)}")

def generate_personas_with_api(count: int) -> List[DebtorPersona]:
    """Generate personas using OpenAI API."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    personas = []
    for i in range(count):
        try:
            prompt = f"""
            Create a realistic persona for a loan defaulter that a debt collection agency would call.
            
            The response MUST be a valid JSON object with EXACTLY these fields:
            - name: A person's full name (string)
            - age: Age in years (integer between 18-75)
            - occupation: Current job or profession (string)
            - income: Monthly income in dollars (float between 1000-10000)
            - debt_amount: Amount of debt in dollars (float between 1000-20000)
            - months_behind: Number of months behind on payment (integer between 1-12)
            - reasons_for_default: List of reasons for defaulting (array of 2-4 strings)
            - communication_style: How they communicate (string describing their style)
            - negotiation_style: Their approach to negotiation (string)
            - objections: Common objections they raise (array of 2-4 strings)
            - financial_situation: Brief description of their finances (string)
            - willingness_to_pay: Number between 0.0 and 1.0 (float)
            
            Be creative and realistic. Generate a fully formed character with a believable financial situation.
            Ensure diverse representation across different personas.
            """
            
            response = client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You generate diverse and realistic personas of people who have defaulted on loans. You MUST return valid JSON matching the requested format exactly."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9
            )
            
            # Extract and validate the response
            try:
                persona_data = json.loads(response.choices[0].message.content)
                
                # Check if all required fields are present
                required_fields = ["name", "age", "occupation", "income", "debt_amount", 
                                  "months_behind", "reasons_for_default", "communication_style", 
                                  "negotiation_style", "objections", "financial_situation", 
                                  "willingness_to_pay"]
                
                missing_fields = [field for field in required_fields if field not in persona_data]
                
                if missing_fields:
                    raise ValueError(f"Missing required fields in API response: {', '.join(missing_fields)}")
                
                # Ensure ID is unique
                persona_data["id"] = f"persona_{i+1}"
                personas.append(DebtorPersona(**persona_data))
                logger.info(f"Generated persona: {persona_data['name']}")
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in API response: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Error generating persona with API: {e}")
            raise
    
    return personas 
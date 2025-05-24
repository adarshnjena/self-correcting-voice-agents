"""
Conversation simulator for testing debt collection agent scripts with various customer personas.
"""

import os
import json
import logging
import datetime
from typing import List, Optional, Callable, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from openai import OpenAI

logger = logging.getLogger(__name__)

@dataclass
class Message:
    """Represents a single message in a conversation."""
    role: str  # "agent" or "customer" 
    content: str
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.datetime.now().isoformat()

@dataclass 
class Conversation:
    """Represents a complete conversation between agent and customer."""
    agent_script: Any  # DebtCollectionScript instance
    customer_persona: Any  # CustomerPersona instance
    messages: List[Message]
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.datetime.now().isoformat()
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation."""
        message = Message(role=role, content=content)
        self.messages.append(message)
        
    def finish(self):
        """Mark the conversation as finished."""
        self.end_time = datetime.datetime.now().isoformat()
    
    def save(self, directory: Optional[str] = None) -> str:
        """Save the conversation to a JSON file."""
        if directory is None:
            directory = "data/conversations"
        
        # Create directory if it doesn't exist
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{self.customer_persona.name.replace(' ', '_')}_{timestamp}.json"
        filepath = Path(directory) / filename
        
        # Convert to serializable format
        conversation_data = {
            "customer_persona": {
                "name": self.customer_persona.name,
                "age": self.customer_persona.age,
                "occupation": self.customer_persona.occupation,
                "debt_amount": self.customer_persona.debt_amount,
                "months_behind": self.customer_persona.months_behind,
                "reasons_for_default": self.customer_persona.reasons_for_default,
                "communication_style": self.customer_persona.communication_style,
                "willingness_to_pay": self.customer_persona.willingness_to_pay
            },
            "script_version": self.agent_script.version,
            "messages": [asdict(msg) for msg in self.messages],
            "start_time": self.start_time,
            "end_time": self.end_time
        }
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(conversation_data, f, indent=2)
        
        logger.info(f"Conversation saved to {filepath}")
        return str(filepath)

def simulate_conversation(
    agent_script: Any,
    customer_persona: Any, 
    max_turns: int = 10,
    message_callback: Optional[Callable[[str, str], None]] = None
) -> Conversation:
    """
    Simulate a conversation between the debt collection agent and a customer persona.
    
    Args:
        agent_script: The agent script to use
        customer_persona: The customer persona to simulate
        max_turns: Maximum number of conversation turns
        message_callback: Optional callback function called for each message (role, content)
        
    Returns:
        Conversation object containing the full interaction
    """
    # Initialize conversation
    conversation = Conversation(
        agent_script=agent_script,
        customer_persona=customer_persona,
        messages=[]
    )
    
    # Check if OpenAI API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not found. Cannot simulate conversation.")
        # Return a dummy conversation for testing
        conversation.add_message("agent", "Hello, this is a debt collection agent.")
        conversation.add_message("customer", "I can't pay right now.")
        conversation.finish()
        return conversation
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Get the starting section of the agent script
        starting_section = agent_script.get_starting_section()
        if starting_section:
            first_message = starting_section.content
            # Replace placeholders with persona data
            first_message = first_message.replace("[Agent Name]", "AI Agent")
            first_message = first_message.replace("[Customer Name]", customer_persona.name)
            first_message = first_message.replace("[Last 4 Digits]", "1234")
            first_message = first_message.replace("[Amount]", f"{customer_persona.debt_amount:.2f}")
            first_message = first_message.replace("[X]", str(customer_persona.months_behind))
        else:
            first_message = f"Hello {customer_persona.name}, this is regarding your past-due account of ${customer_persona.debt_amount:.2f}."
        
        # Add the first agent message
        conversation.add_message("agent", first_message)
        if message_callback:
            message_callback("agent", first_message)
        
        # Simulate the conversation turns
        for turn in range(max_turns):
            # Generate customer response
            customer_response = _generate_customer_response(
                client, customer_persona, conversation.messages
            )
            
            if customer_response:
                conversation.add_message("customer", customer_response)
                if message_callback:
                    message_callback("customer", customer_response)
                    
                # Check if conversation should end
                if _should_end_conversation(customer_response, turn, max_turns):
                    break
                
                # Generate agent response
                agent_response = _generate_agent_response(
                    client, agent_script, customer_persona, conversation.messages
                )
                
                if agent_response:
                    conversation.add_message("agent", agent_response)
                    if message_callback:
                        message_callback("agent", agent_response)
                        
                    # Check if conversation should end
                    if _should_end_conversation(agent_response, turn, max_turns):
                        break
            else:
                break
        
        conversation.finish()
        
    except Exception as e:
        logger.error(f"Error during conversation simulation: {str(e)}")
        # Add an error message to the conversation
        conversation.add_message("system", f"Simulation error: {str(e)}")
        conversation.finish()
    
    return conversation

def _generate_customer_response(
    client: OpenAI,
    customer_persona: Any,
    conversation_history: List[Message]
) -> str:
    """Generate a customer response based on their persona and conversation history."""
    
    # Build conversation context for the customer
    system_prompt = f"""You are roleplaying as a customer with debt who is being contacted by a debt collection agent.

Customer Profile:
- Name: {customer_persona.name}
- Age: {customer_persona.age}
- Occupation: {customer_persona.occupation}
- Debt Amount: ${customer_persona.debt_amount:.2f}
- Months Behind: {customer_persona.months_behind}
- Reasons for Default: {customer_persona.reasons_for_default}
- Communication Style: {customer_persona.communication_style}
- Willingness to Pay: {customer_persona.willingness_to_pay:.1%}

Stay in character as this customer. Respond naturally based on your financial situation, personality, and willingness to pay. Be realistic about your objections and concerns. Do not reveal internal details about your willingness to pay percentage - let this influence your responses naturally."""
    
    # Build message history
    messages = [{"role": "system", "content": system_prompt}]
    
    for msg in conversation_history:
        if msg.role == "agent":
            messages.append({"role": "user", "content": msg.content})
        else:  # customer message
            messages.append({"role": "assistant", "content": msg.content})
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.8,
            max_tokens=150
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        logger.error(f"Error generating customer response: {e}")
        return "I need some time to think about this."

def _generate_agent_response(
    client: OpenAI,
    agent_script: Any,
    customer_persona: Any,
    conversation_history: List[Message]
) -> str:
    """Generate an agent response following the script and responding to customer."""
    
    # Build system prompt for the agent
    system_prompt = f"""You are a professional debt collection agent following a script. Your goal is to collect payment while maintaining compliance and professionalism.

Agent Script: {agent_script.to_prompt()}

Customer Information (for context only - do not reveal directly):
- Debt Amount: ${customer_persona.debt_amount:.2f}
- Months Behind: {customer_persona.months_behind}

Follow your script sections appropriately based on the customer's responses. Be professional, empathetic, and focused on finding a resolution. Adapt your script to the conversation flow while staying compliant with debt collection regulations."""
    
    # Build message history from agent perspective
    messages = [{"role": "system", "content": system_prompt}]
    
    for msg in conversation_history:
        if msg.role == "agent":
            messages.append({"role": "assistant", "content": msg.content})
        else:  # customer message  
            messages.append({"role": "user", "content": msg.content})
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        logger.error(f"Error generating agent response: {e}")
        return "I understand your situation. Let me see what options we have available."

def _should_end_conversation(message: str, turn: int, max_turns: int) -> bool:
    """Determine if the conversation should end based on the message content."""
    
    # End conversation indicators
    end_phrases = [
        "goodbye", "bye", "talk later", "call back", "hang up",
        "not interested", "stop calling", "remove me", "don't call",
        "attorney", "lawyer", "legal", "harassment", 
        "agreed", "deal", "payment arrangement", "will pay"
    ]
    
    message_lower = message.lower()
    
    # Check for explicit end phrases
    if any(phrase in message_lower for phrase in end_phrases):
        return True
    
    # End if we've reached max turns
    if turn >= max_turns - 1:
        return True
    
    return False 
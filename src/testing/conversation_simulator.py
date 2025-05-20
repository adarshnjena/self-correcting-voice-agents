import os
import json
import logging
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

import openai
from openai import OpenAI

from src.personas.persona_generator import DebtorPersona
from src.agent.debt_collection_agent import DebtCollectionScript

logger = logging.getLogger(__name__)

class Message(BaseModel):
    """A message in a conversation."""
    role: str  # "agent" or "customer"
    content: str
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())

class Conversation(BaseModel):
    """A simulated conversation between an agent and a customer."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_script: DebtCollectionScript
    customer_persona: DebtorPersona
    messages: List[Message] = []
    metadata: Dict[str, Any] = {}
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation."""
        self.messages.append(Message(role=role, content=content))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the conversation to a dictionary for storage."""
        return {
            "id": self.id,
            "agent_script_id": self.agent_script.script_id,
            "agent_script_version": self.agent_script.version,
            "customer_persona_id": self.customer_persona.id,
            "messages": [m.dict() for m in self.messages],
            "metadata": self.metadata,
            "created_at": self.created_at
        }
    
    def save(self, directory: str = "data/conversations") -> str:
        """Save the conversation to a JSON file."""
        os.makedirs(directory, exist_ok=True)
        file_path = os.path.join(directory, f"{self.id}.json")
        with open(file_path, "w") as file:
            json.dump(self.to_dict(), file, indent=2)
        return file_path

def simulate_conversation(
    agent_script: DebtCollectionScript,
    customer_persona: DebtorPersona,
    max_turns: int = 15
) -> Conversation:
    """
    Simulate a conversation between a debt collection agent and a customer.
    
    Args:
        agent_script: The script for the debt collection agent
        customer_persona: The persona of the customer
        max_turns: Maximum number of turns in the conversation
        
    Returns:
        A Conversation object containing the simulated conversation
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OpenAI API key is required but not provided")
        
    conversation = Conversation(
        agent_script=agent_script,
        customer_persona=customer_persona,
        metadata={"max_turns": max_turns}
    )
    
    return simulate_conversation_with_api(conversation, max_turns)

def simulate_conversation_with_api(conversation: Conversation, max_turns: int) -> Conversation:
    """Simulate a conversation using OpenAI API."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    agent_prompt = conversation.agent_script.to_prompt()
    customer_prompt = conversation.customer_persona.to_prompt()
    
    # Initialize with agent greeting
    agent_name = "AI Agent"
    customer_name = conversation.customer_persona.name
    
    # Start the conversation with an agent message
    starting_section = conversation.agent_script.get_starting_section()
    first_message = starting_section.content if starting_section else "Hello, this is a debt collection agent calling about your past-due loan."
    first_message = first_message.replace("[Agent Name]", agent_name).replace("[Customer Name]", customer_name)
    first_message = first_message.replace("[Last 4 Digits]", "1234").replace("[Amount]", f"{conversation.customer_persona.debt_amount:.2f}")
    first_message = first_message.replace("[X]", str(conversation.customer_persona.months_behind))
    
    conversation.add_message("agent", first_message)
    logger.info(f"Starting conversation with {customer_name}")
    
    # Prepare conversation history for the model context
    conversation_history = [
        {"role": "system", "content": "This is a simulated conversation between a debt collection agent and a customer who has defaulted on a loan."}
    ]
    
    # Add agent instructions
    conversation_history.append({
        "role": "system", 
        "content": f"You are simulating a debt collection agent. Follow this script: {agent_prompt}"
    })
    
    # Add customer persona
    conversation_history.append({
        "role": "system", 
        "content": f"You are simulating a customer with this persona: {customer_prompt}"
    })
    
    # Add first message
    conversation_history.append({
        "role": "assistant", 
        "content": first_message
    })
    
    # Simulate the conversation
    turn = 0
    current_role = "customer"  # Next message should be from customer (responding to agent)
    
    while turn < max_turns:
        try:
            if current_role == "customer":
                # Get customer response
                logger.info(f"Generating customer response (turn {turn+1})")
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=conversation_history + [{"role": "system", "content": "You are now the customer. Respond naturally as this customer persona would."}],
                    temperature=0.7
                )
                message = response.choices[0].message.content
                conversation.add_message("customer", message)
                conversation_history.append({"role": "user", "content": message})
                current_role = "agent"
                logger.info(f"Customer response: {message[:50]}...")
                
            else:  # Agent's turn
                # Get agent response
                logger.info(f"Generating agent response (turn {turn+1})")
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=conversation_history + [{"role": "system", "content": "You are now the debt collection agent. Respond according to your script."}],
                    temperature=0.3
                )
                message = response.choices[0].message.content
                conversation.add_message("agent", message)
                conversation_history.append({"role": "assistant", "content": message})
                current_role = "customer"
                logger.info(f"Agent response: {message[:50]}...")
            
            turn += 1
            
            # End conversation if it seems complete
            if check_conversation_complete(conversation):
                logger.info("Conversation appears complete, ending simulation")
                break
                
        except Exception as e:
            logger.error(f"Error during conversation simulation: {e}")
            break
    
    # Save the conversation to file
    file_path = conversation.save()
    logger.info(f"Saved conversation to {file_path}")
    
    return conversation

def check_conversation_complete(conversation: Conversation) -> bool:
    """Check if the conversation seems to be complete."""
    # Logic to determine if conversation is complete based on content
    if len(conversation.messages) < 3:
        return False
    
    last_message = conversation.messages[-1].content.lower()
    
    # Check for closing indicators
    closing_phrases = [
        "thank you for your time",
        "have a good day",
        "goodbye",
        "call you back",
        "talk to you later"
    ]
    
    return any(phrase in last_message for phrase in closing_phrases) 
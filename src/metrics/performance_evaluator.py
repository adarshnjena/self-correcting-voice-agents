import os
import re
import logging
import json
from typing import Dict, Any, List, Optional
from collections import Counter

import openai
from openai import OpenAI

from src.testing.conversation_simulator import Conversation

logger = logging.getLogger(__name__)

def evaluate_conversations(conversations: List[Conversation]) -> Dict[str, float]:
    """
    Evaluate the performance of the agent across multiple test conversations.
    
    Args:
        conversations: List of conversation objects to evaluate
        
    Returns:
        Dictionary of performance metrics
    """
    # Initialize metrics
    metrics = {
        "repetition_rate": 0.0,
        "negotiation_effectiveness": 0.0,
        "average_turn_count": 0.0,
        "resolution_rate": 0.0,
        "compliance_score": 0.0
    }
    
    # Calculate average metrics across all conversations
    if not conversations:
        return metrics
    
    # Calculate repetition rate
    repetition_scores = [_calculate_repetition_rate(c) for c in conversations]
    metrics["repetition_rate"] = sum(repetition_scores) / len(repetition_scores)
    
    # Calculate negotiation effectiveness
    negotiation_scores = [_calculate_negotiation_effectiveness(c) for c in conversations]
    metrics["negotiation_effectiveness"] = sum(negotiation_scores) / len(negotiation_scores)
    
    # Calculate average turn count
    turn_counts = [len(c.messages) // 2 for c in conversations]  # Divide by 2 for agent-customer pairs
    metrics["average_turn_count"] = sum(turn_counts) / len(turn_counts)
    
    # Calculate resolution rate
    resolution_scores = [_calculate_resolution_score(c) for c in conversations]
    metrics["resolution_rate"] = sum(resolution_scores) / len(resolution_scores)
    
    # Calculate compliance score
    compliance_scores = [_calculate_compliance_score(c) for c in conversations]
    metrics["compliance_score"] = sum(compliance_scores) / len(compliance_scores)
    
    return metrics

def generate_improvement_feedback(
    conversations: List[Conversation], 
    metrics: Dict[str, float]
) -> Dict[str, Any]:
    """
    Generate feedback for improving the agent script based on test results.
    
    Args:
        conversations: List of conversations to analyze
        metrics: Dictionary of performance metrics
        
    Returns:
        Dictionary containing feedback and suggested improvements
    """
    # Use OpenAI API for advanced analysis if available
    if os.getenv("OPENAI_API_KEY"):
        return _generate_improvement_feedback_with_api(conversations, metrics)
    else:
        # Fallback to rule-based analysis
        return _generate_improvement_feedback_rule_based(conversations, metrics)

def _calculate_repetition_rate(conversation: Conversation) -> float:
    """
    Calculate how often the agent repeats itself unnecessarily.
    Lower is better (less repetition).
    
    Returns a value between 0.0 (no repetition) and 1.0 (high repetition).
    """
    agent_messages = [m.content for m in conversation.messages if m.role == "agent"]
    if len(agent_messages) <= 1:
        return 0.0
    
    # Simplified approach: Check for repeated phrases
    repetition_count = 0
    significant_phrases = []
    
    for message in agent_messages:
        # Extract significant phrases (length > 5 words)
        phrases = [p.strip() for p in re.findall(r'[^.!?]+[.!?]', message)]
        phrases = [p for p in phrases if len(p.split()) > 5]
        
        for phrase in phrases:
            # Check if this is a repetition of an earlier phrase
            for existing_phrase in significant_phrases:
                if _phrase_similarity(phrase, existing_phrase) > 0.7:
                    repetition_count += 1
                    break
            significant_phrases.append(phrase)
    
    # Calculate the rate
    if not significant_phrases:
        return 0.0
    
    return min(1.0, repetition_count / len(significant_phrases))

def _calculate_negotiation_effectiveness(conversation: Conversation) -> float:
    """
    Calculate how effectively the agent negotiates.
    Higher is better (more effective negotiation).
    
    Returns a value between 0.0 (poor negotiation) and 1.0 (excellent negotiation).
    """
    agent_messages = [m.content for m in conversation.messages if m.role == "agent"]
    customer_messages = [m.content for m in conversation.messages if m.role == "customer"]
    
    if len(agent_messages) < 3 or len(customer_messages) < 2:
        return 0.5  # Not enough interaction to judge
    
    # Look for negotiation elements in agent messages
    negotiation_elements = {
        "offers_options": False,
        "acknowledges_concerns": False,
        "provides_alternatives": False,
        "explains_benefits": False,
        "closes_agreement": False
    }
    
    # Check for options
    options_patterns = [
        r'(option|plan|alternative) [123]',
        r'(several|multiple|different) options',
        r'(could|can|might) (offer|provide|suggest)'
    ]
    for message in agent_messages:
        for pattern in options_patterns:
            if re.search(pattern, message.lower()):
                negotiation_elements["offers_options"] = True
                break
    
    # Check for acknowledgment of concerns
    acknowledgment_patterns = [
        r'(understand|appreciate|recognize) (your|the) (concern|situation|difficulty)',
        r'(sorry|apologize) to hear',
        r'(must be|sounds) (difficult|challenging|tough)',
        r'thank you for (explaining|sharing)'
    ]
    for message in agent_messages:
        for pattern in acknowledgment_patterns:
            if re.search(pattern, message.lower()):
                negotiation_elements["acknowledges_concerns"] = True
                break
    
    # Check for alternatives
    alternative_patterns = [
        r'(another|different|alternative) (option|approach|plan)',
        r'(instead|alternatively)',
        r'(we could|we can|let\'s) (try|consider)'
    ]
    for message in agent_messages:
        for pattern in alternative_patterns:
            if re.search(pattern, message.lower()):
                negotiation_elements["provides_alternatives"] = True
                break
    
    # Check for explaining benefits
    benefit_patterns = [
        r'(benefit|advantage|help) (you|your)',
        r'(this way|this will|this means)',
        r'(allow you to|enable you to|help you)'
    ]
    for message in agent_messages:
        for pattern in benefit_patterns:
            if re.search(pattern, message.lower()):
                negotiation_elements["explains_benefits"] = True
                break
    
    # Check for closing agreement
    closing_patterns = [
        r'(do we have|have we reached) (an agreement|a deal)',
        r'(does that|is this) (work|acceptable|agreeable)',
        r'(shall we|should we) (proceed|move forward)',
        r'(confirm|agree to) (the|this) (plan|arrangement|payment)'
    ]
    for message in agent_messages:
        for pattern in closing_patterns:
            if re.search(pattern, message.lower()):
                negotiation_elements["closes_agreement"] = True
                break
    
    # Calculate effectiveness score
    elements_present = sum(1 for value in negotiation_elements.values() if value)
    return elements_present / len(negotiation_elements)

def _calculate_resolution_score(conversation: Conversation) -> float:
    """
    Calculate how often conversations end with a resolution.
    Higher is better (more resolved conversations).
    
    Returns a value between 0.0 (no resolution) and 1.0 (clear resolution).
    """
    if len(conversation.messages) < 4:
        return 0.0  # Too short to have a resolution
    
    # Extract the last few messages
    last_messages = conversation.messages[-4:]
    last_messages_text = " ".join(m.content.lower() for m in last_messages)
    
    # Check for resolution indicators
    resolution_indicators = [
        r'(agree|agreed|accept|commitment) (to|on) (payment|plan)',
        r'(will|can) pay (.*) on (.*)',
        r'(schedule|set up) (the|a) payment',
        r'(thank you|appreciate) (for|your) (help|assistance|understanding)',
        r'(next|follow-up|confirmation) (steps|process|email)'
    ]
    
    resolution_points = 0
    for pattern in resolution_indicators:
        if re.search(pattern, last_messages_text):
            resolution_points += 1
    
    # Check for non-resolution indicators
    non_resolution_indicators = [
        r'(call back|contact you later|think about it)',
        r'(not|can\'t) (agree|accept|afford)',
        r'(need more|additional) (time|information)',
        r'(unhappy|dissatisfied) with',
        r'(disconnect|hang up)'
    ]
    
    for pattern in non_resolution_indicators:
        if re.search(pattern, last_messages_text):
            resolution_points -= 1
    
    # Normalize to 0.0-1.0 range
    normalized_score = (resolution_points + 3) / 6  # Range from -3 to +3 normalized to 0.0-1.0
    return max(0.0, min(1.0, normalized_score))

def _calculate_compliance_score(conversation: Conversation) -> float:
    """
    Calculate how well the agent follows compliance guidelines.
    Higher is better (more compliant).
    
    Returns a value between 0.0 (poor compliance) and 1.0 (excellent compliance).
    """
    agent_messages = [m.content.lower() for m in conversation.messages if m.role == "agent"]
    if not agent_messages:
        return 0.0
    
    all_agent_text = " ".join(agent_messages)
    
    # Check for required compliance elements
    compliance_elements = {
        "identifies_self": False,
        "states_company": False,
        "states_recording": False,
        "verifies_identity": False,
        "explains_purpose": False
    }
    
    # Check for agent identification
    if re.search(r'(my name is|this is) [a-z]+', all_agent_text):
        compliance_elements["identifies_self"] = True
    
    # Check for company identification
    if re.search(r'(calling from|with) [a-z ]+', all_agent_text):
        compliance_elements["states_company"] = True
    
    # Check for recording disclosure
    if re.search(r'(call|conversation) (may be|is being) recorded', all_agent_text):
        compliance_elements["states_recording"] = True
    
    # Check for identity verification
    if re.search(r'(verify|confirm) (your|identity|information)', all_agent_text):
        compliance_elements["verifies_identity"] = True
    
    # Check for purpose statement
    if re.search(r'(regarding|about|concerning) (your|the) (loan|account|payment)', all_agent_text):
        compliance_elements["explains_purpose"] = True
    
    # Check for prohibited language (weighted negatively)
    prohibited_language = {
        "threatening": [
            r'(legal action|lawsuit|court|police|arrest)',
            r'(must|have to|required to) pay (immediately|now)',
            r'(consequences|penalties) (will|shall) (occur|happen|follow)'
        ],
        "harassment": [
            r'(fail|refuse|neglect) to pay',
            r'(irresponsible|negligent|delinquent)',
            r'(repeatedly|continuously|again and again)'
        ],
        "false_statements": [
            r'(only|last|final) (chance|opportunity)',
            r'(guaranteed|promise) to (remove|clear|fix)',
            r'(immediately|instantly) (improve|increase|raise)'
        ]
    }
    
    prohibited_count = 0
    for category, patterns in prohibited_language.items():
        for pattern in patterns:
            if re.search(pattern, all_agent_text):
                prohibited_count += 1
    
    # Calculate the compliance score
    compliance_count = sum(1 for value in compliance_elements.values() if value)
    compliance_score = compliance_count / len(compliance_elements)
    
    # Reduce score for prohibited language
    compliance_score = max(0.0, compliance_score - (prohibited_count * 0.2))
    
    return compliance_score

def _phrase_similarity(phrase1: str, phrase2: str) -> float:
    """
    Calculate a simple similarity score between two phrases.
    
    Returns a value between 0.0 (no similarity) and 1.0 (identical).
    """
    words1 = set(phrase1.lower().split())
    words2 = set(phrase2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union)

def _generate_improvement_feedback_with_api(
    conversations: List[Conversation], 
    metrics: Dict[str, float]
) -> Dict[str, Any]:
    """Generate improvement feedback using OpenAI API."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    feedback = {
        "metrics": metrics,
        "general_feedback": "",
        "script_improvements": {},
        "additional_sections_needed": [],
        "section_improvements": {}
    }
    
    # Prepare conversation samples for analysis
    conversation_samples = []
    for i, conv in enumerate(conversations[:3]):  # Limit to 3 samples for API context
        messages_text = "\n".join([f"{m.role.upper()}: {m.content}" for m in conv.messages])
        conversation_samples.append(f"CONVERSATION {i+1} (Persona: {conv.customer_persona.name}):\n{messages_text}")
    
    conversation_text = "\n\n".join(conversation_samples)
    
    try:
        # Get general feedback
        general_prompt = f"""
        You are an expert in analyzing debt collection conversations.
        
        METRICS:
        {json.dumps(metrics, indent=2)}
        
        CONVERSATION SAMPLES:
        {conversation_text}
        
        Based on these conversations and metrics, provide:
        1. General feedback on the agent's performance
        2. 3-5 specific areas for improvement
        
        Format your response as JSON with these fields:
        - general_feedback: A paragraph of overall assessment
        - improvement_areas: Array of specific improvement suggestions
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You analyze debt collection conversations and provide expert feedback."},
                {"role": "user", "content": general_prompt}
            ],
            temperature=0.4
        )
        
        general_feedback_data = json.loads(response.choices[0].message.content)
        feedback["general_feedback"] = general_feedback_data.get("general_feedback", "")
        
        # Generate script section improvements
        section_prompt = f"""
        You are an expert in improving debt collection scripts.
        
        METRICS:
        {json.dumps(metrics, indent=2)}
        
        CONVERSATION SAMPLES:
        {conversation_text}
        
        IMPROVEMENT AREAS:
        {json.dumps(general_feedback_data.get("improvement_areas", []), indent=2)}
        
        Based on this analysis, provide specific script improvements:
        1. Identify which script sections need improvement
        2. Suggest specific text changes for those sections
        3. Recommend any new sections that should be added
        
        Format your response as JSON with these fields:
        - section_improvements: Object with section_id keys and improvement text values
        - additional_sections_needed: Array of objects with name and content fields
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You improve debt collection scripts based on conversation analysis."},
                {"role": "user", "content": section_prompt}
            ],
            temperature=0.4
        )
        
        script_improvements = json.loads(response.choices[0].message.content)
        feedback["section_improvements"] = script_improvements.get("section_improvements", {})
        feedback["additional_sections_needed"] = script_improvements.get("additional_sections_needed", [])
        
    except Exception as e:
        logger.error(f"Error generating improvement feedback with API: {e}")
        # Fallback to rule-based feedback
        feedback = _generate_improvement_feedback_rule_based(conversations, metrics)
    
    return feedback

def _generate_improvement_feedback_rule_based(
    conversations: List[Conversation], 
    metrics: Dict[str, float]
) -> Dict[str, Any]:
    """Generate improvement feedback using rule-based approach."""
    feedback = {
        "metrics": metrics,
        "general_feedback": "",
        "script_improvements": {},
        "additional_sections_needed": [],
        "section_improvements": {}
    }
    
    # General feedback based on metrics
    if metrics["repetition_rate"] > 0.3:
        feedback["general_feedback"] += "The agent is repeating information too frequently. "
    
    if metrics["negotiation_effectiveness"] < 0.6:
        feedback["general_feedback"] += "The agent's negotiation approach needs improvement. "
    
    if metrics["resolution_rate"] < 0.5:
        feedback["general_feedback"] += "Many conversations are ending without a clear resolution. "
    
    if metrics["compliance_score"] < 0.8:
        feedback["general_feedback"] += "There are compliance issues in the agent's script. "
    
    if not feedback["general_feedback"]:
        feedback["general_feedback"] = "The agent is performing adequately overall."
    
    # Script section improvements
    if metrics["repetition_rate"] > 0.3:
        feedback["section_improvements"]["payment_discussion"] = "Reduce repetition of payment options. Consolidate payment information into clearer, more concise statements."
    
    if metrics["negotiation_effectiveness"] < 0.6:
        feedback["section_improvements"]["payment_plan"] = "Include more flexible payment options. Add language that acknowledges customer concerns and offers alternatives based on their situation."
    
    if metrics["resolution_rate"] < 0.5:
        feedback["section_improvements"]["confirmation"] = "Strengthen the closing agreement language. Add more direct questions to confirm customer agreement and commitment."
    
    if metrics["compliance_score"] < 0.8:
        feedback["section_improvements"]["introduction"] = "Ensure all compliance elements are present: agent identification, company name, recording disclosure, and purpose of call."
    
    # Suggest additional sections if needed
    if metrics["negotiation_effectiveness"] < 0.4:
        feedback["additional_sections_needed"].append({
            "name": "Alternative Payment Options",
            "content": "Let me share some additional payment options that might work better for your situation:\n\n1. Reduced monthly payments over a longer term\n2. Interest-only payments for a limited time\n3. A one-time settlement option\n\nWhich of these might work better for you?"
        })
    
    if metrics["resolution_rate"] < 0.3:
        feedback["additional_sections_needed"].append({
            "name": "Objection Handling",
            "content": "I understand your concerns about [specific objection]. Many customers have similar questions.\n\nLet me address this by explaining [explanation addressing objection].\n\nDoes that help clarify the situation?"
        })
    
    return feedback 
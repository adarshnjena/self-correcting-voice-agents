import os
import json
import logging
import copy
from typing import Dict, Any, List, Optional

import openai
from openai import OpenAI

from src.agent.debt_collection_agent import DebtCollectionScript, ScriptSection, save_script

logger = logging.getLogger(__name__)

def improve_script(
    current_script: DebtCollectionScript,
    feedback: Dict[str, Any]
) -> DebtCollectionScript:
    """
    Improve the debt collection script based on feedback from the performance evaluator.
    
    Args:
        current_script: The current version of the script
        feedback: Feedback and suggested improvements from the performance evaluator
        
    Returns:
        An improved version of the script
    """
    # Create a deep copy of the current script to modify
    improved_script = copy.deepcopy(current_script)
    
    # Update version number
    current_version = float(improved_script.version)
    improved_script.version = f"{current_version + 0.1:.1f}"
    
    # Log the improvement process
    logger.info(f"Improving script v{current_script.version} to v{improved_script.version}")
    
    # Use OpenAI API for advanced improvements if available
    if os.getenv("OPENAI_API_KEY") and feedback.get("general_feedback"):
        try:
            return _improve_script_with_api(current_script, feedback)
        except Exception as e:
            logger.error(f"Error improving script with API: {e}")
            logger.info("Falling back to rule-based improvement")
    
    # Apply section improvements from feedback
    _apply_section_improvements(improved_script, feedback)
    
    # Add recommended new sections
    _add_new_sections(improved_script, feedback)
    
    # Save the improved script
    save_script(improved_script, f"script_v{improved_script.version}.json")
    
    return improved_script

def _apply_section_improvements(
    script: DebtCollectionScript,
    feedback: Dict[str, Any]
) -> None:
    """Apply improvements to existing script sections."""
    section_improvements = feedback.get("section_improvements", {})
    
    for section_id, improvement_text in section_improvements.items():
        if section_id in script.sections:
            section = script.sections[section_id]
            
            # Log the change
            logger.info(f"Improving section '{section.name}' ({section_id})")
            
            # For text improvements, append to description and modify content
            if isinstance(improvement_text, str):
                # Add improvement note to description
                section.description = f"{section.description}\nImproved: {improvement_text}"
                
                # Apply specific improvement types based on section and feedback metrics
                metrics = feedback.get("metrics", {})
                
                if section_id == "payment_discussion" and metrics.get("repetition_rate", 0) > 0.3:
                    section.content = _reduce_repetition(section.content)
                    
                elif section_id == "payment_plan" and metrics.get("negotiation_effectiveness", 1) < 0.6:
                    section.content = _enhance_negotiation(section.content)
                    
                elif section_id == "confirmation" and metrics.get("resolution_rate", 1) < 0.5:
                    section.content = _strengthen_closing(section.content)
                    
                elif section_id == "introduction" and metrics.get("compliance_score", 1) < 0.8:
                    section.content = _improve_compliance(section.content)
                    
                else:
                    # Generic improvement - add a note at the end of the section
                    section.content = f"{section.content}\n\n[Note: {improvement_text}]"
            
            # For dictionary improvements with specific content changes
            elif isinstance(improvement_text, dict) and "content" in improvement_text:
                section.content = improvement_text["content"]
                if "description" in improvement_text:
                    section.description = improvement_text["description"]

def _add_new_sections(
    script: DebtCollectionScript,
    feedback: Dict[str, Any]
) -> None:
    """Add new recommended sections to the script."""
    additional_sections = feedback.get("additional_sections_needed", [])
    
    for new_section in additional_sections:
        if isinstance(new_section, dict) and "name" in new_section and "content" in new_section:
            # Create section ID from name
            section_id = new_section["name"].lower().replace(" ", "_")
            
            # Avoid duplicate IDs
            if section_id in script.sections:
                section_id = f"{section_id}_{len(script.sections)}"
            
            # Create the new section
            section = ScriptSection(
                section_id=section_id,
                name=new_section["name"],
                description=new_section.get("description", f"Added based on performance feedback"),
                content=new_section["content"],
                next_sections=new_section.get("next_sections", ["confirmation"])
            )
            
            # Add the section to the script
            script.sections[section_id] = section
            
            # Update next_sections in other sections to potentially include this new section
            # Find appropriate section to connect to new section
            if "objection" in section_id.lower():
                _update_section_flow(script, "payment_discussion", section_id)
                _update_section_flow(script, "hardship_options", section_id)
            elif "payment" in section_id.lower() or "option" in section_id.lower():
                _update_section_flow(script, "payment_discussion", section_id)
            
            logger.info(f"Added new section: '{section.name}' ({section_id})")

def _update_section_flow(
    script: DebtCollectionScript,
    source_section_id: str,
    target_section_id: str
) -> None:
    """Update the flow between sections by adding a new connection."""
    if source_section_id in script.sections and target_section_id in script.sections:
        source_section = script.sections[source_section_id]
        if target_section_id not in source_section.next_sections:
            source_section.next_sections.append(target_section_id)
            logger.info(f"Updated flow: {source_section_id} -> {target_section_id}")

def _improve_script_with_api(
    current_script: DebtCollectionScript,
    feedback: Dict[str, Any]
) -> DebtCollectionScript:
    """Use OpenAI API to generate more sophisticated script improvements."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Create a deep copy of the current script to modify
    improved_script = copy.deepcopy(current_script)
    
    # Update version number
    current_version = float(improved_script.version)
    improved_script.version = f"{current_version + 0.1:.1f}"
    
    # Prepare the context for the API
    script_sections_json = {}
    for section_id, section in current_script.sections.items():
        script_sections_json[section_id] = {
            "name": section.name,
            "description": section.description,
            "content": section.content,
            "next_sections": section.next_sections
        }
    
    prompt = f"""
    You are an expert in optimizing debt collection scripts. Based on the following feedback and metrics,
    improve the debt collection script to address the identified issues.
    
    CURRENT SCRIPT:
    {json.dumps(script_sections_json, indent=2)}
    
    PERFORMANCE METRICS:
    {json.dumps(feedback.get("metrics", {}), indent=2)}
    
    GENERAL FEEDBACK:
    {feedback.get("general_feedback", "")}
    
    SECTION-SPECIFIC IMPROVEMENTS NEEDED:
    {json.dumps(feedback.get("section_improvements", {}), indent=2)}
    
    ADDITIONAL SECTIONS RECOMMENDED:
    {json.dumps(feedback.get("additional_sections_needed", []), indent=2)}
    
    Please provide an improved version of the script that addresses these issues. For each section,
    modify the content as needed while maintaining the overall structure and flow.
    
    Return the improved script as a JSON object with the same structure as the original script.
    Each section should have: section_id, name, description, content, and next_sections.
    
    You may also add new sections if they would address the feedback.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are an expert in optimizing debt collection scripts."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        improved_sections = json.loads(response.choices[0].message.content)
        
        # Update the script with the improved sections
        if "sections" in improved_sections:
            improved_data = improved_sections["sections"]
        else:
            improved_data = improved_sections
        
        # Process each section in the response
        for section_id, section_data in improved_data.items():
            if section_id in improved_script.sections:
                # Update existing section
                section = improved_script.sections[section_id]
                if "content" in section_data:
                    section.content = section_data["content"]
                if "description" in section_data:
                    section.description = section_data["description"]
                if "name" in section_data:
                    section.name = section_data["name"]
                if "next_sections" in section_data:
                    section.next_sections = section_data["next_sections"]
            else:
                # Add new section
                new_section = ScriptSection(
                    section_id=section_id,
                    name=section_data.get("name", section_id.replace("_", " ").title()),
                    description=section_data.get("description", "Added based on performance feedback"),
                    content=section_data.get("content", ""),
                    next_sections=section_data.get("next_sections", ["confirmation"])
                )
                improved_script.sections[section_id] = new_section
                logger.info(f"Added new section from API: {section_id}")
        
    except Exception as e:
        logger.error(f"Error in API-based script improvement: {e}")
        # Apply simpler improvements as fallback
        _apply_section_improvements(improved_script, feedback)
        _add_new_sections(improved_script, feedback)
    
    # Save the improved script
    save_script(improved_script, f"script_v{improved_script.version}.json")
    
    return improved_script

def _reduce_repetition(content: str) -> str:
    """Reduce repetition in a script section."""
    # Example improvement: Consolidate repeated information
    improved_content = content
    
    # Replace specific repetitive patterns
    if "payment" in content.lower() and "options" in content.lower():
        improved_content = improved_content.replace(
            "Would you be able to make a payment today?\n\n[If customer can make a payment]\nThat's great. How much would you be able to pay today?",
            "Would you be able to make a payment today? If so, how much could you manage?"
        )
    
    # Add a more direct approach
    improved_content += "\n\nLet me outline your options clearly so we can find the best solution for your situation."
    
    return improved_content

def _enhance_negotiation(content: str) -> str:
    """Enhance negotiation effectiveness in a script section."""
    # Add more flexible language and emphasize customer benefits
    improved_content = content
    
    # Replace generic options with more specific ones
    if "Option 1:" in content and "Option 2:" in content:
        improved_content = improved_content.replace(
            "Option 1: [Payment plan details]\nOption 2: [Alternative payment plan details]",
            """Option 1: A structured payment plan of smaller monthly amounts over a longer period, which would reduce the immediate financial pressure.
            
Option 2: A short-term reduced payment plan followed by regular payments, which gives you some breathing room now.

Option 3: A one-time settlement amount if you're able to make a larger payment soon, which would resolve the debt more quickly."""
        )
    
    # Add empathetic language and benefit explanation
    improved_content += "\n\nWhichever option you choose, our goal is to help you successfully resolve this debt in a way that works for your financial situation. Each of these plans would help you avoid additional fees and rebuild your credit over time."
    
    return improved_content

def _strengthen_closing(content: str) -> str:
    """Strengthen the closing and resolution in a script section."""
    # Add more direct confirmation language
    improved_content = content
    
    # Replace vague confirmation with specific agreement
    improved_content = improved_content.replace(
        "[Summarize the agreement]",
        """To confirm, you've agreed to:
1. Make an initial payment of $[Amount] by [Date]
2. Follow with [Number] payments of $[Amount] on the [Day] of each month
3. Complete the final payment by [Date]

Can you confirm that this plan works for you?"""
    )
    
    # Add a clear next action
    improved_content += "\n\nOnce you confirm, I'll mark this agreement in our system and send your confirmation email right away. Do I have your permission to proceed with this plan?"
    
    return improved_content

def _improve_compliance(content: str) -> str:
    """Improve compliance elements in a script section."""
    # Ensure all required compliance elements are present
    improved_content = content
    
    # Make sure company and agent identification are clear
    if "[Agent Name]" in improved_content and "[Company Name]" in improved_content:
        improved_content = improved_content.replace(
            "Hello, my name is [Agent Name] calling from [Company Name].",
            "Hello, my name is [Agent Name], and I'm calling from [Company Name], a debt collection agency."
        )
    
    # Ensure recording disclosure is prominent
    if "recorded" in improved_content:
        improved_content = improved_content.replace(
            "Before we continue, I need to inform you that this call may be recorded for quality assurance purposes.",
            "Before we continue, I am required to inform you that this call is being recorded for quality assurance and compliance purposes."
        )
    
    # Add purpose statement if missing
    if "regarding your loan" not in improved_content.lower():
        improved_content = improved_content.replace(
            "I'm calling regarding your loan account ending in [Last 4 Digits], which is currently past due.",
            "I'm calling regarding your loan account ending in [Last 4 Digits], which is currently past due. The purpose of this call is to discuss options for bringing your account current."
        )
    
    return improved_content 
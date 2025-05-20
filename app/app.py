import os
import json
import sys
import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from openai import OpenAI

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.personas import persona_generator
from src.agent import debt_collection_agent
from src.testing import conversation_simulator
from src.metrics import performance_evaluator
from src.correction import script_improver

# Set page config
st.set_page_config(
    page_title="Self-Correcting Debt Collection Voice Agent",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if "current_script" not in st.session_state:
    st.session_state.current_script = debt_collection_agent.load_base_script()
if "iteration_history" not in st.session_state:
    st.session_state.iteration_history = []
if "latest_metrics" not in st.session_state:
    st.session_state.latest_metrics = None
if "latest_feedback" not in st.session_state:
    st.session_state.latest_feedback = None
if "test_conversations" not in st.session_state:
    st.session_state.test_conversations = []
if "realtime_conv_container" not in st.session_state:
    st.session_state.realtime_conv_container = None
if "current_tab" not in st.session_state:
    st.session_state.current_tab = 0  # Default to first tab

# Main header
st.title("🤖 Self-Correcting Debt Collection Voice Agent System")

# Main content area with tabs - define tabs first before they're referenced in button handlers
tab_labels = ["Current Script", "Test Results", "Improvement History", "Conversations", "Live Conversation"]
tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_labels)

# Auto-select the tab based on session state
if st.session_state.current_tab != 0:
    selected_tab = st.session_state.current_tab
    # Reset to default after use
    st.session_state.current_tab = 0
    # This JavaScript auto-clicks the selected tab
    tab_index = selected_tab  # 0-based index
    st.markdown(f"""
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            setTimeout(function() {{
                document.querySelectorAll('button[data-baseweb="tab"]')[{tab_index}].click();
            }}, 100);
        }});
    </script>
    """, unsafe_allow_html=True)

# Sidebar with controls
with st.sidebar:
    st.header("Controls")
    
    # API Key input
    api_key = st.text_input("OpenAI API Key (required)", type="password", 
                           help="Enter your OpenAI API key to use the system")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        api_key_provided = True
    else:
        api_key_provided = False
        st.warning("⚠️ Please enter your OpenAI API key to use the system")
    
    # Settings
    st.subheader("Test Settings")
    num_personas = st.slider("Number of Test Personas", min_value=1, max_value=10, value=3)
    
    # Metrics thresholds
    st.subheader("Quality Thresholds")
    repetition_threshold = st.slider("Maximum Repetition Rate (lower is better)", 
                                    min_value=0.0, max_value=1.0, value=0.2, step=0.05)
    negotiation_threshold = st.slider("Minimum Performance Score (higher is better)", 
                                     min_value=0.0, max_value=1.0, value=0.7, step=0.05)
    
    st.markdown("---")
    
    # Run buttons
    if st.button("🧪 Run Test Iteration", disabled=not api_key_provided):
        try:
            # Set current tab to Conversations (index 3)
            st.session_state.current_tab = 3
            
            # Create a placeholder for real-time updates
            progress_placeholder = st.empty()
            progress_placeholder.info("Starting test iteration...")
            
            # Generate test personas
            progress_placeholder.info("Generating test personas...")
            personas = persona_generator.generate_personas(count=num_personas)
            progress_placeholder.success(f"Generated {len(personas)} test personas")
            
            # Run simulated conversations
            test_conversations = []
            
            # Clear existing conversations and display new ones in the Conversations tab
            with tab4:
                st.session_state.realtime_conv_container = st.container()
            
            for i, persona in enumerate(personas, 1):
                progress_placeholder.info(f"Simulating conversation {i}/{len(personas)} with {persona.name}...")
                
                # Display persona details in the Conversations tab
                with tab4:
                    with st.session_state.realtime_conv_container:
                        st.subheader(f"Conversation with {persona.name}")
                        st.write(f"Age: {persona.age}, Occupation: {persona.occupation}")
                        st.write(f"Debt Amount: ${persona.debt_amount:.2f}, Months Behind: {persona.months_behind}")
                        st.write(f"Willingness to Pay: {int(persona.willingness_to_pay * 100)}%")
                        
                        # Create a placeholder for conversation messages
                        msg_placeholder = st.empty()
                        messages_area = msg_placeholder.container()
                        
                        # Create a callback function to update UI with each message
                        def message_callback(role, content):
                            with messages_area:
                                if role == "agent":
                                    st.markdown(f"**Agent:** {content}")
                                else:
                                    st.markdown(f"**Customer:** {content}")
                        
                        # Pass the callback to conversation simulator
                        conversation = conversation_simulator.simulate_conversation(
                            agent_script=st.session_state.current_script,
                            customer_persona=persona,
                            max_turns=15,
                            message_callback=message_callback  # Pass the callback function
                        )
                        
                        test_conversations.append(conversation)
                        st.markdown("---")  # Add separator between conversations
            
            # Evaluate performance
            progress_placeholder.info("Evaluating performance metrics...")
            metrics = performance_evaluator.evaluate_conversations(test_conversations)
            
            # Generate improvement feedback
            progress_placeholder.info("Generating improvement feedback...")
            feedback = performance_evaluator.generate_improvement_feedback(
                test_conversations, metrics
            )
            
            # Update session state
            st.session_state.latest_metrics = metrics
            st.session_state.latest_feedback = feedback
            st.session_state.test_conversations = test_conversations
            
            # Add to history
            history_entry = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "script_version": st.session_state.current_script.version,
                "metrics": metrics,
                "feedback_summary": feedback.get("general_feedback", "")[:100] + "..."
            }
            st.session_state.iteration_history.append(history_entry)
            
            # Reset the realtime container so conversations appear in the expanders next time
            st.session_state.realtime_conv_container = None
            
            progress_placeholder.success("Test iteration completed successfully!")
            
            # Switch to the Test Results tab to show metrics
            tab2.write("Test completed! Check the 'Conversations' tab to see all conversations.")
        except Exception as e:
            st.error(f"Error during test iteration: {str(e)}")
            import traceback
            st.exception(f"Detailed error: {traceback.format_exc()}")
    
    if st.button("🔄 Improve Script", disabled=not api_key_provided):
        if st.session_state.latest_feedback:
            try:
                with st.spinner("Improving script based on feedback..."):
                    # Improve the script
                    improved_script = script_improver.improve_script(
                        st.session_state.current_script,
                        st.session_state.latest_feedback
                    )
                    
                    # Update current script
                    st.session_state.current_script = improved_script
                    st.success(f"Script improved to version {improved_script.version}")
            except Exception as e:
                st.error(f"Error during script improvement: {str(e)}")
                import traceback
                st.exception(f"Detailed error: {traceback.format_exc()}")
        else:
            st.error("Run a test iteration first to generate feedback")

# Tab 1: Current Script
with tab1:
    st.header(f"Current Script (v{st.session_state.current_script.version})")
    
    # Display script sections
    for section_id, section in st.session_state.current_script.sections.items():
        with st.expander(f"{section.name} ({section_id})"):
            st.markdown(f"**Description:** {section.description}")
            st.text_area("Content", section.content, height=200, key=f"section_{section_id}")
            st.write(f"Next sections: {', '.join(section.next_sections)}")

# Tab 2: Test Results
with tab2:
    st.header("Latest Test Results")
    
    if st.session_state.latest_metrics:
        # Display metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Performance Metrics")
            metrics_df = pd.DataFrame({
                "Metric": list(st.session_state.latest_metrics.keys()),
                "Value": list(st.session_state.latest_metrics.values())
            })
            
            # Convert Value column to numeric to avoid string comparison issues
            metrics_df["Value"] = pd.to_numeric(metrics_df["Value"], errors="coerce")
            
            # Create a styled dataframe with different styling for repetition_rate
            styled_df = metrics_df.style
            
            # For repetition_rate, highlight low values as good (green) and high values as bad (red)
            repetition_rate_idx = metrics_df[metrics_df["Metric"] == "repetition_rate"].index
            if len(repetition_rate_idx) > 0:
                idx = repetition_rate_idx[0]
                styled_df = styled_df.highlight_between(
                    subset=pd.IndexSlice[idx:idx, ["Value"]], 
                    left=0.0, 
                    right=repetition_threshold, 
                    props="background-color:#aaffaa;color:#000000"
                ).highlight_between(
                    subset=pd.IndexSlice[idx:idx, ["Value"]], 
                    left=repetition_threshold, 
                    right=1.0, 
                    props="background-color:#ffaaaa;color:#000000"
                )
            
            # For all other metrics, highlight high values as good (green) and low values as bad (red)
            other_metrics_idx = metrics_df[metrics_df["Metric"] != "repetition_rate"].index
            if len(other_metrics_idx) > 0:
                styled_df = styled_df.highlight_between(
                    subset=pd.IndexSlice[other_metrics_idx, ["Value"]], 
                    left=negotiation_threshold, 
                    right=1.0, 
                    props="background-color:#aaffaa;color:#000000"
                ).highlight_between(
                    subset=pd.IndexSlice[other_metrics_idx, ["Value"]], 
                    left=0.0, 
                    right=negotiation_threshold, 
                    props="background-color:#ffaaaa;color:#000000"
                )
            
            st.dataframe(styled_df)
            
            # Create a simple bar chart
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Color bars based on whether higher or lower values are better for each metric
            bar_colors = []
            for metric in metrics_df["Metric"]:
                if metric == "repetition_rate":
                    # For repetition rate, lower is better
                    value = metrics_df.loc[metrics_df["Metric"] == metric, "Value"].values[0]
                    bar_colors.append('green' if value <= repetition_threshold else 'red')
                else:
                    # For other metrics, higher is better
                    value = metrics_df.loc[metrics_df["Metric"] == metric, "Value"].values[0]
                    bar_colors.append('green' if value >= negotiation_threshold else 'red')
            
            bars = ax.bar(metrics_df["Metric"], metrics_df["Value"], color=bar_colors)
            
            # Add threshold lines where applicable
            ax.axhline(y=repetition_threshold, color='red', linestyle='--', alpha=0.7, label=f'Repetition Threshold ({repetition_threshold})')
            ax.axhline(y=negotiation_threshold, color='green', linestyle='--', alpha=0.7, label=f'Performance Threshold ({negotiation_threshold})')
            
            ax.set_ylim(0, 1)
            ax.set_ylabel('Score')
            ax.set_title('Performance Metrics')
            ax.legend()
            
            # Add values on top of bars
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:.2f}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom')
            
            st.pyplot(fig)
        
        with col2:
            st.subheader("Improvement Feedback")
            if st.session_state.latest_feedback:
                st.markdown(f"**General Feedback:**")
                st.info(st.session_state.latest_feedback.get("general_feedback", "No general feedback available"))
                
                st.markdown("**Section Improvements:**")
                section_improvements = st.session_state.latest_feedback.get("section_improvements", {})
                if section_improvements:
                    for section_id, improvement in section_improvements.items():
                        st.markdown(f"* **{section_id}**: {improvement[:100]}...")
                else:
                    st.write("No specific section improvements suggested")
                
                st.markdown("**New Sections Recommended:**")
                new_sections = st.session_state.latest_feedback.get("additional_sections_needed", [])
                if new_sections:
                    for i, section in enumerate(new_sections):
                        st.markdown(f"* **{section.get('name', f'New Section {i+1}')}**")
                else:
                    st.write("No new sections recommended")
    else:
        st.info("Run a test iteration to see results here")

# Tab 3: Improvement History
with tab3:
    st.header("Script Improvement History")
    
    if st.session_state.iteration_history:
        history_df = pd.DataFrame(st.session_state.iteration_history)
        
        # Display as a table
        st.dataframe(history_df)
        
        # Plot metrics over time
        if len(history_df) > 1:
            st.subheader("Metrics Over Time")
            
            # Extract metrics from history
            metric_history = []
            for entry in st.session_state.iteration_history:
                metrics = entry["metrics"]
                metrics["version"] = entry["script_version"]
                metrics["timestamp"] = entry["timestamp"]
                metric_history.append(metrics)
            
            metric_df = pd.DataFrame(metric_history)
            
            # Convert metric columns to numeric to avoid string comparison issues
            for metric in ["repetition_rate", "negotiation_effectiveness", "resolution_rate", "compliance_score"]:
                if metric in metric_df.columns:
                    metric_df[metric] = pd.to_numeric(metric_df[metric], errors="coerce")
            
            # Plot
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Plot each metric
            for metric in ["repetition_rate", "negotiation_effectiveness", "resolution_rate", "compliance_score"]:
                if metric in metric_df.columns:
                    ax.plot(metric_df["version"], metric_df[metric], marker='o', label=metric)
            
            ax.set_xlabel('Script Version')
            ax.set_ylabel('Score')
            ax.set_title('Metrics Improvement Over Time')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            st.pyplot(fig)
    else:
        st.info("No improvement history yet")

# Tab 4: Conversations
with tab4:
    st.header("Test Conversations")
    
    # If we're showing real-time conversations during simulation
    if st.session_state.realtime_conv_container is not None:
        st.subheader("🔄 Test in Progress - Watching Conversations in Real-time")
        # Real-time conversations will show up here via the container in st.session_state.realtime_conv_container
    # If there's no active real-time conversation display and we have test conversations
    elif st.session_state.test_conversations:
        st.subheader("📚 Previous Test Results")
        for i, conversation in enumerate(st.session_state.test_conversations):
            with st.expander(f"Conversation with {conversation.customer_persona.name} (Willingness to pay: {conversation.customer_persona.willingness_to_pay:.2f})"):
                st.subheader("Customer Persona")
                st.json({
                    "name": conversation.customer_persona.name,
                    "age": conversation.customer_persona.age,
                    "occupation": conversation.customer_persona.occupation,
                    "debt_amount": conversation.customer_persona.debt_amount,
                    "months_behind": conversation.customer_persona.months_behind,
                    "reasons_for_default": conversation.customer_persona.reasons_for_default,
                    "communication_style": conversation.customer_persona.communication_style,
                    "willingness_to_pay": conversation.customer_persona.willingness_to_pay
                })
                
                st.subheader("Conversation")
                for msg in conversation.messages:
                    if msg.role == "agent":
                        st.markdown(f"**Agent:** {msg.content}")
                    else:
                        st.markdown(f"**Customer:** {msg.content}")
    else:
        st.info("Run a test iteration to see conversations here")

# Tab 5: Live Conversation
with tab5:
    st.header("Live Interactive Conversation")
    
    # Initialize chat history in session state if it doesn't exist
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        
    # Initialize persona for live conversation if it doesn't exist
    if "live_persona" not in st.session_state:
        st.session_state.live_persona = None
    
    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    # Sidebar for this tab
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if not api_key_provided:
            st.warning("Please provide an OpenAI API key in the sidebar to use the live conversation feature.")
        elif st.session_state.live_persona is None:
            if st.button("Generate Random Customer Persona", disabled=not api_key_provided):
                try:
                    with st.spinner("Generating a random customer persona..."):
                        personas = persona_generator.generate_personas(count=1)
                        st.session_state.live_persona = personas[0]
                        
                        # Add system message to chat history
                        agent_script = st.session_state.current_script
                        starting_section = agent_script.get_starting_section()
                        first_message = starting_section.content if starting_section else "Hello, this is a debt collection agent calling about your past-due loan."
                        first_message = first_message.replace("[Agent Name]", "AI Agent").replace("[Customer Name]", st.session_state.live_persona.name)
                        first_message = first_message.replace("[Last 4 Digits]", "1234").replace("[Amount]", f"{st.session_state.live_persona.debt_amount:.2f}")
                        first_message = first_message.replace("[X]", str(st.session_state.live_persona.months_behind))
                        
                        st.session_state.chat_history.append({"role": "assistant", "content": first_message})
                        st.rerun()
                except Exception as e:
                    st.error(f"Error generating persona: {str(e)}")
        else:
            # Input for user message
            if prompt := st.chat_input("Type your response as the customer...", disabled=not api_key_provided):
                # Add user message to chat history immediately
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                
                # Display user message immediately
                with chat_container:
                    with st.chat_message("user"):
                        st.write(prompt)
                
                try:
                    # Get AI response
                    # Prepare the context for the model
                    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                    
                    # Prepare conversation history for the model
                    messages = [
                        {"role": "system", "content": "You are simulating a debt collection agent following a script. The user is roleplaying as a customer with debt."},
                        {"role": "system", "content": f"Agent script: {st.session_state.current_script.to_prompt()}"},
                        {"role": "system", "content": f"Customer persona (only you can see this, never reveal these details directly): {st.session_state.live_persona.to_prompt()}"}
                    ]
                    
                    # Add conversation history
                    for msg in st.session_state.chat_history:
                        role = "assistant" if msg["role"] == "assistant" else "user"
                        messages.append({"role": role, "content": msg["content"]})
                    
                    # Create a placeholder for the agent's response
                    with chat_container:
                        agent_message_placeholder = st.chat_message("assistant").empty()
                        agent_message_placeholder.markdown("🤔 Thinking...")
                    
                    # Generate response
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages,
                        temperature=0.7
                    )
                    
                    agent_response = response.choices[0].message.content
                    
                    # Add AI response to chat history
                    st.session_state.chat_history.append({"role": "assistant", "content": agent_response})
                    
                    # Update the placeholder with the actual response
                    agent_message_placeholder.markdown(agent_response)
                    
                except Exception as e:
                    st.error(f"Error generating response: {str(e)}")
                    import traceback
                    st.exception(f"Detailed error: {traceback.format_exc()}")
            
            if st.button("Reset Conversation"):
                st.session_state.chat_history = []
                st.session_state.live_persona = None
                st.rerun()
                
            if st.button("Save Conversation") and st.session_state.live_persona and len(st.session_state.chat_history) > 1:
                try:
                    # Create a Conversation object from the chat history
                    from src.testing.conversation_simulator import Conversation, Message
                    
                    messages = []
                    for msg in st.session_state.chat_history:
                        role = "agent" if msg["role"] == "assistant" else "customer"
                        messages.append(Message(role=role, content=msg["content"]))
                    
                    conversation = Conversation(
                        agent_script=st.session_state.current_script,
                        customer_persona=st.session_state.live_persona,
                        messages=messages
                    )
                    
                    # Save the conversation
                    file_path = conversation.save()
                    
                    # Add to test conversations for analysis
                    if "test_conversations" not in st.session_state:
                        st.session_state.test_conversations = []
                    
                    st.session_state.test_conversations.append(conversation)
                    
                    st.success(f"Conversation saved! You can view it in the 'Conversations' tab.")
                except Exception as e:
                    st.error(f"Error saving conversation: {str(e)}")
                    import traceback
                    st.exception(f"Detailed error: {traceback.format_exc()}")
    
    with col2:
        if st.session_state.live_persona:
            st.subheader("Customer Persona")
            st.info(f"""
            **Name:** {st.session_state.live_persona.name}  
            **Age:** {st.session_state.live_persona.age}  
            **Occupation:** {st.session_state.live_persona.occupation}  
            **Debt Amount:** ${st.session_state.live_persona.debt_amount:.2f}  
            **Months Behind:** {st.session_state.live_persona.months_behind}  
            **Willingness to Pay:** {int(st.session_state.live_persona.willingness_to_pay * 100)}%
            """)
            
            with st.expander("View Full Persona Details"):
                st.json({
                    "name": st.session_state.live_persona.name,
                    "age": st.session_state.live_persona.age,
                    "occupation": st.session_state.live_persona.occupation,
                    "income": st.session_state.live_persona.income,
                    "debt_amount": st.session_state.live_persona.debt_amount,
                    "months_behind": st.session_state.live_persona.months_behind,
                    "reasons_for_default": st.session_state.live_persona.reasons_for_default,
                    "communication_style": st.session_state.live_persona.communication_style,
                    "negotiation_style": st.session_state.live_persona.negotiation_style,
                    "objections": st.session_state.live_persona.objections,
                    "financial_situation": st.session_state.live_persona.financial_situation,
                    "willingness_to_pay": st.session_state.live_persona.willingness_to_pay
                })

# Footer
st.markdown("---")
st.markdown("Self-Correcting Debt Collection Voice Agent System | Created with ❤️ using Streamlit and OpenAI") 
st.markdown("**Note:** This application requires an OpenAI API key to function. Enter your key in the sidebar to get started.") 
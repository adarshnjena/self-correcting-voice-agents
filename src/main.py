import os
import logging
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the self-correcting voice agent system."""
    logger.info("Starting Self-Correcting Voice Agent System")
    
    # Import core components
    from src.personas import persona_generator
    from src.agent import debt_collection_agent
    from src.testing import conversation_simulator
    from src.metrics import performance_evaluator
    from src.correction import script_improver
    
    # Initialize the base debt collection script
    base_script = debt_collection_agent.load_base_script()
    current_script = base_script
    
    # Set initial thresholds for metrics
    repetition_threshold = float(os.getenv("METRICS_THRESHOLD_REPETITION", "0.2"))
    negotiation_threshold = float(os.getenv("METRICS_THRESHOLD_NEGOTIATION", "0.7"))
    
    # Improvement iterations
    max_iterations = int(os.getenv("MAX_ITERATIONS", "10"))
    current_iteration = 0
    
    while current_iteration < max_iterations:
        logger.info(f"Starting iteration {current_iteration + 1}/{max_iterations}")
        
        # 1. Generate test personas
        personas = persona_generator.generate_personas(count=5)
        logger.info(f"Generated {len(personas)} test personas")
        
        # 2. Run simulated conversations with current script
        test_results = []
        for persona in personas:
            conversation = conversation_simulator.simulate_conversation(
                agent_script=current_script,
                customer_persona=persona
            )
            test_results.append(conversation)
            
        logger.info(f"Completed {len(test_results)} test conversations")
        
        # 3. Evaluate performance metrics
        metrics = performance_evaluator.evaluate_conversations(test_results)
        logger.info(f"Performance metrics: {metrics}")
        
        # 4. Check if current script meets thresholds
        if (metrics["repetition_rate"] <= repetition_threshold and 
                metrics["negotiation_effectiveness"] >= negotiation_threshold):
            logger.info("Script meets or exceeds all performance thresholds!")
            break
            
        # 5. Improve script based on test results
        improvement_feedback = performance_evaluator.generate_improvement_feedback(
            test_results, metrics
        )
        current_script = script_improver.improve_script(
            current_script, improvement_feedback
        )
        
        logger.info("Script updated based on test results")
        current_iteration += 1
    
    logger.info(f"Finished after {current_iteration} iterations")
    return {
        "final_script": current_script,
        "iterations": current_iteration,
        "final_metrics": metrics if current_iteration > 0 else None
    }

if __name__ == "__main__":
    results = main()
    print("\nFinal Results:")
    print(f"Completed in {results['iterations']} iterations")
    if results['final_metrics']:
        print(f"Final Repetition Rate: {results['final_metrics']['repetition_rate']:.2f}")
        print(f"Final Negotiation Effectiveness: {results['final_metrics']['negotiation_effectiveness']:.2f}") 
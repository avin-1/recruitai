"""
Monitoring and Feedback Agent - Processes HR feedback and modifies agent prompts using LLM
"""
import os
import json
from typing import Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv
from backend.prompt_manager import prompt_manager
from backend.agent_orchestrator import AIAgent, notification_store

load_dotenv()

class MonitoringAgent(AIAgent):
    """Monitors agent performance and collects metrics"""
    
    def __init__(self):
        super().__init__(
            "Monitoring Agent",
            "monitors AI agent performance, collects metrics, and identifies areas for improvement"
        )
    
    def monitor_agent_performance(self, agent_name: str, metrics: Dict) -> Dict:
        """Monitor and analyze agent performance"""
        self.notify(
            f"📊 Monitoring performance for {agent_name}...",
            'info',
            reasoning=f"Collecting metrics: {json.dumps(metrics)}"
        )
        
        # Analyze metrics
        analysis = {
            'agent_name': agent_name,
            'metrics': metrics,
            'recommendations': []
        }
        
        # Simple monitoring logic (can be enhanced with LLM)
        if metrics.get('error_rate', 0) > 0.1:
            analysis['recommendations'].append("High error rate detected - consider reviewing agent logic")
        
        if metrics.get('response_time', 0) > 5.0:
            analysis['recommendations'].append("Slow response time - optimization may be needed")
        
        self.notify(
            f"✅ Performance analysis complete for {agent_name}",
            'success',
            reasoning=f"Identified {len(analysis['recommendations'])} recommendations"
        )
        
        return analysis


class FeedbackAgent(AIAgent):
    """Processes HR feedback and suggests prompt modifications using LLM"""
    
    def __init__(self):
        super().__init__(
            "Feedback Agent",
            "processes HR feedback, analyzes it with LLM, and suggests prompt modifications to improve agent behavior"
        )
        
        # Initialize LLM client for prompt modification
        try:
            token = os.environ.get('HF_TOKEN')
            if token:
                self.llm_client = OpenAI(
                    base_url="https://router.huggingface.co/v1",
                    api_key=token,
                    timeout=60.0
                )
            else:
                self.llm_client = None
        except:
            self.llm_client = None
    
    def process_feedback(self, agent_name: str, feedback_text: str, hr_email: str = None) -> Dict:
        """Process HR feedback and generate prompt modification suggestions using LLM"""
        # Submit feedback to database
        feedback_id = prompt_manager.submit_feedback(agent_name, feedback_text, hr_email)
        
        self.notify(
            f"📝 Processing feedback for {agent_name}...",
            'processing',
            reasoning=f"Feedback received: {feedback_text[:100]}..."
        )
        
        # Get current prompts for the agent
        current_prompts = {}
        for prompt_type in ['reasoning', 'matching', 'evaluation', 'scheduling', 'decision']:
            prompt = prompt_manager.get_prompt(agent_name, prompt_type)
            if prompt:
                current_prompts[prompt_type] = prompt
        
        if not current_prompts:
            return {
                'success': False,
                'error': f'No prompts found for agent: {agent_name}',
                'feedback_id': feedback_id
            }
        
        # Generate LLM suggestions for prompt modification
        llm_suggestion = self._generate_prompt_modification_suggestion(
            agent_name, feedback_text, current_prompts
        )
        
        # Generate modified prompts
        modified_prompts = self._generate_modified_prompts(
            agent_name, feedback_text, current_prompts, llm_suggestion
        )
        
        # Store LLM suggestion and modified prompts
        prompt_manager.update_feedback(
            feedback_id,
            llm_suggestion=llm_suggestion,
            modified_prompt=json.dumps(modified_prompts),
            status='suggested'
        )
        
        self.notify(
            f"✅ Generated prompt modification suggestions for {agent_name}",
            'success',
            reasoning=f"LLM analyzed feedback and suggested improvements to {len(modified_prompts)} prompt(s)"
        )
        
        return {
            'success': True,
            'feedback_id': feedback_id,
            'llm_suggestion': llm_suggestion,
            'modified_prompts': modified_prompts,
            'current_prompts': current_prompts
        }
    
    def _generate_prompt_modification_suggestion(self, agent_name: str, feedback_text: str, current_prompts: Dict) -> str:
        """Use LLM to analyze feedback and suggest how to modify prompts"""
        if not self.llm_client:
            return "LLM client not available. Using heuristic-based suggestion."
        
        try:
            prompt = f"""You are an expert AI prompt engineer. An HR manager provided feedback about the '{agent_name}' agent's behavior.

HR Feedback:
{feedback_text}

Current Agent Prompts:
{json.dumps(current_prompts, indent=2)}

Analyze the feedback and provide:
1. What issues the feedback highlights
2. Which prompts need modification
3. How the prompts should be changed to address the feedback
4. Expected improvement after modification

Provide your analysis in a clear, structured format."""

            response = self.llm_client.chat.completions.create(
                model="openai/gpt-oss-20b:fireworks-ai",
                messages=[
                    {"role": "system", "content": "You are an expert AI prompt engineer that helps improve agent behavior through prompt modifications."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating LLM suggestion: {str(e)}. Using fallback suggestion."
    
    def _generate_modified_prompts(self, agent_name: str, feedback_text: str, current_prompts: Dict, llm_suggestion: str) -> Dict:
        """Generate modified prompts based on feedback and LLM suggestion"""
        if not self.llm_client:
            # Fallback: return current prompts with minor modifications
            return current_prompts
        
        modified_prompts = {}
        
        try:
            for prompt_type, current_prompt in current_prompts.items():
                modification_prompt = f"""You are an expert AI prompt engineer. Modify the following prompt based on HR feedback.

Original Prompt ({prompt_type}):
{current_prompt}

HR Feedback:
{feedback_text}

LLM Analysis:
{llm_suggestion}

Modify the prompt to address the feedback while maintaining its core functionality. 
Return ONLY the modified prompt text, without any explanations or markdown formatting."""

                response = self.llm_client.chat.completions.create(
                    model="openai/gpt-oss-20b:fireworks-ai",
                    messages=[
                        {"role": "system", "content": "You are an expert at modifying AI prompts to improve agent behavior. Return only the modified prompt text."},
                        {"role": "user", "content": modification_prompt}
                    ],
                    max_tokens=1000
                )
                
                modified_prompt = response.choices[0].message.content.strip()
                # Remove markdown formatting if present
                if modified_prompt.startswith('```'):
                    lines = modified_prompt.split('\n')
                    if len(lines) > 2:
                        modified_prompt = '\n'.join(lines[1:-1])
                    # Remove code block markers
                    modified_prompt = modified_prompt.strip()
                    if modified_prompt.endswith('```'):
                        modified_prompt = modified_prompt[:-3].strip()
                
                modified_prompts[prompt_type] = modified_prompt
        except Exception as e:
            print(f"Error generating modified prompt for {prompt_type}: {e}")
            # Fallback to current prompt
            modified_prompts[prompt_type] = current_prompts.get(prompt_type, '')
        
        return modified_prompts
    
    def apply_prompt_modifications(self, feedback_id: int, agent_name: str, modified_prompts: Dict) -> Dict:
        """Apply the modified prompts to the agent"""
        try:
            applied_count = 0
            
            for prompt_type, modified_prompt in modified_prompts.items():
                if modified_prompt:
                    new_version = prompt_manager.update_prompt(
                        agent_name,
                        prompt_type,
                        modified_prompt,
                        change_reason=f"Applied based on feedback ID {feedback_id}",
                        feedback_id=feedback_id
                    )
                    applied_count += 1
            
            # Mark feedback as applied
            prompt_manager.update_feedback(feedback_id, status='applied', applied=True)
            
            self.notify(
                f"✅ Applied prompt modifications to {agent_name} ({applied_count} prompts updated)",
                'success',
                reasoning=f"Prompt modifications based on feedback ID {feedback_id} have been applied"
            )
            
            return {
                'success': True,
                'applied_count': applied_count,
                'feedback_id': feedback_id
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'feedback_id': feedback_id
            }


# Global agents
monitoring_agent = MonitoringAgent()
feedback_agent = FeedbackAgent()


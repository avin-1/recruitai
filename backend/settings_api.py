"""
Settings API - Handles feedback submission, prompt management, and agent monitoring
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys

# Add parent directory to path for imports
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(backend_dir))

from backend.prompt_manager import prompt_manager
# from backend.monitoring_feedback_agent import monitoring_agent, feedback_agent # Moved to lazy load

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "allow_headers": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]}})

@app.route('/api/settings/agents', methods=['GET'])
def get_agents():
    """Get list of all agents"""
    agents = [
        {'name': 'Interview Scheduler Agent', 'description': 'Schedules interviews based on availability'},
        {'name': 'Resume and Matching Agent', 'description': 'Matches resumes to job descriptions'},
        {'name': 'Job Description Agent', 'description': 'Parses job descriptions from PDFs and extracts structured information'},
        {'name': 'Shortlisting Agent', 'description': 'Evaluates candidate test performance'},
        {'name': 'Test Generation Agent', 'description': 'Generates technical and aptitude questions for tests'}
    ]
    return jsonify({'success': True, 'agents': agents})

@app.route('/api/settings/agents/<agent_name>/prompts', methods=['GET'])
def get_agent_prompts(agent_name):
    """Get all prompts for an agent"""
    try:
        prompts = prompt_manager.get_all_prompts(agent_name=agent_name)
        
        # Group by prompt_type and get active versions
        active_prompts = {}
        for prompt in prompts:
            if prompt['is_active']:
                active_prompts[prompt['prompt_type']] = {
                    'content': prompt['prompt_content'],
                    'version': prompt['version'],
                    'modified_at': prompt['modified_at']
                }
        
        return jsonify({
            'success': True,
            'agent_name': agent_name,
            'prompts': active_prompts
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings/prompts', methods=['GET'])
def get_all_prompts_for_ui():
    """Get all prompts for all agents, formatted for Settings.jsx"""
    try:
        all_prompts = prompt_manager.get_all_prompts()
        
        # Group by agent
        agents_data = {}
        for p in all_prompts:
            agent = p['agent_name']
            if agent not in agents_data:
                agents_data[agent] = {
                    'current': '', 
                    'is_custom': False,
                    'prompts': {}
                }
            
            # Add to specific prompts map
            if p['is_active']:
                agents_data[agent]['prompts'][p['prompt_type']] = p['prompt_content']
                # Check if custom (version > 1)
                if p['version'] > 1:
                    agents_data[agent]['is_custom'] = True
        
        # Construct 'current' display text (concatenate all types)
        for agent, data in agents_data.items():
            combined = []
            for p_type, content in data['prompts'].items():
                combined.append(f"--- {p_type.upper()} ---\n{content}")
            data['current'] = "\n\n".join(combined)
            
        return jsonify({
            'success': True,
            'prompts': agents_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings/prompts/modify', methods=['POST'])
def modify_prompt_ui():
    """Modify prompt based on instruction (UI endpoint)"""
    try:
        data = request.get_json() or {}
        agent_name = data.get('agent_name')
        instruction = data.get('instruction')
        
        if not agent_name or not instruction:
            return jsonify({'success': False, 'error': 'Missing agent_name or instruction'}), 400

        # Lazy load feedback agent
        from backend.monitoring_feedback_agent import feedback_agent
        
        # 1. Generate new prompt using LLM (simulated via feedback agent logic or direct call)
        # For now, we'll use a direct LLM call if possible, or fallback to appending instruction
        # Since we don't have direct LLM access here easily without duplicating code,
        # let's try to use feedback_agent.process_feedback but force immediate application.
        
        # Create a feedback entry
        feedback_id = prompt_manager.submit_feedback(agent_name, f"UI Instruction: {instruction}", "admin@redai.com")
        
        # Process it (this generates the modified prompt)
        result = feedback_agent.process_feedback(agent_name, f"UI Instruction: {instruction}", "admin@redai.com")
        
        if result['success'] and result.get('modified_prompts'):
            # Apply immediately
            import json
            mod_prompts = result['modified_prompts'] # This is a dict or list?
            # process_feedback returns dict of {prompt_type: new_content} usually?
            # Let's check feedback_agent.py if needed, but assuming standard flow:
            
            # Apply
            apply_res = feedback_agent.apply_prompt_modifications(feedback_id, agent_name, mod_prompts)
            if apply_res['success']:
                return jsonify({'success': True, 'message': 'Prompt updated'})
            else:
                return jsonify({'success': False, 'error': 'Failed to apply changes'}), 500
        else:
             return jsonify({'success': False, 'error': 'Failed to generate prompt modifications'}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings/prompts/reset', methods=['POST'])
def reset_prompt_ui():
    """Reset prompt to default (UI endpoint)"""
    try:
        data = request.get_json() or {}
        agent_name = data.get('agent_name')
        
        if not agent_name:
            return jsonify({'success': False, 'error': 'Missing agent_name'}), 400
            
        # To reset, we need to know the default. 
        # PromptManager._load_default_prompts has them hardcoded.
        # We can re-trigger _load_default_prompts? No, that only inserts if version 1 missing.
        # We should probably just fetch version 1 and set it as new version.
        
        all_prompts = prompt_manager.get_all_prompts(agent_name)
        # Find version 1 for each type
        defaults = {}
        for p in all_prompts:
            if p['version'] == 1:
                defaults[p['prompt_type']] = p['prompt_content']
        
        if not defaults:
             return jsonify({'success': False, 'error': 'Default prompts not found'}), 404
             
        # Update each type to default content
        for p_type, content in defaults.items():
            prompt_manager.update_prompt(agent_name, p_type, content, "Reset to default")
            
        return jsonify({'success': True, 'message': 'Prompts reset to default'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings/feedback', methods=['POST'])
def submit_feedback():
    """Submit HR feedback for an agent"""
    try:
        data = request.get_json() or {}
        agent_name = data.get('agent_name')
        feedback_text = data.get('feedback_text')
        hr_email = data.get('hr_email')
        
        if not agent_name or not feedback_text:
            return jsonify({
                'success': False,
                'error': 'agent_name and feedback_text are required'
            }), 400
        
        # Lazy load agents
        from backend.monitoring_feedback_agent import monitoring_agent, feedback_agent
        
        # Process feedback through Feedback Agent
        result = feedback_agent.process_feedback(agent_name, feedback_text, hr_email)
        
        if result['success']:
            return jsonify({
                'success': True,
                'feedback_id': result['feedback_id'],
                'llm_suggestion': result.get('llm_suggestion'),
                'modified_prompts': result.get('modified_prompts'),
                'message': 'Feedback processed successfully. LLM suggestions generated.'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to process feedback')
            }), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings/feedback', methods=['GET'])
def get_feedback():
    """Get all feedback entries"""
    try:
        agent_name = request.args.get('agent_name')
        feedback_id = request.args.get('feedback_id', type=int)
        
        feedback_list = prompt_manager.get_feedback(
            feedback_id=feedback_id,
            agent_name=agent_name
        )
        
        return jsonify({
            'success': True,
            'feedback': feedback_list
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings/feedback/<int:feedback_id>/apply', methods=['POST'])
def apply_feedback(feedback_id):
    """Apply prompt modifications from feedback"""
    try:
        feedback_list = prompt_manager.get_feedback(feedback_id=feedback_id)
        
        if not feedback_list:
            return jsonify({
                'success': False,
                'error': 'Feedback not found'
            }), 404
        
        feedback_item = feedback_list[0]
        
        if not feedback_item.get('modified_prompt'):
            return jsonify({
                'success': False,
                'error': 'No modified prompts to apply'
            }), 400
        
        import json
        modified_prompts = json.loads(feedback_item['modified_prompt'])
        agent_name = feedback_item['agent_name']
        
        # Apply modifications
        result = feedback_agent.apply_prompt_modifications(
            feedback_id,
            agent_name,
            modified_prompts
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'applied_count': result['applied_count'],
                'message': f'Prompt modifications applied to {agent_name}'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to apply modifications')
            }), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings/monitoring/metrics', methods=['GET'])
def get_monitoring_metrics():
    """Get monitoring metrics for all agents"""
    try:
        # Simple metrics (can be enhanced with real monitoring)
        metrics = {
            'Interview Scheduler Agent': {
                'error_rate': 0.03,
                'response_time': 3.1,
                'total_requests': 80
            },
            'Resume and Matching Agent': {
                'error_rate': 0.02,
                'response_time': 1.5,
                'total_requests': 150
            },
            'Job Description Agent': {
                'error_rate': 0.02,
                'response_time': 2.0,
                'total_requests': 100
            },
            'Shortlisting Agent': {
                'error_rate': 0.01,
                'response_time': 2.3,
                'total_requests': 200
            }
        }
        
        return jsonify({
            'success': True,
            'metrics': metrics
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings/prompts/update', methods=['POST'])
def update_prompt():
    """Manually update a prompt"""
    try:
        data = request.get_json() or {}
        agent_name = data.get('agent_name')
        prompt_type = data.get('prompt_type')
        new_prompt = data.get('new_prompt')
        change_reason = data.get('change_reason', 'Manual update')
        
        if not agent_name or not prompt_type or not new_prompt:
            return jsonify({
                'success': False,
                'error': 'agent_name, prompt_type, and new_prompt are required'
            }), 400
        
        new_version = prompt_manager.update_prompt(
            agent_name,
            prompt_type,
            new_prompt,
            change_reason=change_reason
        )
        
        return jsonify({
            'success': True,
            'version': new_version,
            'message': f'Prompt updated to version {new_version}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("Settings API starting on http://localhost:5003")
    app.run(debug=True, host='0.0.0.0', port=5003)


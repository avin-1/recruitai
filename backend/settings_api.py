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
from backend.monitoring_feedback_agent import monitoring_agent, feedback_agent

app = Flask(__name__)
CORS(app)

@app.route('/api/settings/agents', methods=['GET'])
def get_agents():
    """Get list of all agents"""
    agents = [
        {'name': 'Interview Scheduler Agent', 'description': 'Schedules interviews based on availability'},
        {'name': 'Resume and Matching Agent', 'description': 'Matches resumes to job descriptions'},
        {'name': 'Job Description Agent', 'description': 'Parses job descriptions from PDFs and extracts structured information'},
        {'name': 'Shortlisting Agent', 'description': 'Evaluates candidate test performance'}
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


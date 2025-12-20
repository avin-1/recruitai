from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import sqlite3
from test_service import TestService
from shortlisting_database import DatabaseManager
# Don't import LLMPerformanceAnalyzer at module level - it loads large models
# import llm_analyzer - will be imported lazily
import datetime
import datetime
import sys
import os
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
# from backend.email_service import EmailService


# Lazy load shortlisting agent to prevent crashes on import
shortlisting_agent = None
def get_shortlisting_agent():
    global shortlisting_agent
    if shortlisting_agent is None:
        try:
            try:
                from agent_orchestrator import shortlisting_agent as agent
                shortlisting_agent = agent
            except ImportError:
                 from backend.agent_orchestrator import shortlisting_agent as agent # Fallback if path still works
                 shortlisting_agent = agent
        except Exception as e:
            print(f"Warning: Failed to load shortlisting agent: {e}")
            print("Notifications will be disabled but system will continue working")
            # Create a dummy agent that doesn't crash
            class DummyAgent:
                def notify(self, *args, **kwargs):
                    pass
                def evaluate_candidate(self, *args, **kwargs):
                    return {'decision': 'UNKNOWN', 'completion_rate': 0, 'reasoning': 'Agent unavailable'}
            shortlisting_agent = DummyAgent()
    return shortlisting_agent

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "allow_headers": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]}})

# Initialize services
test_service = TestService()
db_manager = DatabaseManager()
# email_service = EmailService() # Removed in microservice refactor
# test_gen_agent = TestGenerationAgent() # Moved to lazy load

# Lazy load test generation agent
test_gen_agent = None
def get_test_gen_agent():
    global test_gen_agent
    if test_gen_agent is None:
        try:
            # Import locally to avoid circular imports or startup delays
            from test_agent import TestGenerationAgent
            test_gen_agent = TestGenerationAgent()
        except Exception as e:
            print(f"Warning: Failed to load test generation agent: {e}")
            # Return a dummy agent that fails gracefully
            class DummyTestAgent:
                def generate_questions(self, *args, **kwargs):
                    raise Exception(f"Test Generation Agent unavailable: {e}")
            test_gen_agent = DummyTestAgent()
    return test_gen_agent

# Lazy load LLM analyzer to prevent crashes during Flask reloads
llm_analyzer = None
_llm_analyzer_module = None

def get_llm_analyzer():
    """Lazy load LLM analyzer only when needed - prevents crashes during startup"""
    global llm_analyzer, _llm_analyzer_module
    if llm_analyzer is None:
        try:
            # Import module only when needed
            if _llm_analyzer_module is None:
                from llm_analyzer import LLMPerformanceAnalyzer
                _llm_analyzer_module = LLMPerformanceAnalyzer
            
            # Create analyzer WITHOUT loading model initially (load_model=False)
            # Model will load on first use if needed
            llm_analyzer = _llm_analyzer_module(load_model=False)
        except Exception as e:
            print(f"Warning: Failed to initialize LLM analyzer: {e}")
            print("Falling back to rule-based analysis only")
            import traceback
            traceback.print_exc()
            llm_analyzer = None  # Set to None to indicate failure
    return llm_analyzer

@app.route('/api/tests/problems', methods=['GET'])
def get_problems():
    """Get available problems from Codeforces"""
    try:
        difficulty_min = request.args.get('difficulty_min', type=int)
        difficulty_max = request.args.get('difficulty_max', type=int)
        tags = request.args.getlist('tags')
        
        try:
            get_shortlisting_agent().notify(
                f"🔍 Fetching Codeforces problems (difficulty: {difficulty_min or 'any'}-{difficulty_max or 'any'}, tags: {len(tags)} selected)...",
                'processing',
                reasoning=f"Searching Codeforces problem database with specified filters to find suitable test questions"
            )
        except:
            pass
        
        problems = test_service.get_available_problems(
            difficulty_min=difficulty_min,
            difficulty_max=difficulty_max,
            tags=tags if tags else None
        )
        
        try:
            get_shortlisting_agent().notify(
                f"✅ Found {len(problems)} Codeforces problems matching criteria",
                'success',
                reasoning=f"Retrieved {len(problems)} problems that match the specified difficulty range and tags"
            )
        except:
            pass
        
        return jsonify({
            'success': True,
            'problems': problems
        })
    except Exception as e:
        try:
            get_shortlisting_agent().notify(
                f"❌ Error fetching problems: {str(e)}",
                'warning'
            )
        except:
            pass
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tests/generate-questions', methods=['POST'])
def generate_questions():
    """Generate questions using AI"""
    try:
        data = request.get_json()
        topic = data.get('topic')
        count = data.get('count', 5)
        difficulty = data.get('difficulty', 'medium')
        q_type = data.get('type', 'multiple_choice')
        
        if not topic:
            return jsonify({'success': False, 'error': 'Topic is required'}), 400
            
        questions = get_test_gen_agent().generate_questions(topic, count, difficulty, q_type)
        
        return jsonify({
            'success': True,
            'questions': questions
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tests/chat', methods=['POST'])
def chat_with_agent():
    """Agentic chat endpoint for test management"""
    try:
        data = request.get_json()
        message = data.get('message', '').lower()
        
        response = {
            'success': True,
            'message': "I didn't understand that command.",
            'action': None,
            'data': None
        }

        # Simple intent classification (can be upgraded to LLM)
        if 'create' in message and 'test' in message:
            # Extract name if possible, else ask for it
            # For now, just trigger the UI modal or form
            response['message'] = "I can help you create a test. I've opened the creation form for you."
            response['action'] = 'OPEN_CREATE_TEST'
            
        elif 'generate' in message or 'question' in message:
            # Extract count and topic
            import re
            count_match = re.search(r'(\d+)', message)
            count = int(count_match.group(1)) if count_match else 5
            topic = message.replace('generate', '').replace('questions', '').replace(str(count), '').strip()
            
            if not topic:
                topic = 'general programming'
                
            questions = get_test_gen_agent().generate_questions(topic, count, 'medium', 'multiple_choice')
            response['message'] = f"I've generated {len(questions)} questions about {topic}."
            response['action'] = 'SHOW_GENERATED_QUESTIONS'
            response['data'] = questions
            
        elif 'delete' in message and 'test' in message:
            response['message'] = "Please select the test you want to delete from the list."
            response['action'] = 'SWITCH_TAB_MANAGE'
            
        elif 'list' in message or 'show' in message:
            response['message'] = "Here are the current tests."
            response['action'] = 'SWITCH_TAB_MANAGE'
            
        else:
            # Fallback to general AI chat or help
            response['message'] = "I can help you create tests, generate questions, or manage existing assessments. Try saying 'Create a python test' or 'Generate 5 java questions'."
            
        return jsonify(response)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tests/create', methods=['POST'])
def create_test():
    """Create a new test"""
    try:
        data = request.get_json()
        test_name = data.get('test_name')
        test_description = data.get('test_description', '')
        # 'questions' can now be a list (legacy Codeforces) OR a list of sections (New format)
        questions_data = data.get('questions', []) 
        platform_type = data.get('platform_type', 'codeforces')
        custom_platform_name = data.get('custom_platform_name', None)
        
        if not test_name:
            return jsonify({
                'success': False,
                'error': 'Test name is required'
            }), 400
        
        # Validation logic
        if platform_type == 'codeforces' and not questions_data:
             return jsonify({
                'success': False,
                'error': 'Questions are required for Codeforces tests'
            }), 400
            
        # If platform is custom/internal, questions_data might be sections.
        # We store it as JSON string regardless.
        
        test_id = db_manager.create_test(test_name, test_description, json.dumps(questions_data) if questions_data else '[]', platform_type, custom_platform_name)
        
        try:
            get_shortlisting_agent().notify(
                f"✅ Created test '{test_name}' using {platform_type} platform",
                'success',
                reasoning=f"Test created with platform type: {platform_type}" + (f" ({custom_platform_name})" if custom_platform_name else "")
            )
        except:
            pass
        
        return jsonify({
            'success': True,
            'test_id': test_id,
            'message': 'Test created successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tests/<int:test_id>/send-invitations', methods=['POST'])
def send_test_invitations(test_id):
    """Send test invitations to candidates"""
    try:
        data = request.get_json() or {}
        test_link = data.get('test_link')
        
        # Check if test is archived
        status = db_manager.get_test_status(test_id)
        if status == 'archived':
            return jsonify({
                'success': False,
                'error': 'Cannot send invitations for an archived test'
            }), 400
        
        try:
            get_shortlisting_agent().notify(
                f"📧 Sending test invitations for test {test_id}...",
                'processing',
                reasoning=f"Preparing to send test invitations to all selected candidates via email"
            )
        except:
            pass
        
        # If no test_link provided, use default
        if not test_link:
            test_link = f"http://localhost:3000/test/{test_id}"
        
        results = test_service.send_test_invitations(test_id, test_link)
        
        try:
            get_shortlisting_agent().notify(
                f"✅ Sent {results.get('total_sent', 0)} test invitations successfully",
                'success',
                reasoning=f"Email invitations sent to {results.get('total_sent', 0)} candidates with test link"
            )
        except:
            pass
        
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        try:
            get_shortlisting_agent().notify(
                f"❌ Error sending invitations: {str(e)}",
                'warning'
            )
        except:
            pass
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tests', methods=['GET'])
def get_all_tests():
    """Get all tests"""
    try:
        tests = db_manager.get_all_tests()
        # Format tests to include platform info
        formatted_tests = []
        for test in tests:
            test_dict = {
                'id': test[0],
                'test_name': test[1],
                'test_description': test[2],
                'questions': test[3],
                'created_date': test[4] if len(test) > 4 else None,
                'status': test[5] if len(test) > 5 else 'active',
                'platform_type': test[6] if len(test) > 6 else 'codeforces',
                'custom_platform_name': test[7] if len(test) > 7 else None
            }
            formatted_tests.append(test_dict)
        return jsonify({
            'success': True,
            'tests': formatted_tests
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tests/<int:test_id>/platform', methods=['GET'])
def get_test_platform(test_id):
    """Get platform type for a test"""
    try:
        platform_info = db_manager.get_test_platform(test_id)
        return jsonify({
            'success': True,
            'platform': platform_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tests/<int:test_id>', methods=['DELETE'])
def delete_test(test_id):
    """Archive a test (soft delete) or permanently delete"""
    try:
        permanent = request.args.get('permanent', 'false').lower() == 'true'
        
        if permanent:
            try:
                get_shortlisting_agent().notify(
                    f"🗑️ Permanently deleting test {test_id}...",
                    'processing',
                    reasoning="Removing test and all associated data from database"
                )
            except:
                pass
            
            db_manager.permanently_delete_test(test_id)
            message = 'Test permanently deleted'
        else:
            try:
                get_shortlisting_agent().notify(
                    f"🗑️ Archiving test {test_id}...",
                    'processing'
                )
            except:
                pass
            
            db_manager.archive_test(test_id)
            message = 'Test archived successfully'
        
        try:
            get_shortlisting_agent().notify(
                f"✅ Test {test_id} archived successfully",
                'success',
                reasoning="Test has been soft-deleted (archived) and will no longer appear in active test lists"
            )
        except:
            pass
        
        return jsonify({
            'success': True,
            'message': 'Test archived successfully'
        })
    except Exception as e:
        try:
            get_shortlisting_agent().notify(
                f"❌ Error archiving test: {str(e)}",
                'warning'
            )
        except:
            pass
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tests/<int:test_id>/register', methods=['POST'])
def register_candidate(test_id):
    """Register a candidate for a test"""
    try:
        data = request.get_json()
        candidate_email = data.get('candidate_email')
        codeforces_username = data.get('codeforces_username')
        
        if not candidate_email or not codeforces_username:
            return jsonify({
                'success': False,
                'error': 'Candidate email and Codeforces username are required'
            }), 400
        
        userid_id = test_service.register_candidate(candidate_email, codeforces_username, test_id)
        
        return jsonify({
            'success': True,
            'userid_id': userid_id,
            'message': 'Candidate registered successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tests/<int:test_id>/fetch-results', methods=['POST'])
def fetch_test_results(test_id):
    """Fetch and save test results from Codeforces"""
    try:
        try:
            get_shortlisting_agent().notify(
                f"🔄 Fetching test results from Codeforces for test {test_id}...",
                'processing',
                reasoning=f"Querying Codeforces API to retrieve candidate submission data for test {test_id}"
            )
        except:
            pass  # Continue even if notification fails
        
        results_summary = test_service.fetch_and_save_results(test_id)
        
        try:
            get_shortlisting_agent().notify(
                f"✅ Fetched results: {results_summary.get('total_users', 0)} candidates, {results_summary.get('total_solved', 0)} problems solved",
                'success',
                reasoning=f"Successfully retrieved and processed submission data from Codeforces for all registered candidates"
            )
        except:
            pass  # Continue even if notification fails
        
        return jsonify({
            'success': True,
            'summary': results_summary
        })
    except Exception as e:
        error_msg = str(e)
        try:
            get_shortlisting_agent().notify(
                f"❌ Error fetching results for test {test_id}: {error_msg}",
                'warning'
            )
        except:
            pass  # Continue even if notification fails
        
        import traceback
        print(f"Error in fetch_test_results: {error_msg}")
        print(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@app.route('/api/tests/<int:test_id>/results', methods=['GET'])
def get_test_results(test_id):
    """Get test results"""
    try:
        try:
            get_shortlisting_agent().notify(
                f"📊 Loading test results for test {test_id}...",
                'processing'
            )
        except:
            pass
        
        results = test_service.get_test_results(test_id)
        
        try:
            get_shortlisting_agent().notify(
                f"✅ Loaded results for {len(results)} candidates",
                'success',
                reasoning=f"Retrieved and formatted performance data for {len(results)} candidates who completed the test"
            )
        except:
            pass
        
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        try:
            get_shortlisting_agent().notify(
                f"❌ Error loading results: {str(e)}",
                'warning'
            )
        except:
            pass
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    """Get all AI agent notifications from shortlisting service"""
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from backend.agent_orchestrator import get_notifications as get_notifs
        notifications = get_notifs()
        return jsonify({'success': True, 'notifications': notifications})
    except Exception as e:
        print(f"Error getting notifications: {e}")
        # Return empty list instead of error to prevent crashes
        return jsonify({'success': True, 'notifications': []})

@app.route('/api/notifications/<int:index>/read', methods=['POST'])
def mark_notification_read(index):
    """Mark notification as read"""
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from backend.agent_orchestrator import mark_notification_read as mark_read
        mark_read(index)
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error marking notification read: {e}")
        return jsonify({'success': True})  # Return success to prevent crashes

@app.route('/api/notifications/clear', methods=['POST'])
def clear_notifications():
    """Clear all notifications"""
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from backend.agent_orchestrator import clear_all_notifications
        clear_all_notifications()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error clearing notifications: {e}")
        return jsonify({'success': True})  # Return success to prevent crashes

@app.route('/api/tests/<int:test_id>/questions', methods=['GET'])
def get_test_questions(test_id):
    """Get questions for a specific test"""
    try:
        questions = db_manager.get_test_questions(test_id)
        
        # Get test info
        conn = sqlite3.connect(db_manager.selected_candidates_db)
        cursor = conn.cursor()
        cursor.execute('SELECT test_name, test_description FROM tests WHERE id = ?', (test_id,))
        test_info = cursor.fetchone()
        conn.close()
        
        return jsonify({
            'success': True,
            'questions': questions,
            'test_info': {
                'id': test_id,
                'name': test_info[0] if test_info else f'Test {test_id}',
                'description': test_info[1] if test_info and test_info[1] else 'Technical Assessment Test'
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/candidates', methods=['GET'])
def get_candidates():
    """Get all selected candidates"""
    try:
        candidates = db_manager.get_all_candidates()
        
        return jsonify({
            'success': True,
            'candidates': candidates
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tests/<int:test_id>/candidate/<int:candidate_id>/analysis', methods=['GET'])
def get_candidate_analysis(test_id, candidate_id):
    """Get detailed AI-powered performance analysis for a specific candidate"""
    try:
        report_type = request.args.get('report_type', 'general')
        job_role = request.args.get('job_role', 'Software Engineer')
        
        # Get test questions
        test_questions = db_manager.get_test_questions(test_id)
        
        # Get candidate results
        raw_results = db_manager.get_test_results(test_id)
        
        # Find candidate data
        candidate_data = None
        for row in raw_results:
            if row[0] == candidate_id:  # candidate_id matches u.id (index 0)
                # Unpack 8 columns returned by get_test_results (including tab_switches and time_taken)
                user_id, email, username, question_id, solved, result_data, tab_switches, time_taken = row
                if not candidate_data:
                    candidate_data = {
                        'email': email,
                        'username': username,
                        'questions': {},
                        'total_solved': 0,
                        'total_questions': len(test_questions)
                    }
                
                candidate_data['questions'][question_id] = {
                    'solved': solved,
                    'data': result_data
                }
                
                if solved:
                    candidate_data['total_solved'] += 1
        
        if not candidate_data:
            return jsonify({
                'success': False,
                'error': 'Candidate not found or no results available'
            }), 404
        
        # Fetch real Codeforces data ONLY if test has Codeforces questions
        from codeforces_api import CodeforcesAPI
        cf_api = CodeforcesAPI()
        
        # Check if test has Codeforces questions
        has_codeforces = False
        for q in test_questions:
            if q.get('type') == 'codeforces' or ('contestId' in q and 'index' in q):
                has_codeforces = True
                break
        
        codeforces_data = None
        if has_codeforces:
            codeforces_data = cf_api.get_user_submission_details(candidate_data['username'], test_questions)
        
        # Perform AI analysis with real Codeforces data
        analyzer = get_llm_analyzer()
        if analyzer is None:
            # Create a fallback instance WITHOUT loading model (prevents crashes)
            try:
                from llm_analyzer import LLMPerformanceAnalyzer
                analyzer = LLMPerformanceAnalyzer(load_model=False)
            except Exception as fallback_err:
                print(f"Warning: Could not load LLM analyzer even as fallback: {fallback_err}")
                # Return basic analysis without LLM
                return jsonify({
                    'success': True,
                    'analysis': {
                        'performance_score': candidate_data.get('total_solved', 0) / len(test_questions) * 100 if test_questions else 0,
                        'recommendation': 'NEEDS_MANUAL_REVIEW',
                        'agent_decision': {'decision': 'UNKNOWN', 'completion_rate': 0, 'reasoning': 'Analyzer unavailable'}
                    }
                })
        
        # Use autonomous shortlisting agent
        try:
            shortlisting_decision = get_shortlisting_agent().evaluate_candidate(candidate_data, test_questions)
        except Exception as agent_err:
            print(f"Warning: Shortlisting agent unavailable: {agent_err}")
            shortlisting_decision = {'decision': 'UNKNOWN', 'completion_rate': 0, 'reasoning': 'Agent unavailable'}
        
        # Wrap analysis in try-except to prevent crashes
        try:
            analysis = analyzer.analyze_candidate_performance(candidate_data, test_questions, codeforces_data, report_type=report_type, job_role=job_role)
        except Exception as analysis_err:
            print(f"Error during candidate analysis: {analysis_err}")
            import traceback
            traceback.print_exc()
            # Return basic analysis on error
            analysis = {
                'performance_score': candidate_data.get('total_solved', 0) / len(test_questions) * 100 if test_questions else 0,
                'recommendation': 'NEEDS_MANUAL_REVIEW',
                'reasoning': f'Analysis failed: {str(analysis_err)}'
            }
        
        # Add agent decision to analysis
        analysis['agent_decision'] = shortlisting_decision
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        print(f"Error in get_candidate_analysis endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tests/<int:test_id>/candidate-analysis', methods=['GET'])
def get_all_candidate_analysis(test_id):
    """Get AI-powered analysis for all candidates in a test"""
    try:
        # Get test questions
        test_questions = db_manager.get_test_questions(test_id)
        
        # Get all candidate results using test_service which handles deduplication
        candidates_list = test_service.get_test_results(test_id)
        
        # Convert list to dict keyed by user_key for compatibility
        candidates_data = {}
        for candidate in candidates_list:
            user_key = f"{candidate['email']}_{candidate['username']}"
            candidates_data[user_key] = candidate
        
        # Analyze each candidate with real Codeforces data
        analyses = []
        from codeforces_api import CodeforcesAPI
        cf_api = CodeforcesAPI()
        
        analyzer = get_llm_analyzer()
        if analyzer is None:
            # Create a fallback instance WITHOUT loading model (prevents crashes)
            try:
                from llm_analyzer import LLMPerformanceAnalyzer
                analyzer = LLMPerformanceAnalyzer(load_model=False)
            except Exception as fallback_err:
                print(f"Warning: Could not load LLM analyzer: {fallback_err}")
                # Return basic analyses without LLM
                basic_analyses = []
                for candidate_data in candidates_data.values():
                    basic_analyses.append({
                        'performance_score': candidate_data.get('total_solved', 0) / len(test_questions) * 100 if test_questions else 0,
                        'recommendation': 'NEEDS_MANUAL_REVIEW',
                        'agent_decision': {'decision': 'UNKNOWN', 'completion_rate': 0, 'reasoning': 'Analyzer unavailable'}
                    })
                return jsonify({
                    'success': True,
                    'analyses': basic_analyses
                })
        for candidate_data in candidates_data.values():
            # Fetch real Codeforces data for each candidate
            codeforces_data = cf_api.get_user_submission_details(candidate_data['username'], test_questions)
            
            # Use autonomous shortlisting agent
            try:
                shortlisting_decision = get_shortlisting_agent().evaluate_candidate(candidate_data, test_questions)
            except Exception as agent_err:
                print(f"Warning: Shortlisting agent unavailable: {agent_err}")
                shortlisting_decision = {'decision': 'UNKNOWN', 'completion_rate': 0, 'reasoning': 'Agent unavailable'}
            
            # Wrap analysis in try-except to prevent one failure from stopping all analyses
            try:
                analysis = analyzer.analyze_candidate_performance(candidate_data, test_questions, codeforces_data)
                analysis['agent_decision'] = shortlisting_decision
                analyses.append(analysis)
            except Exception as analysis_err:
                print(f"Error analyzing candidate {candidate_data.get('email', 'unknown')}: {analysis_err}")
                # Add basic analysis for this candidate
                analyses.append({
                    'performance_score': candidate_data.get('total_solved', 0) / len(test_questions) * 100 if test_questions else 0,
                    'recommendation': 'NEEDS_MANUAL_REVIEW',
                    'agent_decision': shortlisting_decision,
                    'reasoning': f'Analysis failed: {str(analysis_err)}'
                })
        
        return jsonify({
            'success': True,
            'analyses': analyses
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# New endpoint to select candidate for interview
@app.route('/api/tests/<int:test_id>/select-candidate', methods=['POST'])
def select_candidate_for_interview(test_id):
    """Autonomous agent saves approved candidate for interview"""
    try:
        data = request.get_json() or {}
        candidate_email = data.get('candidate_email')
        codeforces_username = data.get('codeforces_username')
        
        if not candidate_email:
            return jsonify({
                'success': False,
                'error': 'candidate_email is required'
            }), 400
        
        try:
            get_shortlisting_agent().notify(
                f"✅ Selected {candidate_email} for interview (Test {test_id})",
                'success',
                reasoning=f"Based on performance evaluation, candidate meets shortlisting criteria and will proceed to interview stage"
            )
        except:
            pass
        
        candidate_id = db_manager.save_interview_candidate(candidate_email, codeforces_username, test_id)
        
        # Send interview selection email
        try:
            # Get test name
            conn = sqlite3.connect(db_manager.selected_candidates_db)
            cursor = conn.cursor()
            cursor.execute('SELECT test_name FROM tests WHERE id = ?', (test_id,))
            row = cursor.fetchone()
            conn.close()
            
            test_name = row[0] if row else f"Test {test_id}"
            
            # Send email
            email_service.send_interview_selection_email(candidate_email, codeforces_username or "Candidate", test_name)
            
            try:
                get_shortlisting_agent().notify(
                    f"📧 Sent interview selection email to {candidate_email}",
                    'success'
                )
            except:
                pass
        except Exception as e:
            print(f"Error sending interview email: {e}")

        return jsonify({
            'success': True,
            'candidate_id': candidate_id
        })
    except Exception as e:
        try:
            get_shortlisting_agent().notify(
                f"❌ Failed to select candidate: {str(e)}",
                'warning'
            )
        except:
            pass
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Interview endpoints
@app.route('/api/interviews/candidates', methods=['GET'])
def get_interview_candidates():
    try:
        emails = db_manager.get_interview_candidate_emails()
        return jsonify({'success': True, 'emails': emails})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/interviews/candidates-with-schedules', methods=['GET'])
def get_interview_candidates_with_schedules():
    try:
        candidates = db_manager.get_interview_candidates_details()
        return jsonify({'success': True, 'candidates': candidates})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/interviews/reject-candidate', methods=['POST'])
def reject_interview_candidate():
    try:
        data = request.get_json() or {}
        candidate_email = data.get('candidate_email')
        if not candidate_email:
            return jsonify({'success': False, 'error': 'candidate_email is required'}), 400
            
        success = db_manager.reject_candidate(candidate_email)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/interviews/select-candidate', methods=['POST'])
def select_interview_candidate():
    try:
        data = request.get_json() or {}
        candidate_email = data.get('candidate_email')
        if not candidate_email:
            return jsonify({'success': False, 'error': 'candidate_email is required'}), 400
            
        success = db_manager.select_candidate(candidate_email)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to select candidate'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Lazy load interview agent
interview_agent = None
def get_interview_agent():
    global interview_agent
    if interview_agent is None:
        try:
            from interview_agent import InterviewChatAgent
            interview_agent = InterviewChatAgent()
        except Exception as e:
            print(f"Failed to load InterviewChatAgent: {e}")
            return None
    return interview_agent

@app.route('/api/interviews/chat', methods=['POST'])
def interview_chat():
    """AI chat to suggest interview slots using LLM"""
    try:
        data = request.get_json() or {}
        message = data.get('message', '')
        
        agent = get_interview_agent()
        if not agent:
            return jsonify({
                'success': True, 
                'response': "I'm currently offline (Agent unavailable).", 
                'slots': []
            })
            
        result = agent.process_chat(message, data)
        
        return jsonify({
            'success': True,
            'response': result.get('response'),
            'slots': result.get('slots', [])
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/interviews/availability', methods=['POST'])
def get_hr_availability():
    """Placeholder: Would call Google Calendar API to fetch next 5 days availability"""
    try:
        data = request.get_json() or {}
        hr_email = data.get('hr_email')
        # Placeholder availability blocks (ISO strings)
        today = datetime.datetime.utcnow().date()
        slots = []
        for i in range(5):
            day = today + datetime.timedelta(days=i+1)
            start = datetime.datetime(day.year, day.month, day.day, 10, 0)
            end = start + datetime.timedelta(minutes=30)
            slots.append({
                'start': start.isoformat() + 'Z',
                'end': end.isoformat() + 'Z'
            })
        return jsonify({'success': True, 'slots': slots})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/interviews/propose', methods=['POST'])
def propose_interview_slots():
    """Send HR availability to LLM (placeholder) and return suggested slots"""
    try:
        data = request.get_json() or {}
        availability = data.get('availability', [])
        # Placeholder: simply echo availability as proposed suggestions
        return jsonify({'success': True, 'proposals': availability[:5]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/interviews/schedule', methods=['POST'])
def schedule_interviews():
    """Schedule selected proposal for all interview candidates and email them (placeholder send & meet link)"""
    try:
        data = request.get_json() or {}
        start = data.get('start')
        end = data.get('end')
        hr_email = data.get('hr_email')
        if not start or not end:
            return jsonify({'success': False, 'error': 'start and end are required'}), 400
        emails = db_manager.get_interview_candidate_emails()
        meeting_link = f"https://meet.google.com/{'xyz-abcw-pqr'}"
        scheduled = []
        for email in emails:
            schedule_id = db_manager.save_interview_schedule(email, start, end, hr_email, meeting_link)
            scheduled.append({'email': email, 'schedule_id': schedule_id})
        # Placeholder: send emails via existing email service if desired
        return jsonify({'success': True, 'scheduled': scheduled, 'meeting_link': meeting_link})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tests/<int:test_id>/submit', methods=['POST'])
def submit_test(test_id):
    """Submit test answers (manual questions)"""
    try:
        data = request.get_json()
        candidate_email = data.get('candidate_email')
        answers = data.get('answers', {})
        
        if not candidate_email:
            return jsonify({'success': False, 'error': 'Candidate email is required'}), 400
            
        # Get userid_id
        conn = sqlite3.connect(db_manager.userids_db)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM userids WHERE candidate_email = ? AND test_id = ?', (candidate_email, test_id))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'success': False, 'error': 'Candidate not registered for this test'}), 404
            
        userid_id = row[0]
        
        # Save metrics
        tab_switches = data.get('tab_switches', 0)
        time_taken = data.get('time_taken', 0)
        
        db_manager.update_candidate_metrics(userid_id, tab_switches, time_taken)
        
        # Format results for saving
        formatted_results = {}
        for q_id, answer in answers.items():
            formatted_results[q_id] = {
                'solved': True, # Mark as solved/submitted
                'answer': answer,
                'type': 'manual',
                'submission_time': datetime.datetime.utcnow().isoformat()
            }
            
        # Save results
        db_manager.save_test_results(userid_id, test_id, formatted_results)
        
        try:
            get_shortlisting_agent().notify(
                f"✅ Candidate {candidate_email} submitted test {test_id} (Tabs: {tab_switches}, Time: {time_taken}s)",
                'success',
                reasoning=f"Received and saved answers for {len(answers)} questions"
            )
        except:
            pass
            
        return jsonify({
            'success': True,
            'message': 'Test submitted successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tests/<int:test_id>/candidates/delete', methods=['POST'])
def delete_candidate_result(test_id):
    """Delete a candidate's result and registration"""
    try:
        data = request.get_json()
        candidate_email = data.get('candidate_email')
        
        if not candidate_email:
            return jsonify({'success': False, 'error': 'Candidate email is required'}), 400
            
        success = db_manager.delete_candidate_result(test_id, candidate_email)
        
        if success:
            return jsonify({'success': True, 'message': 'Candidate removed successfully'})
        else:
            return jsonify({'success': False, 'error': 'Candidate not found or could not be removed'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



# --- Prompt Settings Endpoints ---

from prompt_manager import PromptManager
prompt_manager = PromptManager()

@app.route('/api/settings/prompts', methods=['GET'])
def get_prompts():
    """Get current prompts for all agents"""
    agents = ["Test Generation Agent", "Interview Chat Agent", "Job Description Agent"]
    prompts = {}
    for agent in agents:
        prompts[agent] = {
            "current": prompt_manager.get_prompt(agent),
            "default": prompt_manager.get_default_prompt(agent),
            "is_custom": prompt_manager.get_prompt(agent) != prompt_manager.get_default_prompt(agent)
        }
    return jsonify({'success': True, 'prompts': prompts})

@app.route('/api/settings/prompts/modify', methods=['POST'])
def modify_prompt():
    """Modify an agent's prompt using LLM"""
    data = request.get_json()
    agent_name = data.get('agent_name')
    instruction = data.get('instruction')
    
    if not agent_name or not instruction:
        return jsonify({'success': False, 'error': 'Missing agent_name or instruction'}), 400
        
    try:
        new_prompt = prompt_manager.modify_prompt_with_llm(agent_name, instruction)
        return jsonify({'success': True, 'new_prompt': new_prompt})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings/prompts/reset', methods=['POST'])
def reset_prompt():
    """Reset an agent's prompt to default"""
    data = request.get_json()
    agent_name = data.get('agent_name')
    
    if not agent_name:
        return jsonify({'success': False, 'error': 'Missing agent_name'}), 400
        
    try:
        prompt_manager.reset_prompt(agent_name)
        return jsonify({'success': True, 'prompt': prompt_manager.get_default_prompt(agent_name)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port, debug=False)

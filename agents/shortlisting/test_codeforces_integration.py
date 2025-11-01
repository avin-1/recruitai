#!/usr/bin/env python3
"""
Test script for Codeforces API integration
"""

from codeforces_api import CodeforcesAPI
from llm_analyzer import LLMPerformanceAnalyzer

def test_codeforces_integration():
    """Test the Codeforces API integration"""
    
    print("Testing Codeforces API Integration...")
    print("=" * 50)
    
    try:
        # Initialize Codeforces API
        cf_api = CodeforcesAPI()
        
        # Test with the provided example
        test_questions = [
            {
                'contestId': 2134,
                'index': 'A',
                'name': 'Painting With Two Colors',
                'rating': 800,
                'tags': ['constructive algorithms', 'implementation', 'math']
            }
        ]
        
        print("Fetching submission details for user 'lavy10'...")
        result = cf_api.get_user_submission_details('lavy10', test_questions)
        
        print(f"API Status: {result.get('status', 'FAILED')}")
        print(f"Username: {result.get('username', 'N/A')}")
        print(f"Total Submissions: {result.get('total_submissions', 0)}")
        print(f"Relevant Submissions: {len(result.get('relevant_submissions', []))}")
        
        if result.get('status') == 'OK':
            print("\nRelevant Submissions Details:")
            for i, submission in enumerate(result.get('relevant_submissions', []), 1):
                print(f"\nSubmission {i}:")
                print(f"  Problem: {submission.get('contest_id', '')}{submission.get('problem_index', '')}")
                print(f"  Name: {submission.get('problem_name', 'Unknown')}")
                print(f"  Rating: {submission.get('problem_rating', 'Unknown')}")
                print(f"  Verdict: {submission.get('verdict', 'Unknown')}")
                print(f"  Language: {submission.get('programming_language', 'Unknown')}")
                print(f"  Time: {submission.get('time_consumed', 0)}ms")
                print(f"  Memory: {submission.get('memory_consumed', 0)} bytes")
        
        # Test LLM analyzer with real data
        print("\n" + "=" * 50)
        print("Testing LLM Analyzer with Codeforces Data...")
        
        candidate_data = {
            'email': 'test@example.com',
            'username': 'lavy10',
            'questions': {
                '2134A': {'solved': True, 'data': 'AC'}
            },
            'total_solved': 1,
            'total_questions': 1
        }
        
        analyzer = LLMPerformanceAnalyzer()
        analysis = analyzer.analyze_candidate_performance(candidate_data, test_questions, result)
        
        print(f"Performance Score: {analysis['performance_score']}/100")
        print(f"Performance Level: {analysis['performance_level']}")
        print(f"Completion Rate: {analysis['candidate_info']['completion_rate']}%")
        
        if analysis.get('codeforces_data'):
            cf_data = analysis['codeforces_data']
            print(f"Codeforces Success Rate: {cf_data.get('success_rate', 0)}%")
            print(f"Languages Used: {', '.join(cf_data.get('languages_used', []))}")
            print(f"Average Time: {cf_data.get('average_time', 0)}ms")
        
        print("\nInsights:")
        for insight in analysis.get('insights', []):
            print(f"- {insight}")
        
        print("\nStrengths:")
        for strength in analysis.get('strengths', []):
            print(f"- {strength}")
        
        print("\nAreas for Improvement:")
        for area in analysis.get('areas_for_improvement', []):
            print(f"- {area}")
        
        print("\n✅ Codeforces API integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing Codeforces integration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_codeforces_integration()

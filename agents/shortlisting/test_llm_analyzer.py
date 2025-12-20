#!/usr/bin/env python3
"""
Test script for the LLM Performance Analyzer
"""

from llm_analyzer import LLMPerformanceAnalyzer

def test_llm_analyzer():
    """Test the LLM analyzer with sample data"""
    
    # Sample candidate data
    candidate_data = {
        'email': 'test@example.com',
        'username': 'testuser',
        'questions': {
            '1234A': {'solved': True, 'data': 'AC'},
            '1234B': {'solved': False, 'data': 'WA'},
            '1234C': {'solved': True, 'data': 'AC'},
        },
        'total_solved': 2,
        'total_questions': 3
    }
    
    # Sample test questions
    test_questions = [
        {
            'contestId': 1234,
            'index': 'A',
            'name': 'Problem A',
            'rating': 1000,
            'tags': ['implementation', 'math']
        },
        {
            'contestId': 1234,
            'index': 'B',
            'name': 'Problem B',
            'rating': 1500,
            'tags': ['greedy', 'sorting']
        },
        {
            'contestId': 1234,
            'index': 'C',
            'name': 'Problem C',
            'rating': 2000,
            'tags': ['dp', 'graphs']
        }
    ]
    
    print("Testing LLM Performance Analyzer...")
    print("=" * 50)
    
    try:
        # Initialize analyzer
        analyzer = LLMPerformanceAnalyzer()
        
        # Perform analysis
        analysis = analyzer.analyze_candidate_performance(candidate_data, test_questions)
        
        print("Analysis Results:")
        print("-" * 30)
        print(f"Performance Score: {analysis['performance_score']}/100")
        print(f"Performance Level: {analysis['performance_level']}")
        print(f"Completion Rate: {analysis['candidate_info']['completion_rate']}%")
        print(f"Problems Solved: {analysis['candidate_info']['solved_questions']}/{analysis['candidate_info']['total_questions']}")
        
        print("\nInsights:")
        for insight in analysis['insights']:
            print(f"- {insight}")
        
        print("\nStrengths:")
        for strength in analysis['strengths']:
            print(f"- {strength}")
        
        print("\nAreas for Improvement:")
        for area in analysis['areas_for_improvement']:
            print(f"- {area}")
        
        print("\nRecommendations:")
        for rec in analysis['recommendations']:
            print(f"- {rec}")
        
        print("\nDifficulty Analysis:")
        for difficulty, stats in analysis['difficulty_analysis'].items():
            print(f"{difficulty.capitalize()}: {stats['solved']}/{stats['total']} ({stats['percentage']}%)")
        
        print("\n✅ LLM Analyzer test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing LLM analyzer: {e}")
        print("This is expected if the model is not available - the analyzer will fall back to rule-based analysis.")

if __name__ == "__main__":
    test_llm_analyzer()

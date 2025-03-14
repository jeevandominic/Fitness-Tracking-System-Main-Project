import numpy as np
from sklearn.tree import DecisionTreeClassifier
from typing import Dict, List, Tuple
import joblib
import os

class WellnessSuggestionGenerator:
    """Generate personalized wellness suggestions based on mental fitness predictions."""
    
    def __init__(self):
        self.suggestion_categories = {
            'mental_fitness': {
                'title': 'Mental Fitness & Focus Enhancement',
                'suggestions': [
                    'Start with 10-15 minutes of daily meditation to improve focus and mental clarity',
                    'Practice mindfulness exercises during daily activities',
                    'Try brain-training games or puzzles for 15-20 minutes daily',
                    'Take regular short breaks during work using the Pomodoro Technique',
                    'Practice visualization exercises before important tasks',
                    'Create a structured daily routine with clear goals',
                    'Use memory enhancement techniques like mnemonics'
                ]
            },
            'stress_management': {
                'title': 'Stress Management',
                'suggestions': [
                    'Practice deep breathing exercises 3 times daily',
                    'Try progressive muscle relaxation before bed',
                    'Include 20-30 minutes of light yoga or stretching daily',
                    'Take short walks in nature when feeling overwhelmed',
                    'Practice mindful meditation before stressful situations',
                    'Use aromatherapy with calming scents',
                    'Keep a stress diary to identify triggers'
                ]
            },
            'social_engagement': {
                'title': 'Social Engagement Activities',
                'suggestions': [
                    'Join group fitness classes or sports teams',
                    'Participate in community wellness events',
                    'Consider finding a workout buddy or joining fitness communities',
                    'Attend local fitness meetups or workshops',
                    'Share your fitness journey on social media',
                    'Join online fitness communities',
                    'Organize group activities with friends'
                ]
            },
            'mood_enhancement': {
                'title': 'Mood Enhancement Activities',
                'suggestions': [
                    'Engage in 30 minutes of aerobic exercise daily',
                    'Practice gratitude journaling before bed',
                    'Try mood-boosting activities like dancing or swimming',
                    'Maintain a regular sleep schedule',
                    'Expose yourself to natural sunlight daily',
                    'Listen to uplifting music while exercising',
                    'Practice positive affirmations'
                ]
            },
            'confidence_building': {
                'title': 'Confidence Building',
                'suggestions': [
                    'Set and achieve small daily fitness goals',
                    'Track your progress and celebrate small wins',
                    'Try strength training exercises 2-3 times per week',
                    'Learn new workout techniques gradually',
                    'Share your achievements with others',
                    'Take progress photos to visualize changes',
                    'Join confidence-building workshops'
                ]
            },
            'cognitive_enhancement': {
                'title': 'Cognitive Enhancement',
                'suggestions': [
                    'Practice memory exercises daily',
                    'Learn a new skill or hobby',
                    'Read for 30 minutes before bed',
                    'Try crossword puzzles or sudoku',
                    'Learn a new language',
                    'Practice chess or strategic games',
                    'Take online courses in interesting subjects'
                ]
            }
        }
        
        # Initialize the priority classifier
        self.priority_classifier = self._initialize_priority_classifier()

    def _initialize_priority_classifier(self) -> DecisionTreeClassifier:
        """Initialize and train the priority classifier."""
        classifier = DecisionTreeClassifier(random_state=42)
        
        # Training data: [mental_fitness_score, stress_score, depression_score, anxiety_score]
        X = np.array([
            [0.2, 0.8, 0.7, 0.6],  # High priority example
            [0.3, 0.7, 0.6, 0.5],  # High priority example
            [0.5, 0.5, 0.4, 0.3],  # Medium priority example
            [0.6, 0.4, 0.3, 0.2],  # Medium priority example
            [0.8, 0.2, 0.2, 0.1],  # Low priority example
            [0.9, 0.1, 0.1, 0.1],  # Low priority example
        ])
        
        # Priority labels: 0 = low, 1 = medium, 2 = high
        y = np.array([2, 2, 1, 1, 0, 0])
        
        # Train the classifier
        classifier.fit(X, y)
        return classifier

    def _convert_percentage_to_float(self, value: str) -> float:
        """Convert percentage string to float."""
        try:
            return float(value.rstrip('%')) / 100
        except (ValueError, AttributeError):
            return 0.0

    def _get_priority(self, metrics: Dict[str, float]) -> int:
        """Determine suggestion priority based on metrics."""
        features = np.array([[
            1 - metrics.get('mental_fitness_score', 0),  # Inverse of mental fitness
            metrics.get('stress_score', 0),
            metrics.get('depression_score', 0),
            metrics.get('anxiety_score', 0)
        ]])
        return self.priority_classifier.predict(features)[0]

    def generate_suggestions(self, predictions: Dict[str, str]) -> List[Dict[str, any]]:
        """Generate personalized suggestions based on prediction results."""
        suggestions = []
        
        # Convert prediction values to normalized scores
        metrics = {
            'mental_fitness_score': 1.0 if predictions['Mental_Fitness_Level'] == 'High' else 
                                  0.5 if predictions['Mental_Fitness_Level'] == 'Medium' else 0.2,
            'stress_score': 1.0 if predictions['Stress_Level'] == 'High' else 
                          0.5 if predictions['Stress_Level'] == 'Medium' else 0.2,
            'social_score': self._convert_percentage_to_float(predictions['Social_Engagement_Score']),
            'depression_score': self._convert_percentage_to_float(predictions['Depression_Score']),
            'anxiety_score': self._convert_percentage_to_float(predictions['Anxiety_Score']),
            'confidence_score': 1.0 if predictions['Confidence_Level'] == 'High' else 
                              0.5 if predictions['Confidence_Level'] == 'Medium' else 0.2,
            'cleverness_score': self._convert_percentage_to_float(predictions['Cleverness_Score']),
            'focus_score': 1.0 if predictions['Focus_Level'] == 'High' else 
                         0.5 if predictions['Focus_Level'] == 'Medium' else 0.2
        }
        
        # Generate suggestions based on conditions
        if metrics['mental_fitness_score'] < 0.7 or metrics['focus_score'] < 0.7:
            priority = self._get_priority(metrics)
            suggestions.append({
                'category': 'mental_fitness',
                'title': self.suggestion_categories['mental_fitness']['title'],
                'suggestions': self._get_prioritized_suggestions(
                    self.suggestion_categories['mental_fitness']['suggestions'],
                    priority
                )
            })
        
        if metrics['stress_score'] > 0.3:
            priority = self._get_priority(metrics)
            suggestions.append({
                'category': 'stress_management',
                'title': self.suggestion_categories['stress_management']['title'],
                'suggestions': self._get_prioritized_suggestions(
                    self.suggestion_categories['stress_management']['suggestions'],
                    priority
                )
            })
        
        if metrics['social_score'] < 0.7:
            priority = self._get_priority(metrics)
            suggestions.append({
                'category': 'social_engagement',
                'title': self.suggestion_categories['social_engagement']['title'],
                'suggestions': self._get_prioritized_suggestions(
                    self.suggestion_categories['social_engagement']['suggestions'],
                    priority
                )
            })
        
        if metrics['depression_score'] > 0.3 or metrics['anxiety_score'] > 0.2:
            priority = self._get_priority(metrics)
            suggestions.append({
                'category': 'mood_enhancement',
                'title': self.suggestion_categories['mood_enhancement']['title'],
                'suggestions': self._get_prioritized_suggestions(
                    self.suggestion_categories['mood_enhancement']['suggestions'],
                    priority
                )
            })
        
        if metrics['confidence_score'] < 0.7:
            priority = self._get_priority(metrics)
            suggestions.append({
                'category': 'confidence_building',
                'title': self.suggestion_categories['confidence_building']['title'],
                'suggestions': self._get_prioritized_suggestions(
                    self.suggestion_categories['confidence_building']['suggestions'],
                    priority
                )
            })
        
        if metrics['cleverness_score'] < 0.6:
            priority = self._get_priority(metrics)
            suggestions.append({
                'category': 'cognitive_enhancement',
                'title': self.suggestion_categories['cognitive_enhancement']['title'],
                'suggestions': self._get_prioritized_suggestions(
                    self.suggestion_categories['cognitive_enhancement']['suggestions'],
                    priority
                )
            })
        
        return suggestions

    def _get_prioritized_suggestions(self, suggestions: List[str], priority: int) -> List[Dict[str, str]]:
        """Prioritize suggestions based on importance."""
        prioritized = []
        for i, suggestion in enumerate(suggestions):
            if i < 2 and priority == 2:  # High priority for first 2 if priority is high
                prioritized.append({'text': suggestion, 'priority': 'high'})
            elif i < 3 and priority == 1:  # Medium priority for first 3 if priority is medium
                prioritized.append({'text': suggestion, 'priority': 'medium'})
            else:
                prioritized.append({'text': suggestion, 'priority': 'low'})
        return prioritized 
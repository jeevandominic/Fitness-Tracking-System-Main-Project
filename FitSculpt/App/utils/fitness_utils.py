from datetime import datetime, timedelta
from .models import Workout, Nutrition, Client

def get_weekly_summary(client_id):
    # Get the current date and the date one week ago
    today = datetime.now()
    one_week_ago = today - timedelta(days=7)

    # Fetch workouts and nutrition for the past week
    workouts = Workout.objects.filter(client_id=client_id, completed=True, date__gte=one_week_ago)
    nutrition = Nutrition.objects.filter(client_id=client_id, completed=True, date__gte=one_week_ago)

    # Check if all workouts and nutrition are completed
    all_workouts_completed = workouts.count() == Workout.objects.count()  # Adjust this logic as needed
    all_nutrition_completed = nutrition.count() == Nutrition.objects.count()  # Adjust this logic as needed

    # Determine fitness level and diet quality
    physical_fitness_level = 'High' if all_workouts_completed else 'Medium' if workouts.count() > 0 else 'Low'
    diet_quality = 'Good' if all_nutrition_completed else 'Average' if nutrition.count() > 0 else 'Poor'

    return physical_fitness_level, diet_quality 
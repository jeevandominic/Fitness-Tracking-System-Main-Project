import re
from typing import Dict, List
import random

class FitnessChatbot:
    def __init__(self):
        self.knowledge_base = {
            # Specific Body Part Workouts
            'chest|pecs|bench': {
                'exercises': [
                    "Chest exercises:\n1. Push-ups (3 sets x 12-15 reps)\n2. Bench Press (4 sets x 8-12 reps)\n3. Dumbbell Flyes (3 sets x 12 reps)\n4. Incline Press (3 sets x 10-12 reps)\n5. Decline Push-ups (3 sets x max reps)",
                    "Chest workout routine:\n1. Flat Bench Press\n2. Incline Dumbbell Press\n3. Cable Flyes\n4. Dips\n5. Push-ups\nDo 3-4 sets of each, 8-12 reps"
                ],
                'home': [
                    "Home chest workout:\n1. Regular Push-ups\n2. Diamond Push-ups\n3. Wide Push-ups\n4. Decline Push-ups\n5. Resistance Band Press\nEach: 3 sets till failure"
                ]
            },
            
            'back|lats|pullup': {
                'exercises': [
                    "Back exercises:\n1. Pull-ups/Assisted Pull-ups (3 sets x max reps)\n2. Bent-over Rows (4 sets x 12 reps)\n3. Lat Pulldowns (3 sets x 12-15 reps)\n4. Face Pulls (3 sets x 15 reps)\n5. Deadlifts (4 sets x 8-10 reps)",
                    "Back workout split:\nDay 1 - Width:\n1. Pull-ups\n2. Lat Pulldowns\n3. Single-arm Rows\nDay 2 - Thickness:\n1. Deadlifts\n2. T-Bar Rows\n3. Face Pulls"
                ]
            },

            'biceps|arms|curl': {
                'exercises': [
                    "Biceps workout:\n1. Barbell Curls (4 sets x 12 reps)\n2. Hammer Curls (3 sets x 12 each arm)\n3. Incline Curls (3 sets x 12 reps)\n4. Preacher Curls (3 sets x 10 reps)\n5. Cable Curls (3 sets x 15 reps)",
                    "Biceps variations:\n1. Standing Curls\n2. Seated Incline Curls\n3. Concentration Curls\n4. Spider Curls\n5. 21s\nRotate these exercises, 3-4 sets each"
                ]
            },

            'triceps|pushdown': {
                'exercises': [
                    "Triceps routine:\n1. Close-grip Bench Press (4 sets x 12)\n2. Tricep Pushdowns (3 sets x 15)\n3. Overhead Extensions (3 sets x 12)\n4. Diamond Push-ups (3 sets x max)\n5. Dips (3 sets x failure)",
                    "Triceps workout:\n1. Rope Pushdowns\n2. Skull Crushers\n3. Single-arm Extensions\n4. Bench Dips\nDo 3-4 sets, 12-15 reps each"
                ]
            },

            'shoulder|deltoid|press': {
                'exercises': [
                    "Shoulder exercises:\n1. Military Press (4 sets x 8-10)\n2. Lateral Raises (4 sets x 12-15)\n3. Front Raises (3 sets x 12)\n4. Rear Delt Flyes (3 sets x 15)\n5. Upright Rows (3 sets x 12)",
                    "Complete shoulder workout:\nAnterior Deltoid:\n- Military Press\n- Front Raises\nLateral Deltoid:\n- Lateral Raises\n- Upright Rows\nPosterior Deltoid:\n- Face Pulls\n- Reverse Flyes"
                ]
            },

            'legs|quads|hamstring': {
                'exercises': [
                    "Leg day routine:\n1. Squats (5 sets x 8-12)\n2. Romanian Deadlifts (4 sets x 10-12)\n3. Leg Press (4 sets x 12-15)\n4. Lunges (3 sets x 12 each)\n5. Calf Raises (4 sets x 20)",
                    "Leg split workout:\nQuads Focus:\n1. Front Squats\n2. Leg Extensions\n3. Walking Lunges\nHamstrings Focus:\n1. Romanian Deadlifts\n2. Leg Curls\n3. Good Mornings"
                ]
            },

            # Diet Categories
            'diet|nutrition|meal': {
                'vegetarian': [
                    "Vegetarian protein sources:\n1. Legumes (beans, lentils)\n2. Quinoa\n3. Greek yogurt\n4. Tofu/Tempeh\n5. Nuts and seeds\n6. Protein-rich vegetables\nAim for 0.8-1g protein per kg body weight",
                    "Vegetarian meal plan:\nBreakfast: Oatmeal with nuts and fruits\nSnack: Greek yogurt with berries\nLunch: Quinoa bowl with chickpeas\nSnack: Hummus with vegetables\nDinner: Lentil curry with brown rice"
                ],
                'non-vegetarian': [
                    "Non-veg protein sources:\n1. Chicken breast (31g/100g)\n2. Fish (20-25g/100g)\n3. Eggs (6g/egg)\n4. Lean beef (26g/100g)\n5. Turkey (29g/100g)\nPlus vegetarian sources",
                    "Non-veg meal plan:\nBreakfast: Eggs with whole grain toast\nSnack: Protein shake\nLunch: Grilled chicken with quinoa\nSnack: Tuna with crackers\nDinner: Fish with vegetables"
                ],
                'weight_loss': [
                    "Weight loss diet tips:\n1. Calculate TDEE and eat 500 calories less\n2. High protein (1.6-2.2g/kg)\n3. High fiber foods\n4. Lots of vegetables\n5. Stay hydrated\n6. Avoid processed foods",
                    "Weight loss meal timing:\nBreakfast (7-8 AM): Protein + complex carbs\nSnack (10-11 AM): Fruits\nLunch (1-2 PM): Protein + vegetables\nSnack (4-5 PM): Nuts/seeds\nDinner (7-8 PM): Light protein + vegetables"
                ],
                'bulking': [
                    "Bulking diet:\n1. Caloric surplus (300-500 extra calories)\n2. High protein (2g/kg body weight)\n3. Moderate fats (0.5g/kg)\n4. Rest carbs\n5. 5-6 meals per day",
                    "Bulking meal plan (3000 cal example):\nBreakfast: Oats + eggs + banana\nSnack: Mass gainer shake\nLunch: Chicken rice bowl\nPost-workout: Protein shake + fruits\nDinner: Salmon + sweet potato\nBefore bed: Casein protein"
                ]
            },

            # Body Composition
            'bmi|weight|body': {
                'underweight': [
                    "Underweight (BMI < 18.5) recommendations:\n1. Increase calories by 500/day\n2. Eat every 2-3 hours\n3. High-calorie healthy foods\n4. Strength training\n5. Protein-rich diet\n6. Healthy fats",
                    "Weight gain tips:\n1. Track calories (aim for surplus)\n2. Eat calorie-dense foods\n3. Liquid calories (smoothies)\n4. Regular meals\n5. Progressive overload in training"
                ],
                'overweight': [
                    "Overweight (BMI 25-29.9) guidelines:\n1. Create caloric deficit\n2. Increase protein intake\n3. Regular exercise\n4. Portion control\n5. Sleep 7-9 hours\n6. Stress management",
                    "Weight management:\n1. Track food intake\n2. Regular cardio\n3. Strength training\n4. Mindful eating\n5. Regular meals\n6. Adequate hydration"
                ],
                'obese': [
                    "Obesity management (BMI ≥ 30):\n1. Consult healthcare provider\n2. Start with walking\n3. Gradual diet changes\n4. Regular monitoring\n5. Support group\n6. Professional guidance",
                    "Obesity action plan:\n1. Set realistic goals\n2. Daily movement\n3. Food diary\n4. Regular check-ups\n5. Behavioral therapy\n6. Stress management"
                ]
            },

            # Mental Fitness
            'mental|mind|stress': {
                'sleep': [
                    "Sleep guidelines:\n1. 7-9 hours per night\n2. Consistent schedule\n3. Dark, quiet room (18-20°C)\n4. No screens 1 hour before bed\n5. Regular exercise\n6. No caffeine after 2 PM",
                    "Better sleep routine:\n1. Fixed bedtime\n2. Evening relaxation\n3. Morning sunlight\n4. No late meals\n5. Comfortable bedding\n6. White noise if needed"
                ],
                'anxiety': [
                    "Anxiety management:\n1. Deep breathing exercises\n2. Regular exercise\n3. Meditation/Mindfulness\n4. Proper sleep\n5. Limited caffeine\n6. Professional help if needed",
                    "Anti-anxiety techniques:\n1. 4-7-8 breathing\n2. Progressive relaxation\n3. Grounding exercises\n4. Regular walks\n5. Journaling\n6. Support groups"
                ],
                'meditation': [
                    "Meditation guide:\n1. Start with 5-10 minutes\n2. Focus on breath\n3. Body scan technique\n4. Guided meditation apps\n5. Regular practice\n6. Quiet environment",
                    "Meditation types:\n1. Mindfulness\n2. Transcendental\n3. Loving-kindness\n4. Body scan\n5. Walking meditation\n6. Breath awareness"
                ]
            },

            # Supplements and Protein Powders
            'supplement|protein powder|bcaa|creatine': {
                'whey_protein': [
                    "Whey Protein Guide:\n1. Fast-absorbing protein\n2. Best post-workout\n3. Types:\n   - Whey Concentrate (80% protein)\n   - Whey Isolate (90% protein)\n   - Hydrolyzed Whey\n4. Dosage: 20-30g per serving\n5. Timing: Post-workout or between meals",
                    "Whey Protein Benefits:\n1. Muscle recovery\n2. Lean muscle growth\n3. Immune system support\n4. Contains essential amino acids\n5. Quick digestion\nBest brands: Optimum Nutrition, MyProtein, Dymatize"
                ],
                'plant_protein': [
                    "Plant Protein Options:\n1. Pea Protein (high in BCAAs)\n2. Hemp Protein (omega-3 rich)\n3. Rice Protein\n4. Soy Protein\n5. Mixed Plant Proteins\nBest for: Vegetarians/vegans, dairy allergies",
                    "Plant Protein Tips:\n1. Check complete amino profile\n2. Mix different sources\n3. Look for added digestive enzymes\n4. Consider protein blend products\n5. Watch for added sugars"
                ],
                'creatine': [
                    "Creatine Guide:\n1. Most researched supplement\n2. Recommended dose: 5g daily\n3. Types:\n   - Monohydrate (most studied)\n   - HCL\n   - Ethyl Ester\n4. Benefits:\n   - Strength gains\n   - Muscle volume\n   - Recovery\n5. No loading needed",
                    "Creatine Usage:\n1. Take daily\n2. Mix with water/shake\n3. Timing not crucial\n4. Stay hydrated\n5. Safe long-term\n6. Affordable option"
                ]
            },

            # Health Conditions and Exercise
            'disease|condition|health issue': {
                'diabetes': [
                    "Exercise with Diabetes:\n1. Check blood sugar before/after\n2. Carry fast-acting carbs\n3. Start slowly\n4. Best exercises:\n   - Walking\n   - Swimming\n   - Cycling\n   - Light weights\n5. Monitor feet for injuries\n6. Stay hydrated",
                    "Diabetes Workout Tips:\n1. Exercise same time daily\n2. Wear medical ID\n3. Check sugar every 30 mins\n4. Avoid high-intensity initially\n5. Partner workout recommended\n6. Consult doctor first"
                ],
                'heart_condition': [
                    "Exercise with Heart Conditions:\n1. Get doctor's clearance\n2. Start very gradually\n3. Focus on low-impact:\n   - Walking\n   - Swimming\n   - Tai Chi\n4. Monitor heart rate\n5. Know warning signs\n6. Avoid high-intensity",
                    "Heart-Safe Exercise Tips:\n1. Warm up properly\n2. Cool down essential\n3. Monitor breathing\n4. Use RPE scale\n5. Stay hydrated\n6. No breath holding"
                ],
                'arthritis': [
                    "Arthritis Exercise Guide:\n1. Focus on:\n   - Range of motion\n   - Water exercises\n   - Gentle yoga\n   - Light resistance\n2. Avoid high-impact\n3. Use heat before\n4. Ice after\n5. Listen to pain",
                    "Joint-Friendly Workouts:\n1. Swimming/water aerobics\n2. Stationary cycling\n3. Elliptical machine\n4. Chair exercises\n5. Gentle stretching\n6. Tai Chi"
                ]
            },

            # Hydration and Water Intake
            'water|hydration|drink': {
                'general': [
                    "Hydration Guidelines:\n1. Daily intake:\n   - Men: 3.7 liters\n   - Women: 2.7 liters\n2. Signs of dehydration:\n   - Dark urine\n   - Thirst\n   - Fatigue\n   - Headache\n3. Increase intake during:\n   - Exercise\n   - Hot weather\n   - Illness",
                    "Water Intake Tips:\n1. Start day with water\n2. Carry water bottle\n3. Set reminders\n4. Track intake\n5. Add natural flavors\n6. Check urine color"
                ],
                'exercise': [
                    "Exercise Hydration:\n1. Pre-workout: 16-20 oz (2-3 hours before)\n2. During: 7-10 oz every 10-20 mins\n3. Post-workout: 16-24 oz per pound lost\n4. Signs of need:\n   - Thirst\n   - Dark urine\n   - Fatigue\n   - Decreased performance",
                    "Sports Hydration:\n1. Electrolyte needs:\n   - Sodium\n   - Potassium\n   - Magnesium\n2. When to use sports drinks:\n   - 60+ min exercise\n   - Hot weather\n   - High intensity"
                ]
            },

            # Recovery and Injury Prevention
            'recovery|injury|pain': {
                'prevention': [
                    "Injury Prevention:\n1. Proper warm-up (10-15 mins)\n2. Correct form\n3. Gradual progression\n4. Rest days\n5. Cross-training\n6. Regular stretching\n7. Proper gear",
                    "Prevention Tips:\n1. Listen to body\n2. Regular maintenance:\n   - Foam rolling\n   - Stretching\n   - Massage\n3. Proper nutrition\n4. Adequate sleep\n5. Stress management"
                ],
                'treatment': [
                    "RICE Method:\n1. Rest - Avoid aggravating\n2. Ice - 20 mins on/off\n3. Compression - Not too tight\n4. Elevation - Above heart\nWhen to see doctor:\n- Severe pain\n- Swelling\n- Limited movement",
                    "Recovery Tools:\n1. Foam roller\n2. Massage balls\n3. Compression gear\n4. Ice/heat therapy\n5. Recovery supplements\n6. Professional massage"
                ]
            },

            # Fitness for Different Age Groups
            'age|elderly|senior|youth': {
                'seniors': [
                    "Senior Fitness (65+):\n1. Focus areas:\n   - Balance exercises\n   - Light resistance\n   - Walking\n   - Water aerobics\n2. Frequency: 3-5 times/week\n3. Duration: 20-30 mins\n4. Intensity: Moderate",
                    "Senior Exercise Tips:\n1. Start slowly\n2. Use support when needed\n3. Focus on balance\n4. Social activities\n5. Regular stretching\n6. Chair exercises"
                ],
                'youth': [
                    "Youth Fitness (13-19):\n1. Focus on:\n   - Proper form\n   - Bodyweight exercises\n   - Sports skills\n   - Flexibility\n2. Avoid heavy weights\n3. Emphasize technique\n4. Include play time",
                    "Teen Exercise Guidelines:\n1. Mix activities\n2. Include friends\n3. Sports participation\n4. Proper nutrition\n5. Adequate rest\n6. Growth consideration"
                ]
            },

            # Advanced Training Techniques
            'advanced|technique|method': {
                'hiit': [
                    "HIIT Training:\n1. Structure:\n   - 30s high intensity\n   - 30s rest\n   - 20-30 mins total\n2. Benefits:\n   - Fat burning\n   - Time efficient\n   - Improved endurance\n3. 2-3 times/week",
                    "HIIT Workouts:\n1. Tabata (20s on/10s off)\n2. Circuit training\n3. Sprint intervals\n4. Bodyweight HIIT\n5. Recovery crucial\n6. Form priority"
                ],
                'supersets': [
                    "Superset Training:\n1. Types:\n   - Antagonist (bi/tri)\n   - Compound\n   - Pre-exhaust\n2. Benefits:\n   - Time efficient\n   - Intensity boost\n   - Enhanced pump",
                    "Superset Examples:\n1. Chest/Back:\n   - Bench + Rows\n2. Bi/Tri:\n   - Curls + Extensions\n3. Legs:\n   - Squats + Lunges"
                ]
            },

            # Fitness Goals
            'goal|target|aim': {
                'fat_loss': [
                    "Fat Loss Strategy:\n1. Caloric deficit (500-700 cal/day)\n2. Macros:\n   - High protein (2g/kg)\n   - Moderate carbs (2-3g/kg)\n   - Low fat (0.5g/kg)\n3. Training:\n   - Weight training 4x/week\n   - HIIT 2-3x/week\n   - 10k steps daily\n4. Sleep 7-8 hours\n5. Stress management",
                    "Fat Loss Tips:\n1. Track calories accurately\n2. Increase protein intake\n3. Progressive overload\n4. HIIT cardio\n5. Stay hydrated\n6. Meal timing:\n   - Pre-workout: Protein + carbs\n   - Post-workout: Protein + carbs\n   - Other meals: Protein + veggies"
                ],
                'muscle_gain': [
                    "Muscle Building Plan:\n1. Caloric surplus (300-500 cal)\n2. Macros:\n   - Protein: 2.2g/kg\n   - Carbs: 4-7g/kg\n   - Fats: 0.5-1g/kg\n3. Training:\n   - Progressive overload\n   - 6-12 reps\n   - 3-4 sets\n   - 4-5 days/week\n4. Rest 48hrs/muscle group",
                    "Muscle Gain Tips:\n1. Focus compounds lifts\n2. Track progress weekly\n3. Deload every 6-8 weeks\n4. Sleep 8+ hours\n5. Meal timing:\n   - Pre: Complex carbs\n   - Post: Fast carbs + protein\n6. Supplements:\n   - Creatine\n   - Protein powder"
                ],
                'strength': [
                    "Strength Training:\n1. Program focus:\n   - Squat\n   - Deadlift\n   - Bench Press\n   - Overhead Press\n2. Rep ranges: 1-5\n3. Sets: 4-6\n4. Rest: 3-5 mins\n5. Frequency: 3-4x/week",
                    "Strength Tips:\n1. Progressive overload\n2. Perfect form first\n3. Track numbers\n4. Deload properly\n5. Nutrition:\n   - Maintenance calories\n   - High protein\n   - Carbs around workout"
                ]
            },

            # Exercise Form
            'form|technique|posture': {
                'squat': [
                    "Squat Form Guide:\n1. Stance:\n   - Feet shoulder-width\n   - Toes slightly out\n2. Movement:\n   - Brace core\n   - Hip hinge back\n   - Knees track toes\n   - Chest up\n   - Deep breath hold\n3. Common errors:\n   - Knees caving in\n   - Heels rising\n   - Back rounding",
                    "Squat Variations:\n1. Back Squat\n2. Front Squat\n3. Goblet Squat\n4. Bulgarian Split Squat\n5. Box Squat\nKey points:\n- Start light\n- Film yourself\n- Get feedback"
                ],
                'deadlift': [
                    "Deadlift Form:\n1. Setup:\n   - Mid-foot under bar\n   - Hip hinge\n   - Shoulders over bar\n2. Movement:\n   - Push floor away\n   - Bar drags legs\n   - Hips and shoulders rise\n3. Lockout:\n   - Squeeze glutes\n   - Neutral spine\n4. Breathing:\n   - Brace core\n   - Hold breath during rep",
                    "Deadlift Tips:\n1. Common mistakes:\n   - Rounded back\n   - Bar too far\n   - Jerking bar\n2. Cues:\n   - Protect armpits\n   - Proud chest\n   - Push ground away\n3. Start light\n4. Film form"
                ],
                'bench_press': [
                    "Bench Press Form:\n1. Setup:\n   - Shoulder blades pinched\n   - Feet planted\n   - Slight arch\n2. Movement:\n   - Control descent\n   - Touch mid-chest\n   - Explosive press\n3. Grip:\n   - 1.5-2x shoulder width\n   - Wrap thumb\n4. Eyes under bar",
                    "Bench Tips:\n1. Safety:\n   - Use spotter\n   - Set safety pins\n2. Common errors:\n   - Bouncing\n   - Butt lifting\n   - Wrists bending\n3. Variations:\n   - Close grip\n   - Incline\n   - Dumbbell"
                ]
            },

            # Training Splits
            'split|routine|program': {
                'beginner': [
                    "Beginner Split:\n1. Full Body 3x/week:\nDay 1:\n- Squats\n- Bench Press\n- Rows\n- Shoulder Press\nDay 2:\n- Deadlifts\n- Incline Press\n- Pull-ups\n- Lunges\nDay 3:\n- Front Squats\n- Dips\n- Face Pulls\n- Core work",
                    "Beginner Tips:\n1. Rest between days\n2. Focus on form\n3. Start light\n4. Progress slowly\n5. Track workouts\n6. Get enough sleep"
                ],
                'intermediate': [
                    "Upper/Lower Split:\nUpper 1:\n- Bench Press\n- Rows\n- Shoulder Press\n- Arms\nLower 1:\n- Squats\n- Romanian Deadlifts\n- Lunges\n- Calves\nUpper 2:\n- Incline Press\n- Pull-ups\n- Lateral Raises\nLower 2:\n- Deadlifts\n- Leg Press\n- Hip Thrusts",
                    "Push/Pull/Legs:\nPush:\n- Chest\n- Shoulders\n- Triceps\nPull:\n- Back\n- Biceps\n- Rear Delts\nLegs:\n- Quads\n- Hamstrings\n- Calves"
                ]
            },

            # Cardio Types
            'cardio|conditioning|endurance': {
                'types': [
                    "Cardio Options:\n1. LISS (Low Intensity):\n   - Walking\n   - Light jogging\n   - Swimming\n   - Cycling\n2. HIIT:\n   - Sprints\n   - Burpees\n   - Jump rope\n3. Benefits:\n   - Heart health\n   - Fat loss\n   - Recovery\n   - Endurance",
                    "Cardio Programming:\n1. Fat Loss:\n   - HIIT: 2-3x/week\n   - LISS: 2-3x/week\n2. Muscle Gain:\n   - LISS: 2x/week\n   - Post-weights\n3. General Health:\n   - 150 mins/week\n   - Mix intensities"
                ],
                'heart_rate': [
                    "Heart Rate Zones:\n1. Zone 1 (50-60%): Recovery\n2. Zone 2 (60-70%): Fat burn\n3. Zone 3 (70-80%): Aerobic\n4. Zone 4 (80-90%): Anaerobic\n5. Zone 5 (90-100%): Maximum\nCalculate max HR: 220 - age",
                    "Zone Training:\n1. Fat Loss: Zone 2-3\n2. Endurance: Zone 3-4\n3. Performance: Zone 4-5\n4. Recovery: Zone 1-2\nMonitor with HR monitor"
                ]
            },

            # Weight Loss and Fat Loss
            'weight loss|fat loss|slim|reduce': {
                'diet_tips': [
                    "Weight Loss Diet Tips:\n1. Caloric deficit fundamentals:\n   - Calculate TDEE\n   - Subtract 500-700 calories\n   - Track everything\n2. Macros:\n   - Protein: 2.2g/kg bodyweight\n   - Fats: 0.5-0.8g/kg\n   - Carbs: remaining calories\n3. Meal timing:\n   - 4-6 smaller meals\n   - Protein with each meal\n   - Last meal 2-3 hrs before bed",
                    "Fat Loss Nutrition:\n1. Foods to emphasize:\n   - Lean proteins (chicken, fish)\n   - Green vegetables\n   - Complex carbs\n   - Healthy fats\n2. Foods to limit:\n   - Processed foods\n   - Added sugars\n   - Alcohol\n   - High-fat snacks"
                ],
                'workout_plan': [
                    "Fat Loss Workout Plan:\n1. Weight Training:\n   - 4 days/week\n   - Compound movements\n   - Moderate weights\n   - 10-15 rep range\n2. Cardio:\n   - HIIT: 2-3x/week\n   - LISS: 3-4x/week\n3. Daily Activity:\n   - 10,000 steps\n   - Active hobbies",
                    "Weekly Split for Fat Loss:\nDay 1: Push + HIIT\nDay 2: Pull + LISS\nDay 3: Rest + Walk\nDay 4: Legs + HIIT\nDay 5: Upper Body + LISS\nDay 6: Rest + Walk\nDay 7: Full Body + LISS"
                ],
                'lifestyle': [
                    "Lifestyle for Fat Loss:\n1. Sleep hygiene:\n   - 7-9 hours/night\n   - Consistent schedule\n   - Dark room\n2. Stress management:\n   - Meditation\n   - Deep breathing\n   - Regular breaks\n3. Daily habits:\n   - Morning walk\n   - Meal prep\n   - Progress photos",
                    "Success Strategies:\n1. Track progress:\n   - Weekly photos\n   - Measurements\n   - Scale weight\n2. Support system:\n   - Workout partner\n   - Online community\n   - Professional help\n3. Mindset:\n   - Small goals\n   - Celebrate wins\n   - Focus on health"
                ]
            },

            # Plateau Breaking
            'plateau|stuck|not losing': {
                'strategies': [
                    "Breaking Plateaus:\n1. Diet adjustments:\n   - Recalculate calories\n   - Cycle carbs\n   - Diet breaks\n2. Training changes:\n   - Increase intensity\n   - Change rep ranges\n   - Add supersets\n3. Recovery check:\n   - Sleep quality\n   - Stress levels\n   - Recovery weeks",
                    "Plateau Solutions:\n1. Shock methods:\n   - Reverse diet\n   - Change workout time\n   - New exercises\n2. Track harder:\n   - Food weighing\n   - Step counting\n   - Sleep tracking\n3. Advanced techniques:\n   - Fasted cardio\n   - Drop sets\n   - Giant sets"
                ],
                'common_mistakes': [
                    "Common Plateau Causes:\n1. Diet issues:\n   - Hidden calories\n   - Weekend overeating\n   - Poor tracking\n2. Training mistakes:\n   - Too much cardio\n   - Not enough weights\n   - Same routine\n3. Lifestyle factors:\n   - Stress eating\n   - Poor sleep\n   - Inconsistency",
                    "Breaking Bad Habits:\n1. Identify triggers:\n   - Stress eating\n   - Social pressure\n   - Time management\n2. Create solutions:\n   - Meal prep\n   - Support system\n   - Alternative rewards\n3. Stay consistent:\n   - Weekly check-ins\n   - Adjust as needed\n   - Keep accountable"
                ]
            },

            # Body Recomposition
            'recomp|build muscle lose fat|tone': {
                'nutrition': [
                    "Recomp Nutrition:\n1. Calorie cycling:\n   - Training days: maintenance\n   - Rest days: slight deficit\n2. Protein focus:\n   - 2.2-2.8g/kg bodyweight\n   - Every 3-4 hours\n   - Quality sources\n3. Nutrient timing:\n   - Pre-workout: carbs + protein\n   - Post-workout: fast digesting\n   - Other meals: balanced",
                    "Meal Planning for Recomp:\nBreakfast: Eggs + oats\nSnack: Protein shake\nPre-workout: Rice + chicken\nPost-workout: Whey + banana\nDinner: Fish + sweet potato\nBefore bed: Casein protein"
                ],
                'training': [
                    "Recomp Training:\n1. Weight training:\n   - Heavy compounds\n   - Progressive overload\n   - 6-12 rep range\n2. Cardio balance:\n   - Moderate intensity\n   - Post-weights\n   - Heart rate zones\n3. Recovery focus:\n   - Sleep quality\n   - Stress management\n   - Deload weeks",
                    "Weekly Recomp Split:\nDay 1: Heavy push\nDay 2: Heavy pull\nDay 3: Rest\nDay 4: Legs\nDay 5: Upper body\nDay 6: Rest\nDay 7: Full body\nCardio: 2-3x HIIT"
                ]
            },

            # Long-term Success
            'maintain|sustain|lifestyle': {
                'habits': [
                    "Sustainable Habits:\n1. Flexible dieting:\n   - 80/20 rule\n   - Social eating\n   - Food variety\n2. Enjoyable exercise:\n   - Mixed activities\n   - Social sports\n   - Regular walking\n3. Lifestyle balance:\n   - Stress management\n   - Sleep priority\n   - Social support",
                    "Maintenance Tips:\n1. Regular monitoring:\n   - Weekly weigh-ins\n   - Monthly photos\n   - Clothing fit\n2. Adjust as needed:\n   - Seasonal changes\n   - Life events\n   - Energy levels\n3. Stay consistent:\n   - Meal prep\n   - Exercise schedule\n   - Sleep routine"
                ],
                'mindset': [
                    "Success Mindset:\n1. Long-term focus:\n   - Health first\n   - Sustainable changes\n   - Life balance\n2. Identity shift:\n   - Healthy lifestyle\n   - Active person\n   - Mindful eater\n3. Growth mindset:\n   - Learn from setbacks\n   - Adapt to changes\n   - Continuous improvement",
                    "Mental Strategies:\n1. Goal setting:\n   - Process goals\n   - Achievement markers\n   - Regular reviews\n2. Support system:\n   - Like-minded friends\n   - Online community\n   - Professional help\n3. Stress management:\n   - Regular exercise\n   - Meditation\n   - Hobbies"
                ]
            },

            # Cardio Activities
            'cycling|bike|bicycle': {
                'benefits': [
                    "Cycling Benefits:\n1. Cardiovascular:\n   - Heart health\n   - Endurance\n   - Low impact\n2. Muscles worked:\n   - Quadriceps\n   - Hamstrings\n   - Calves\n   - Core\n3. Benefits:\n   - Joint-friendly\n   - Fat burning\n   - Outdoor option",
                    "Cycling Tips:\n1. Bike setup:\n   - Proper seat height\n   - Handlebar position\n   - Foot position\n2. Form:\n   - Straight back\n   - Relaxed shoulders\n   - Slight knee bend\n3. Progression:\n   - Start 20 mins\n   - Build gradually\n   - Mix intensities"
                ],
                'workouts': [
                    "Cycling Workouts:\n1. Beginner:\n   - 20-30 mins steady\n   - Flat terrain\n   - Moderate pace\n2. Intermediate:\n   - Hill intervals\n   - Speed intervals\n   - 45-60 mins\n3. Advanced:\n   - HIIT sprints\n   - Long distance\n   - Mixed terrain",
                    "Indoor Cycling:\n1. Spin class:\n   - Group motivation\n   - Structured workout\n   - Music driven\n2. Stationary bike:\n   - Resistance levels\n   - Program options\n   - Progress tracking"
                ]
            },

            'walking|steps|stroll': {
                'basics': [
                    "Walking Guide:\n1. Benefits:\n   - Low impact\n   - Fat burning\n   - Mental health\n   - Accessibility\n2. Goals:\n   - 10,000 steps/day\n   - 30 mins continuous\n   - Brisk pace\n3. Progression:\n   - Increase duration\n   - Add inclines\n   - Speed walking",
                    "Walking Tips:\n1. Form:\n   - Head up\n   - Shoulders back\n   - Arms swing\n   - Heel-to-toe\n2. Equipment:\n   - Good shoes\n   - Comfortable clothes\n   - Step tracker\n3. Safety:\n   - Well-lit areas\n   - Weather appropriate\n   - Stay hydrated"
                ],
                'programs': [
                    "Walking Programs:\n1. Beginner:\n   - Start: 10 mins\n   - Build by 5 mins\n   - Goal: 30 mins\n2. Weight Loss:\n   - Morning fasted\n   - Post-meal walks\n   - Incline walking\n3. Active Life:\n   - Park further\n   - Take stairs\n   - Walking meetings",
                    "Walking Workouts:\n1. Power walking:\n   - Faster pace\n   - Arm movement\n   - Engage core\n2. Hill walking:\n   - Build strength\n   - More calories\n   - Better cardio\n3. Interval walking:\n   - Mix speeds\n   - Add bodyweight\n   - Time-based"
                ]
            },

            # Gym Equipment
            'equipment|machine|gym': {
                'cardio_machines': [
                    "Cardio Equipment Guide:\n1. Treadmill:\n   - Walking/Running\n   - Incline options\n   - Program variety\n2. Elliptical:\n   - Low impact\n   - Full body\n   - Resistance levels\n3. Stair Master:\n   - Leg focus\n   - Intense cardio\n   - Posture important\n4. Rowing Machine:\n   - Full body\n   - Power development\n   - Technique crucial",
                    "Machine Settings:\n1. Treadmill:\n   - Speed: 3-12 mph\n   - Incline: 0-15%\n   - Programs: interval/hill\n2. Elliptical:\n   - Resistance: 1-20\n   - Stride length\n   - Handle use\n3. Rower:\n   - Damper: 3-5 start\n   - Stroke rate\n   - Split time"
                ],
                'weight_machines': [
                    "Weight Machine Guide:\n1. Chest:\n   - Chest press\n   - Pec deck\n   - Cable station\n2. Back:\n   - Lat pulldown\n   - Seated row\n   - Smith machine\n3. Legs:\n   - Leg press\n   - Leg extension\n   - Leg curl\n4. Arms:\n   - Bicep curl\n   - Tricep pushdown\n   - Cable machine",
                    "Machine Tips:\n1. Setup:\n   - Adjust seat\n   - Set weight\n   - Check range\n2. Form:\n   - Control motion\n   - Full range\n   - Proper breathing\n3. Safety:\n   - Start light\n   - Clean equipment\n   - Ask for help"
                ],
                'free_weights': [
                    "Free Weight Equipment:\n1. Dumbbells:\n   - Pairs 2-150 lbs\n   - Versatile use\n   - Unilateral work\n2. Barbells:\n   - Olympic bar\n   - Weight plates\n   - Clips/collars\n3. Kettlebells:\n   - Swing focus\n   - Dynamic moves\n   - Core engagement",
                    "Weight Selection:\n1. Beginners:\n   - Light weight\n   - Perfect form\n   - Build gradually\n2. Form tips:\n   - Control weight\n   - Full range\n   - Core engaged\n3. Safety:\n   - Use mirrors\n   - Spotter help\n   - Proper rack"
                ]
            },

            'machine form|equipment use': {
                'setup': [
                    "Machine Setup Guide:\n1. Seat adjustment:\n   - Height align\n   - Back support\n   - Handle reach\n2. Weight selection:\n   - Test light\n   - Smooth motion\n   - Control range\n3. Safety checks:\n   - Pin secure\n   - Path clear\n   - Emergency stop",
                    "Equipment Safety:\n1. Before use:\n   - Check cables\n   - Secure weights\n   - Clean surfaces\n2. During use:\n   - Control motion\n   - Proper breathing\n   - Stay focused\n3. After use:\n   - Re-rack weights\n   - Wipe down\n   - Report issues"
                ],
                'common_mistakes': [
                    "Machine Mistakes:\n1. Setup errors:\n   - Wrong height\n   - Poor alignment\n   - Too heavy\n2. Form issues:\n   - Rushing reps\n   - Partial range\n   - Body swing\n3. Safety risks:\n   - No spotting\n   - Improper clips\n   - Quick release",
                    "Form Corrections:\n1. Basic rules:\n   - Controlled motion\n   - Full range\n   - Proper path\n2. Breathing:\n   - Exhale effort\n   - Inhale return\n   - Stay regular\n3. Focus:\n   - Mind-muscle\n   - Feel movement\n   - Target area"
                ]
            },

            'gym basics|starter|beginner': {
                'etiquette': [
                    "Gym Etiquette:\n1. Equipment use:\n   - Share machines\n   - Time limits\n   - Wipe down\n2. Space respect:\n   - Personal space\n   - Mirror access\n   - Walking paths\n3. General rules:\n   - Re-rack weights\n   - Use towel\n   - Indoor shoes",
                    "Gym Basics:\n1. First visit:\n   - Tour facility\n   - Learn rules\n   - Start simple\n2. Equipment:\n   - Ask questions\n   - Start machines\n   - Learn setup\n3. Routine:\n   - Warm up first\n   - Basic exercises\n   - Cool down"
                ],
                'starter_routine': [
                    "Beginner Program:\n1. Cardio start:\n   - 5-10 min warmup\n   - Choose machine\n   - Moderate pace\n2. Basic machines:\n   - Chest press\n   - Lat pulldown\n   - Leg press\n3. Cool down:\n   - Light cardio\n   - Basic stretches",
                    "First Weeks:\n1. Schedule:\n   - 2-3 days/week\n   - Rest between\n   - Short sessions\n2. Progress:\n   - Form first\n   - Light weights\n   - Build slowly\n3. Goals:\n   - Learn equipment\n   - Build routine\n   - Stay consistent"
                ]
            }
        }

    def get_response(self, user_input: str) -> str:
        user_input = user_input.lower().strip()

        # Check for greetings
        if self._is_greeting(user_input):
            return "Hello! I'm your fitness assistant. How can I help you with your fitness, diet, or mental wellness journey?"

        # Check for farewells
        if self._is_farewell(user_input):
            return "Goodbye! Stay healthy and keep moving!"

        # More specific pattern matching first
        # Leg workout specific patterns
        if any(word in user_input for word in ['leg', 'legs', 'quad', 'hamstring', 'calf', 'calves', 'thigh']):
            return random.choice(self.knowledge_base['legs|quads|hamstring']['exercises'])
        
        # Existing specific patterns
        if 'non' in user_input and ('veg' in user_input or 'vegetarian' in user_input):
            return random.choice(self.knowledge_base['diet|nutrition|meal']['non-vegetarian'])
        
        if 'weight loss' in user_input or 'lose weight' in user_input:
            return random.choice(self.knowledge_base['diet|nutrition|meal']['weight_loss'])
        
        if 'obese' in user_input or 'obesity' in user_input:
            return random.choice(self.knowledge_base['bmi|weight|body']['obese'])
        
        if 'vegetarian' in user_input or ('veg' in user_input and 'non' not in user_input):
            return random.choice(self.knowledge_base['diet|nutrition|meal']['vegetarian'])

        # General pattern matching for other queries
        for pattern, categories in self.knowledge_base.items():
            if re.search(pattern, user_input):
                # Check for specific category matches
                for category, responses in categories.items():
                    if category in user_input:
                        return random.choice(responses)
                
                # If no specific category matched, return a general response from this pattern
                first_category = list(categories.values())[0]
                return random.choice(first_category)

        # Default response if no pattern matched
        return ("I can help you with fitness, diet, and mental wellness. Try asking about:\n"
                "- Workout routines and exercises\n"
                "- Nutrition and diet tips\n"
                "- Stress management and mental wellness\n"
                "- General fitness advice")

    def _is_greeting(self, text: str) -> bool:
        greetings = ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
        return any(greeting in text for greeting in greetings)

    def _is_farewell(self, text: str) -> bool:
        farewells = ['bye', 'goodbye', 'see you', 'farewell', 'thanks', 'thank you']
        return any(farewell in text for farewell in farewells) 
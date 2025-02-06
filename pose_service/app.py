from flask import Flask, request, jsonify, send_file
import mediapipe as mp
import cv2
import numpy as np
import base64
from flask_cors import CORS
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime

app = Flask(__name__)

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Exercise definitions
EXERCISES = {
    'chest': {
        'push_up': {
            'name': 'Push Up',
            'landmarks': [
                mp_pose.PoseLandmark.LEFT_SHOULDER,
                mp_pose.PoseLandmark.LEFT_ELBOW,
                mp_pose.PoseLandmark.LEFT_WRIST
            ],
            'angle_thresholds': {
                'good': (85, 110),
                'warning': (70, 120)
            },
            'feedback': {
                'too_low': "Keep your chest up, don't go too low",
                'too_high': "Lower your body more for full range of motion",
                'good': "Perfect push-up form!"
            }
        },
        'bench_press': {
            'name': 'Bench Press',
            'landmarks': [
                mp_pose.PoseLandmark.LEFT_SHOULDER,
                mp_pose.PoseLandmark.LEFT_ELBOW,
                mp_pose.PoseLandmark.LEFT_WRIST
            ],
            'angle_thresholds': {
                'good': (80, 100),
                'warning': (70, 110)
            },
            'feedback': {
                'too_low': "Bar is too low, maintain control",
                'too_high': "Lower the bar with control",
                'good': "Great bench press form!"
            }
        },
        'dumbbell_fly': {
            'name': 'Dumbbell Fly',
            'landmarks': [
                mp_pose.PoseLandmark.LEFT_SHOULDER,
                mp_pose.PoseLandmark.LEFT_ELBOW,
                mp_pose.PoseLandmark.LEFT_WRIST
            ],
            'angle_thresholds': {
                'good': (140, 170),
                'warning': (130, 180)
            },
            'feedback': {
                'too_low': "Don't let arms drop too low",
                'too_high': "Keep slight bend in elbows",
                'good': "Perfect fly movement!"
            }
        },
        'incline_press': {
            'name': 'Incline Press',
            'landmarks': [
                mp_pose.PoseLandmark.LEFT_SHOULDER,
                mp_pose.PoseLandmark.LEFT_ELBOW,
                mp_pose.PoseLandmark.LEFT_WRIST
            ],
            'angle_thresholds': {
                'good': (75, 95),
                'warning': (65, 105)
            },
            'feedback': {
                'too_low': "Keep control at bottom",
                'too_high': "Full extension needed",
                'good': "Perfect incline press!"
            }
        },
        'decline_press': {
            'name': 'Decline Press',
            'landmarks': [
                mp_pose.PoseLandmark.LEFT_SHOULDER,
                mp_pose.PoseLandmark.LEFT_ELBOW,
                mp_pose.PoseLandmark.LEFT_WRIST
            ],
            'angle_thresholds': {
                'good': (80, 100),
                'warning': (70, 110)
            },
            'feedback': {
                'too_low': "Maintain form at bottom",
                'too_high': "Control the descent",
                'good': "Great decline press form!"
            }
        }
    },
    'shoulders': {
        'overhead_press': {
            'name': 'Overhead Press',
            'landmarks': [
                mp_pose.PoseLandmark.LEFT_HIP,
                mp_pose.PoseLandmark.LEFT_SHOULDER,
                mp_pose.PoseLandmark.LEFT_ELBOW
            ],
            'angle_thresholds': {
                'good': (165, 180),
                'warning': (150, 185)
            },
            'feedback': {
                'too_low': "Press fully overhead",
                'too_bent': "Extend arms more",
                'good': "Perfect overhead press!"
            }
        },
        'lateral_raise': {
            'name': 'Lateral Raise',
            'landmarks': [
                mp_pose.PoseLandmark.LEFT_HIP,
                mp_pose.PoseLandmark.LEFT_SHOULDER,
                mp_pose.PoseLandmark.LEFT_ELBOW
            ],
            'angle_thresholds': {
                'good': (80, 100),
                'warning': (70, 110)
            },
            'feedback': {
                'too_low': "Raise to shoulder level",
                'too_high': "Keep at shoulder height",
                'good': "Perfect lateral raise!"
            }
        },
        'front_raise': {
            'name': 'Front Raise',
            'landmarks': [
                mp_pose.PoseLandmark.LEFT_HIP,
                mp_pose.PoseLandmark.LEFT_SHOULDER,
                mp_pose.PoseLandmark.LEFT_ELBOW
            ],
            'angle_thresholds': {
                'good': (80, 100),
                'warning': (70, 110)
            },
            'feedback': {
                'too_low': "Raise arms higher",
                'too_high': "Control the movement",
                'good': "Perfect front raise!"
            }
        },
        'reverse_fly': {
            'name': 'Reverse Fly',
            'landmarks': [
                mp_pose.PoseLandmark.LEFT_HIP,
                mp_pose.PoseLandmark.LEFT_SHOULDER,
                mp_pose.PoseLandmark.LEFT_ELBOW
            ],
            'angle_thresholds': {
                'good': (70, 90),
                'warning': (60, 100)
            },
            'feedback': {
                'too_low': "Raise arms more",
                'too_high': "Control the movement",
                'good': "Perfect rear delt work!"
            }
        },
        'arnold_press': {
            'name': 'Arnold Press',
            'landmarks': [
                mp_pose.PoseLandmark.LEFT_HIP,
                mp_pose.PoseLandmark.LEFT_SHOULDER,
                mp_pose.PoseLandmark.LEFT_ELBOW
            ],
            'angle_thresholds': {
                'good': (160, 180),
                'warning': (150, 185)
            },
            'feedback': {
                'too_low': "Rotate and press up",
                'too_bent': "Extend fully at top",
                'good': "Perfect Arnold press!"
            }
        }
    },
    'back': {
        'pull_up': {
            'name': 'Pull Up',
            'landmarks': [
                mp_pose.PoseLandmark.LEFT_SHOULDER,
                mp_pose.PoseLandmark.LEFT_ELBOW,
                mp_pose.PoseLandmark.LEFT_WRIST
            ],
            'angle_thresholds': {
                'good': (45, 70),
                'warning': (30, 80)
            },
            'feedback': {
                'too_low': "Pull up more, chin over bar",
                'incomplete': "Complete the full range of motion",
                'good': "Strong pull-up form!"
            }
        },
        'bent_over_row': {
            'name': 'Bent Over Row',
            'landmarks': [
                mp_pose.PoseLandmark.LEFT_HIP,
                mp_pose.PoseLandmark.LEFT_SHOULDER,
                mp_pose.PoseLandmark.LEFT_ELBOW
            ],
            'angle_thresholds': {
                'good': (75, 105),
                'warning': (65, 115)
            },
            'feedback': {
                'too_upright': "Bend over more at the hips",
                'too_low': "Keep your back straight",
                'good': "Perfect rowing form!"
            }
        }
    },
    'biceps': {
        'standing_curl': {
            'name': 'Standing Bicep Curl',
            'landmarks': [
                mp_pose.PoseLandmark.LEFT_SHOULDER,
                mp_pose.PoseLandmark.LEFT_ELBOW,
                mp_pose.PoseLandmark.LEFT_WRIST
            ],
            'angle_thresholds': {
                'good': (45, 60),
                'warning': (30, 70)
            },
            'feedback': {
                'too_low': "Curl the weight up more",
                'too_high': "Control the weight down",
                'good': "Perfect curl form!"
            }
        },
        'hammer_curl': {
            'name': 'Hammer Curl',
            'landmarks': [
                mp_pose.PoseLandmark.LEFT_SHOULDER,
                mp_pose.PoseLandmark.LEFT_ELBOW,
                mp_pose.PoseLandmark.LEFT_WRIST
            ],
            'angle_thresholds': {
                'good': (45, 60),
                'warning': (30, 70)
            },
            'feedback': {
                'too_low': "Complete the curl movement",
                'too_loose': "Keep elbows close to body",
                'good': "Perfect hammer curl form!"
            }
        }
    },
    'triceps': {
        'tricep_pushdown': {
            'name': 'Tricep Pushdown',
            'landmarks': [
                mp_pose.PoseLandmark.LEFT_SHOULDER,
                mp_pose.PoseLandmark.LEFT_ELBOW,
                mp_pose.PoseLandmark.LEFT_WRIST
            ],
            'angle_thresholds': {
                'good': (165, 180),
                'warning': (150, 185)
            },
            'feedback': {
                'too_bent': "Extend arms fully",
                'too_loose': "Keep elbows at sides",
                'good': "Perfect tricep pushdown!"
            }
        },
        'overhead_extension': {
            'name': 'Overhead Tricep Extension',
            'landmarks': [
                mp_pose.PoseLandmark.LEFT_SHOULDER,
                mp_pose.PoseLandmark.LEFT_ELBOW,
                mp_pose.PoseLandmark.LEFT_WRIST
            ],
            'angle_thresholds': {
                'good': (30, 45),
                'warning': (20, 55)
            },
            'feedback': {
                'too_wide': "Keep elbows close to head",
                'too_low': "Extend arms fully",
                'good': "Perfect extension form!"
            }
        }
    },
    'legs': {
        'squat': {
            'name': 'Squat',
            'landmarks': [
                mp_pose.PoseLandmark.LEFT_HIP,
                mp_pose.PoseLandmark.LEFT_KNEE,
                mp_pose.PoseLandmark.LEFT_ANKLE
            ],
            'angle_thresholds': {
                'good': (95, 105),
                'warning': (85, 115)
            },
            'feedback': {
                'too_high': "Squat deeper, keep form",
                'too_low': "Rise up a bit, maintain control",
                'good': "Perfect squat depth!"
            }
        },
        'deadlift': {
            'name': 'Deadlift',
            'landmarks': [
                mp_pose.PoseLandmark.LEFT_HIP,
                mp_pose.PoseLandmark.LEFT_KNEE,
                mp_pose.PoseLandmark.LEFT_ANKLE
            ],
            'angle_thresholds': {
                'good': (165, 180),
                'warning': (155, 185)
            },
            'feedback': {
                'too_bent': "Keep back straight",
                'too_upright': "Hinge at hips more",
                'good': "Perfect deadlift form!"
            }
        },
        'lunges': {
            'name': 'Lunges',
            'landmarks': [
                mp_pose.PoseLandmark.LEFT_HIP,
                mp_pose.PoseLandmark.LEFT_KNEE,
                mp_pose.PoseLandmark.LEFT_ANKLE
            ],
            'angle_thresholds': {
                'good': (85, 95),
                'warning': (75, 105)
            },
            'feedback': {
                'too_shallow': "Lower knee closer to ground",
                'too_forward': "Keep front knee behind toes",
                'good': "Perfect lunge form!"
            }
        }
    }
}

@app.route('/exercises', methods=['GET'])
def get_exercises():
    return jsonify({
        'categories': {
            category: list(exercises.keys())
            for category, exercises in EXERCISES.items()
        }
    })

def analyze_exercise_form(frame, exercise_category, exercise_name):
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(image)
    
    if not results.pose_landmarks:
        return {"error": "No pose detected"}
    
    # Draw landmarks with connections
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    
    annotated_image = frame.copy()
    
    # Draw the pose with custom styling
    mp_drawing.draw_landmarks(
        annotated_image,
        results.pose_landmarks,
        mp_pose.POSE_CONNECTIONS,
        landmark_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
        connection_drawing_spec=mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2)
    )
    
    # Add additional visual cues for the specific exercise
    exercise_config = EXERCISES[exercise_category][exercise_name]
    landmarks = results.pose_landmarks.landmark
    points = [landmarks[lm.value] for lm in exercise_config['landmarks']]
    
    # Draw exercise-specific angles
    h, w, _ = frame.shape
    points_px = [(int(p.x * w), int(p.y * h)) for p in points]
    for i in range(len(points_px)):
        cv2.circle(annotated_image, points_px[i], 5, (0, 255, 0), -1)
    
    # Calculate angle
    angle = calculate_angle(
        (points[0].x, points[0].y),
        (points[1].x, points[1].y),
        (points[2].x, points[2].y)
    )
    
    # Only draw angle if it's valid
    if angle > 0:
        cv2.putText(
            annotated_image,
            f"{int(angle)}°",
            points_px[1],
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2
        )
    
    # Convert annotated image to base64
    _, buffer = cv2.imencode('.jpg', annotated_image)
    annotated_image_base64 = base64.b64encode(buffer).decode('utf-8')
    
    # Analyze form based on exercise thresholds
    thresholds = exercise_config['angle_thresholds']
    feedback = exercise_config['feedback']
    
    if thresholds['good'][0] <= angle <= thresholds['good'][1]:
        form_quality = "Good"
        form_feedback = [feedback['good']]
    else:
        form_quality = "Needs Improvement"
        form_feedback = []
        if angle < thresholds['warning'][0]:
            form_feedback.append(feedback['too_low'])
        elif angle > thresholds['warning'][1]:
            form_feedback.append(feedback['too_high'])
    
    return {
        "exercise": exercise_config['name'],
        "angle": angle,
        "feedback": form_feedback,
        "form_quality": form_quality,
        "annotated_image": f"data:image/jpeg;base64,{annotated_image_base64}"
    }

def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    # Check if any point is NaN
    if np.isnan(a).any() or np.isnan(b).any() or np.isnan(c).any():
        return 0
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    
    if angle > 180.0:
        angle = 360-angle
        
    return angle

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        print("Received analysis request")
        data = request.json
        image_data = data['image']
        exercise_category = data.get('category', 'legs')  # default to legs
        exercise_name = data.get('exercise', 'squat')  # default to squat
        
        print(f"Analyzing {exercise_category} - {exercise_name}")
        image_bytes = base64.b64decode(image_data.split(',')[1])
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        results = analyze_exercise_form(frame, exercise_category, exercise_name)
        return jsonify(results)
        
    except Exception as e:
        print("Error occurred:", str(e))
        return jsonify({"error": str(e)})

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    try:
        print("Received PDF generation request")
        data = request.json
        print("Data received:", data)
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12
        )
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=6
        )

        # Title
        story.append(Paragraph(f"Workout Analysis Report", title_style))
        
        # Basic Information
        story.append(Paragraph("Exercise Information", heading_style))
        info_data = [
            ["Body Part", data['category']],
            ["Exercise", data['exercise']],
            ["Date", data['date']],
            ["Time", data['time']],
            ["Duration", data['duration']],
        ]
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(info_table)
        story.append(Spacer(1, 20))

        # Performance Metrics
        story.append(Paragraph("Performance Metrics", heading_style))
        metrics_data = [
            ["Total Reps Analyzed", str(data['totalReps'])],
            ["Form Accuracy", f"{data['accuracy']}%"],
        ]
        metrics_table = Table(metrics_data, colWidths=[2*inch, 4*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 20))

        # Common Issues
        story.append(Paragraph("Areas for Improvement", heading_style))
        for issue in data['commonIssues']:
            story.append(Paragraph(f"• {issue}", normal_style))
        story.append(Spacer(1, 20))

        # Recommendations
        story.append(Paragraph("Recommendations", heading_style))
        for rec in data['recommendations']:
            story.append(Paragraph(f"• {rec}", normal_style))
        story.append(Spacer(1, 20))

        # Exercise Tips
        story.append(Paragraph("Exercise Tips & Best Practices", heading_style))
        for tip in data['exerciseTips']:
            story.append(Paragraph(f"• {tip}", normal_style))

        # Generate PDF
        doc.build(story)
        buffer.seek(0)
        
        response = send_file(
            buffer,
            as_attachment=True,
            download_name=f"{data['category']}-{data['exercise']}-Workout-Summary-{datetime.now().strftime('%Y-%m-%d')}.pdf",
            mimetype='application/pdf',
            max_age=0
        )
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    except Exception as e:
        print("Error generating PDF:", str(e))
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Add CORS support with additional options
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "expose_headers": ["Content-Disposition"]
    }
})

if __name__ == '__main__':
    app.run(port=5000) 
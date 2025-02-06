import cv2
import mediapipe as mp
import numpy as np
from typing import Dict, List, Tuple

class WorkoutAnalyzer:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        # Increase detection confidence thresholds for better accuracy
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils

    def analyze_form(self, video_path: str) -> Dict:
        """Analyzes workout form from video and returns injury risk assessment."""
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Error opening video file")

        frame_count = 0
        valid_frames = 0
        risk_scores = []
        form_issues = []
        
        try:
            while cap.isOpened() and frame_count < 300:  # Limit to 300 frames for performance
                ret, frame = cap.read()
                if not ret:
                    break

                # Resize frame for better performance
                frame = cv2.resize(frame, (640, 480))
                
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.pose.process(frame_rgb)

                if results.pose_landmarks:
                    valid_frames += 1
                    # Analyze pose for each frame
                    risk_score, issues = self._analyze_pose(results.pose_landmarks)
                    risk_scores.append(risk_score)
                    form_issues.extend(issues)

                frame_count += 1

            cap.release()

            if valid_frames == 0:
                raise ValueError("No valid poses detected in the video. Please ensure full body is visible.")

            # Calculate overall risk and compile unique issues
            avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0
            unique_issues = list(set(form_issues))

            # Add general form assessment
            if not unique_issues:
                unique_issues.append("No major form issues detected")

            return {
                'risk_level': self._categorize_risk(avg_risk),
                'form_issues': unique_issues,
                'recommendations': self._get_recommendations(unique_issues)
            }

        except Exception as e:
            cap.release()
            raise Exception(f"Error analyzing video: {str(e)}")

    def _analyze_pose(self, landmarks) -> Tuple[float, List[str]]:
        """Analyzes pose landmarks for potential form issues."""
        issues = []
        risk_score = 0

        try:
            # Get landmark positions
            landmark_dict = self._get_landmark_positions(landmarks)

            # Check shoulder movement for shoulder exercises
            left_shoulder = landmark_dict[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            right_shoulder = landmark_dict[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            left_elbow = landmark_dict[self.mp_pose.PoseLandmark.LEFT_ELBOW.value]
            right_elbow = landmark_dict[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value]
            nose = landmark_dict[self.mp_pose.PoseLandmark.NOSE.value]

            # Check shoulder elevation
            if left_shoulder[1] < 0.2 or right_shoulder[1] < 0.2:  # Shoulders too high
                issues.append("Excessive shoulder elevation")
                risk_score += 0.3

            # Check elbow alignment
            left_elbow_angle = self._calculate_angle(
                landmark_dict[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value],
                landmark_dict[self.mp_pose.PoseLandmark.LEFT_ELBOW.value],
                landmark_dict[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
            )
            right_elbow_angle = self._calculate_angle(
                landmark_dict[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value],
                landmark_dict[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value],
                landmark_dict[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
            )

            if abs(left_elbow_angle - right_elbow_angle) > 15:
                issues.append("Uneven elbow movement")
                risk_score += 0.25

            # Check for shoulder symmetry
            shoulder_diff = abs(left_shoulder[1] - right_shoulder[1])
            if shoulder_diff > 0.1:
                issues.append("Shoulder asymmetry")
                risk_score += 0.25

            # Check for proper range of motion
            if left_elbow_angle < 45 or right_elbow_angle < 45:
                issues.append("Limited range of motion")
                risk_score += 0.2

            # Check head position relative to shoulders (instead of using neck)
            head_alignment = self._calculate_angle(
                nose,
                right_shoulder,  # Using right shoulder as reference
                (right_shoulder[0], right_shoulder[1] - 0.5, right_shoulder[2])  # Virtual point above shoulder
            )
            
            if head_alignment < 70:  # Head tilted too far forward
                issues.append("Forward head posture")
                risk_score += 0.2

        except Exception as e:
            print(f"Error in pose analysis: {str(e)}")
            issues.append("Unable to fully analyze pose")
            risk_score = 0.5

        return risk_score, issues

    def _get_landmark_positions(self, landmarks):
        """Converts landmarks to normalized coordinates."""
        positions = {}
        for idx, landmark in enumerate(landmarks.landmark):
            positions[idx] = (landmark.x, landmark.y, landmark.z)
        return positions

    def _calculate_angle(self, p1: Tuple, p2: Tuple, p3: Tuple) -> float:
        """Calculates angle between three points."""
        try:
            v1 = np.array([p1[0] - p2[0], p1[1] - p2[1]])
            v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]])
            
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
            angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
            
            return np.degrees(angle)
        except:
            return 180.0  # Return default angle if calculation fails

    def _categorize_risk(self, risk_score: float) -> str:
        """Categorizes risk level based on score."""
        if risk_score < 0.3:
            return "Low"
        elif risk_score < 0.6:
            return "Medium"
        else:
            return "High"

    def _get_recommendations(self, issues: List[str]) -> List[str]:
        """Provides recommendations based on identified issues."""
        recommendations = {
            "Excessive shoulder elevation": "Keep shoulders relaxed and away from ears. Focus on controlled movements.",
            "Uneven elbow movement": "Maintain equal movement on both sides. Use lighter weights if needed.",
            "Shoulder asymmetry": "Focus on balanced shoulder positioning and consider mobility exercises.",
            "Limited range of motion": "Gradually work on improving flexibility. Don't force movements beyond comfort.",
            "Forward head posture": "Keep your head aligned with your spine. Look straight ahead.",
            "Unable to fully analyze pose": "Ensure full body is visible in the video and lighting is adequate.",
            "No major form issues detected": "Continue with current form. Consider increasing intensity gradually."
        }
        
        return [recommendations[issue] for issue in issues if issue in recommendations] 
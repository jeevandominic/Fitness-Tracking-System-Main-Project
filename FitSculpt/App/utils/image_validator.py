import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
from PIL import Image
import io
import pytesseract
import cv2

class ImageValidator:
    def __init__(self):
        # Load MobileNet model
        self.model = tf.keras.Sequential([
            hub.KerasLayer("https://tfhub.dev/google/imagenet/mobilenet_v2_100_224/classification/4")
        ])
        
        # Define allowed categories and keywords
        self.allowed_categories = [
            'dumbbell', 'barbell', 'weight', 'gym', 'treadmill', 'bicycle',
            'yoga', 'protein', 'salad', 'food', 'fruit', 'vegetable',
            'running', 'fitness', 'sports', 'exercise', 'workout',
            'training', 'athlete', 'muscle', 'stretching', 'jumping',
            'swimming', 'cycling', 'jogging', 'lifting', 'crossfit',
            'meditation', 'nutrition', 'diet', 'health', 'wellness',
            'person', 'people', 'human', 'man', 'woman', 'sportswear'
        ]
        
        self.fitness_keywords = [
            'fitness', 'gym', 'workout', 'exercise', 'training',
            'health', 'nutrition', 'diet', 'protein', 'muscle',
            'cardio', 'strength', 'yoga', 'running', 'cycling',
            'swimming', 'sports', 'athlete', 'wellness', 'lifestyle',
            'crossfit', 'bodybuilding', 'weightlifting', 'stretching',
            'meditation', 'healthy', 'organic', 'natural', 'fresh'
        ]
        
        # Load ImageNet labels
        self.labels_path = tf.keras.utils.get_file(
            'ImageNetLabels.txt',
            'https://storage.googleapis.com/download.tensorflow.org/data/ImageNetLabels.txt'
        )
        self.imagenet_labels = np.array(open(self.labels_path).read().splitlines())

    def preprocess_image(self, image_bytes):
        image = Image.open(io.BytesIO(image_bytes))
        image = image.convert('RGB')
        image = image.resize((224, 224))
        image = np.array(image) / 255.0
        return np.expand_dims(image, axis=0), image

    def extract_text(self, image):
        # Convert PIL image to cv2 format
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Ensure the image is in the correct format
        if opencv_image.dtype != np.uint8:
            opencv_image = (opencv_image * 255).astype(np.uint8)  # Convert to 8-bit format
        
        # Extract text using pytesseract
        text = pytesseract.image_to_string(opencv_image).lower()
        return text

    def contains_fitness_keyword(self, text):
        return any(keyword in text.lower() for keyword in self.fitness_keywords)

    def is_fitness_related(self, image_bytes, confidence_threshold=0.2):
        try:
            # Preprocess image
            image_tensor, original_image = self.preprocess_image(image_bytes)
            
            # Get predictions from MobileNet
            predictions = self.model.predict(image_tensor)
            predicted_label = self.imagenet_labels[np.argmax(predictions[0])]
            confidence = np.max(predictions[0])
            
            print(f"Predicted Label: {predicted_label}, Confidence: {confidence}")  # Debugging output
            
            # Check if prediction is in allowed categories
            is_allowed = any(category.lower() in predicted_label.lower() 
                             for category in self.allowed_categories)
            
            # If not immediately allowed, check for text in image
            if not is_allowed or confidence < confidence_threshold:
                extracted_text = self.extract_text(original_image)
                print(f"Extracted Text: {extracted_text}")  # Debugging output
                
                if self.contains_fitness_keyword(extracted_text):
                    return True, f"Fitness text detected: {extracted_text[:50]}...", 1.0
            
            if is_allowed and confidence >= confidence_threshold:
                return True, predicted_label, confidence
            
            # If still not validated, check for person/people with lower confidence
            if 'person' in predicted_label.lower() or 'people' in predicted_label.lower():
                return True, "Person detected in fitness context", confidence
            
            return False, predicted_label, confidence
            
        except Exception as e:
            print(f"Error validating image: {str(e)}")
            return False, "Error", 0.0 
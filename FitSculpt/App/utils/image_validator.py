import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
from PIL import Image
import io
import pytesseract
import cv2
from typing import Tuple, Optional, List, Union
import logging
import os
import tempfile
import requests
from pathlib import Path
import time
import psutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageValidator:
    """A class to validate fitness-related images using MobileNet and text extraction."""

    MOBILENET_URL = "https://tfhub.dev/google/imagenet/mobilenet_v2_100_224/classification/4"
    IMAGENET_LABELS_URL = "https://storage.googleapis.com/download.tensorflow.org/data/ImageNetLabels.txt"
    FALLBACK_MODEL_URL = "https://tfhub.dev/google/imagenet/mobilenet_v2_035_96/classification/5"  # Smaller model
    
    def __init__(self, model_url: Optional[str] = None, cache_dir: Optional[str] = None, max_retries: int = 3):
        """
        Initialize the ImageValidator with MobileNet model and predefined categories.
        
        Args:
            model_url (Optional[str]): Custom URL for the MobileNet model.
            cache_dir (Optional[str]): Directory to cache the model and labels.
            max_retries (int): Maximum number of retries for model initialization.
        
        Raises:
            RuntimeError: If model loading fails after all retries.
        """
        # Print TensorFlow and TensorFlow Hub versions for debugging
        logger.info(f"TensorFlow version: {tf.__version__}")
        logger.info(f"TensorFlow Hub version: {hub.__version__}")
        
        self.cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), 'fitsculpt_cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize model with retries
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                self._initialize_model(model_url or self.MOBILENET_URL)
                break
            except Exception as e:
                last_error = e
                retry_count += 1
                logger.warning(f"Retry {retry_count}/{max_retries} failed: {str(e)}")
                time.sleep(1)
                
                if retry_count == max_retries - 1:  # Last retry, attempt fallback
                    try:
                        logger.info("Attempting to load lightweight fallback model...")
                        self._initialize_model(self.FALLBACK_MODEL_URL)
                        break
                    except Exception as fallback_error:
                        last_error = fallback_error
                        logger.error("Fallback model failed to load")
        
        if not hasattr(self, 'model'):
            raise RuntimeError(f"Failed to initialize model after {max_retries} attempts: {str(last_error)}")
        
        # Define allowed categories and keywords
        self.allowed_categories: List[str] = [
            'dumbbell', 'barbell', 'weight', 'gym', 'treadmill', 'bicycle',
            'yoga', 'protein', 'salad', 'food', 'fruit', 'vegetable',
            'running', 'fitness', 'sports', 'exercise', 'workout',
            'training', 'athlete', 'muscle', 'stretching', 'jumping',
            'swimming', 'cycling', 'jogging', 'lifting', 'crossfit',
            'meditation', 'nutrition', 'diet', 'health', 'wellness',
            'person', 'people', 'human', 'man', 'woman', 'sportswear'
        ]
        
        self.fitness_keywords: List[str] = [
            'fitness', 'gym', 'workout', 'exercise', 'training',
            'health', 'nutrition', 'diet', 'protein', 'muscle',
            'cardio', 'strength', 'yoga', 'running', 'cycling',
            'swimming', 'sports', 'athlete', 'wellness', 'lifestyle',
            'crossfit', 'bodybuilding', 'weightlifting', 'stretching',
            'meditation', 'healthy', 'organic', 'natural', 'fresh'
        ]
        
        # Load ImageNet labels
        self._initialize_labels()

    def _download_file(self, url: str, local_path: str) -> bool:
        """Download a file from URL to local path with retry mechanism."""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()
                
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    logger.error(f"Failed to download file from {url} after {max_retries} attempts: {str(e)}")
                    return False
                logger.warning(f"Download attempt {retry_count} failed, retrying...")
                time.sleep(1)  # Wait before retrying

    def _initialize_model(self, model_url: str):
        """Initialize the MobileNet model with fallback options."""
        try:
            # Check if model is cached
            model_name = Path(model_url).name or 'mobilenet_v2'
            model_path = os.path.join(self.cache_dir, model_name)
            
            if os.path.exists(model_path):
                try:
                    # Try loading from cache first
                    self.model = tf.keras.models.load_model(model_path)
                    logger.info("Model loaded from cache successfully")
                    return
                except Exception as cache_error:
                    logger.warning(f"Failed to load from cache: {str(cache_error)}")
                    # If cache is corrupted, delete it
                    import shutil
                    shutil.rmtree(model_path, ignore_errors=True)
            
            # If no cache or cache failed, download and create model
            logger.info("Downloading model...")
            
            # Create model using functional API instead of Sequential
            try:
                # First attempt: Use newer TF Hub approach
                input_layer = tf.keras.layers.Input(shape=(224, 224, 3), dtype=tf.float32)
                hub_layer = hub.KerasLayer(model_url, trainable=False)
                output_layer = hub_layer(input_layer)
                self.model = tf.keras.Model(inputs=input_layer, outputs=output_layer)
            except Exception as e1:
                logger.warning(f"Failed to load with newer approach: {str(e1)}")
                try:
                    # Second attempt: Use older TF Hub approach
                    handle = hub.load(model_url)
                    self.model = handle
                except Exception as e2:
                    logger.warning(f"Failed to load with older approach: {str(e2)}")
                    # Final attempt: Try direct module loading with minimal wrapper
                    self.model = hub.load(model_url)
            
            # Test the model with a dummy input
            dummy_input = np.zeros((1, 224, 224, 3), dtype=np.float32)
            if isinstance(self.model, tf.keras.Model):
                self.model.predict(dummy_input, verbose=0)
            else:
                self.model(dummy_input, training=False, batch_norm_momentum=0.99)
            
            # Only save if it's a Keras model
            if isinstance(self.model, tf.keras.Model):
                os.makedirs(model_path, exist_ok=True)
                self.model.save(model_path)
                logger.info("Model downloaded and cached successfully")
            else:
                logger.info("Model loaded successfully (not cached - using TF Hub directly)")
            
        except Exception as e:
            logger.error(f"Model initialization failed: {str(e)}")
            raise RuntimeError(f"Failed to initialize model: {str(e)}")

    def _initialize_labels(self):
        """Initialize ImageNet labels with fallback options."""
        try:
            # Try to load labels from cache or download
            labels_path = os.path.join(self.cache_dir, 'ImageNetLabels.txt')
            
            if not os.path.exists(labels_path):
                logger.info("Downloading ImageNet labels...")
                if not self._download_file(self.IMAGENET_LABELS_URL, labels_path):
                    raise RuntimeError("Failed to download ImageNet labels")
            
            self.imagenet_labels = np.array(open(labels_path).read().splitlines())
            if len(self.imagenet_labels) == 0:
                raise ValueError("Empty labels file")
                
            logger.info("ImageNet labels loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load ImageNet labels: {str(e)}")
            # Fallback to a minimal set of labels if loading fails
            self.imagenet_labels = np.array([
                'unknown', 'person', 'people', 'sports_equipment',
                'food', 'clothing', 'exercise_equipment'
            ])
            logger.warning("Using fallback labels due to loading failure")

    def preprocess_image(self, image_bytes: bytes) -> Tuple[np.ndarray, Image.Image]:
        """
        Preprocess the image for model prediction.
        
        Args:
            image_bytes (bytes): Raw image bytes.
            
        Returns:
            Tuple[np.ndarray, Image.Image]: Preprocessed image tensor and original PIL image.
            
        Raises:
            ValueError: If image processing fails.
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image = image.convert('RGB')
            image = image.resize((224, 224))
            # Convert to float32 explicitly
            image_array = np.array(image, dtype=np.float32) / 255.0
            return np.expand_dims(image_array, axis=0), image
        except Exception as e:
            logger.error(f"Failed to preprocess image: {str(e)}")
            raise ValueError("Invalid image format or corrupted image data") from e

    def extract_text(self, image: Image.Image) -> str:
        """
        Extract text from the image using OCR.
        
        Args:
            image (Image.Image): PIL Image to extract text from.
            
        Returns:
            str: Extracted text from the image.
        """
        try:
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            if opencv_image.dtype != np.uint8:
                opencv_image = (opencv_image * 255).astype(np.uint8)
            
            text = pytesseract.image_to_string(opencv_image).lower()
            return text
        except Exception as e:
            logger.warning(f"Text extraction failed: {str(e)}")
            return ""

    def contains_fitness_keyword(self, text: str) -> bool:
        """
        Check if text contains any fitness-related keywords.
        
        Args:
            text (str): Text to check for keywords.
            
        Returns:
            bool: True if fitness keywords are found.
        """
        return any(keyword in text.lower() for keyword in self.fitness_keywords)

    def is_fitness_related(self, image_bytes: bytes, confidence_threshold: float = 0.2) -> Tuple[bool, str, float]:
        """
        Determine if an image is fitness-related using model prediction and text extraction.
        
        Args:
            image_bytes (bytes): Raw image bytes.
            confidence_threshold (float): Minimum confidence threshold for predictions.
            
        Returns:
            Tuple[bool, str, float]: (is_valid, reason, confidence_score)
            
        Raises:
            ValueError: If image validation fails.
        """
        try:
            # Preprocess image
            image_tensor, original_image = self.preprocess_image(image_bytes)
            
            # Get predictions based on model type
            if isinstance(self.model, tf.keras.Model):
                predictions = self.model.predict(image_tensor, verbose=0)
            else:
                # For TF Hub module, ensure input is float32 and handle batch norm params
                image_tensor = tf.cast(image_tensor, tf.float32)
                predictions = self.model(image_tensor, training=False, batch_norm_momentum=0.99)
                if isinstance(predictions, dict):
                    predictions = predictions['logits']
                predictions = predictions.numpy()
            
            predicted_label = self.imagenet_labels[np.argmax(predictions[0])]
            confidence = float(np.max(predictions[0]))
            
            logger.info(f"Predicted Label: {predicted_label}, Confidence: {confidence}")
            
            # Check if prediction is in allowed categories
            is_allowed = any(category.lower() in predicted_label.lower() 
                           for category in self.allowed_categories)
            
            # Primary validation: high confidence prediction
            if is_allowed and confidence >= confidence_threshold:
                return True, f"Detected: {predicted_label}", confidence
            
            # Secondary validation: text detection
            extracted_text = self.extract_text(original_image)
            logger.info(f"Extracted Text: {extracted_text[:100]}...")
            
            if self.contains_fitness_keyword(extracted_text):
                return True, f"Fitness text detected: {extracted_text[:50]}...", 1.0
            
            # Tertiary validation: person detection with lower confidence
            if confidence >= confidence_threshold * 0.5 and (
                'person' in predicted_label.lower() or 
                'people' in predicted_label.lower()
            ):
                return True, "Person detected in fitness context", confidence
            
            return False, f"Not fitness-related: {predicted_label}", confidence
            
        except Exception as e:
            logger.error(f"Image validation failed: {str(e)}")
            raise ValueError(f"Failed to validate image: {str(e)}")

try:
    validator = ImageValidator(
        cache_dir="/path/to/cache",  # Optional: specify custom cache directory
        max_retries=3  # Optional: customize number of retries
    )
except RuntimeError as e:
    print(f"Failed to initialize validator: {e}")

try:
    response = requests.get("https://www.google.com", timeout=5)
    print("Network is available")
except:
    print("Network connection issue")

cache_dir = os.path.join(tempfile.gettempdir(), 'fitsculpt_cache')
print(f"Can write to cache: {os.access(cache_dir, os.W_OK)}")

print(f"Available memory: {psutil.virtual_memory().available / (1024*1024*1024):.2f} GB") 
import re
from better_profanity import profanity
from textblob import TextBlob

class ContentModerator:
    def __init__(self):
        # Initialize profanity filter with custom words
        profanity.load_censor_words()
        
        # Add fitness-specific inappropriate terms
        custom_badwords = [
            # Add any custom inappropriate terms specific to fitness context
        ]
        profanity.add_censor_words(custom_badwords)
        
        # Toxic language patterns
        self.toxic_patterns = [
            r'kill\s*(yourself|ur self)',
            r'die\s*',
            r'hate\s*you',
            r'kys',
            r'suicide',
            r'(fat|ugly)\s*shame',
            r'harassment',
            r'bully',
            r'threat'
        ]
        
        # Spam patterns
        self.spam_patterns = [
            r'(buy|sell|discount|offer|click|win|earn).*(http|www|\.com)',
            r'(http|www|\.com)',
            r'\$\d+',
            r'(diet|weight loss) miracle',
            r'(miracle|magic|quick) (cure|fix|solution)',
            r'(earn|make) money',
            r'subscribe|follow me|check out my'
        ]

    def is_appropriate(self, text):
        """
        Check if the comment is appropriate.
        Returns (is_appropriate, reason)
        """
        if not text or len(text.strip()) == 0:
            return False, "Comment cannot be empty"
            
        # Check length
        if len(text) > 500:
            return False, "Comment is too long (max 500 characters)"
            
        # Check for profanity
        if profanity.contains_profanity(text):
            return False, "Comment contains inappropriate language"
        
        # Check for toxic language patterns
        for pattern in self.toxic_patterns:
            if re.search(pattern, text.lower()):
                return False, "Comment contains harmful or toxic language"
        
        # Check for spam patterns
        for pattern in self.spam_patterns:
            if re.search(pattern, text.lower()):
                return False, "Comment appears to be spam or advertising"
        
        # Sentiment analysis
        blob = TextBlob(text)
        if blob.sentiment.polarity < -0.7:  # Very negative sentiment
            return False, "Comment appears to be overly negative or hostile"
        
        # Check for excessive capitalization (shouting)
        caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
        if len(text) > 10 and caps_ratio > 0.7:
            return False, "Please don't use excessive capital letters"
        
        # Check for repetitive characters
        if re.search(r'(.)\1{4,}', text):
            return False, "Please avoid repeating characters excessively"
        
        return True, "OK"

    def clean_text(self, text):
        """
        Clean and format the text while preserving fitness-related terms
        """
        # Preserve fitness-related terms that might contain numbers
        preserved_terms = [
            'c25k', '5x5', '5/3/1', '3x10', '4x8',
            'b12', 'vitamin d3', 'omega3'
        ]
        
        # Temporarily replace preserved terms
        preserved_dict = {}
        for i, term in enumerate(preserved_terms):
            if term in text.lower():
                placeholder = f"PRESERVED{i}"
                preserved_dict[placeholder] = term
                text = text.lower().replace(term, placeholder)
        
        # Clean the text
        text = re.sub(r'[^\w\s.,!?-]', '', text)  # Remove special characters
        text = re.sub(r'\s+', ' ', text)  # Remove extra whitespace
        text = text.strip()
        
        # Restore preserved terms
        for placeholder, term in preserved_dict.items():
            text = text.replace(placeholder.lower(), term)
        
        return text 
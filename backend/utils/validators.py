import bleach
from html import escape
import re

class InputValidator:
    # Whitelist allowed HTML tags for bios/descriptions
    ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'a']
    
    @staticmethod
    def sanitize_text(text):
        """Remove XSS attacks from text fields"""
        if not text:
            return text
        # Remove all tags for plain text fields
        cleaned = bleach.clean(str(text), tags=[], strip=True)
        return escape(cleaned)
    
    @staticmethod
    def sanitize_html(html_content):
        """Clean HTML but preserve safe tags for formatted text"""
        if not html_content:
            return html_content
        return bleach.clean(
            str(html_content),
            tags=InputValidator.ALLOWED_TAGS,
            strip=True
        )
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        if not email: return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, str(email)) is not None
    
    @staticmethod
    def validate_phone(phone):
        """Validate Indian phone number (10 digits)"""
        if not phone: return False
        clean_phone = str(phone).replace('-', '').replace(' ', '').replace('+91', '')
        pattern = r'^[6-9][0-9]{9}$'
        return re.match(pattern, clean_phone) is not None
    
    @staticmethod
    def validate_gst(gst):
        """Validate Indian GST format"""
        if not gst: return False
        pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[A-Z0-9]{1}[Z]{1}[0-9A-Z]{1}$'
        return re.match(pattern, str(gst)) is not None
    
    @staticmethod
    def validate_aadhar(aadhar):
        """Validate Aadhar format (12 digits)"""
        if not aadhar: return False
        aadhar_clean = str(aadhar).replace('-', '').replace(' ', '')
        return len(aadhar_clean) == 12 and aadhar_clean.isdigit()

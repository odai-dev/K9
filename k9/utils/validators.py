"""
Validation utilities for K9 system
"""
import re


def validate_yemen_phone(phone):
    """
    Validate Yemen phone number format.
    
    Accepts only local format: 9 digits starting with 77, 78, 73, 70, or 71
    No spaces or special characters allowed.
    
    Args:
        phone (str): Phone number to validate
        
    Returns:
        tuple: (is_valid, error_message)
            - is_valid (bool): True if valid, False otherwise
            - error_message (str): Arabic error message if invalid, None if valid
    """
    if not phone:
        return False, "رقم الهاتف مطلوب"
    
    # Remove any whitespace
    phone = phone.strip()
    
    # Check if it contains only digits
    if not phone.isdigit():
        return False, "رقم الهاتف يجب أن يحتوي على أرقام فقط (بدون مسافات أو رموز)"
    
    # Check exact length (9 digits)
    if len(phone) != 9:
        return False, "رقم الهاتف يجب أن يكون 9 أرقام بالضبط"
    
    # Check if it starts with valid Yemen mobile prefixes
    valid_prefixes = ['77', '78', '73', '70', '71']
    if not any(phone.startswith(prefix) for prefix in valid_prefixes):
        return False, "رقم الهاتف يجب أن يبدأ بـ: 77 أو 78 أو 73 أو 70 أو 71"
    
    return True, None


def format_phone_for_display(phone):
    """
    Format phone number for display (add spaces for readability).
    
    Args:
        phone (str): Phone number (9 digits)
        
    Returns:
        str: Formatted phone number (e.g., "771234567" -> "77 123 4567")
    """
    if not phone or len(phone) != 9:
        return phone
    
    return f"{phone[:2]} {phone[2:5]} {phone[5:]}"

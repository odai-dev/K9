"""
Range resolution utilities for unified K9 reports
Handles date range parsing and aggregation strategy determination
"""

from datetime import date, datetime, timedelta
import calendar
from typing import Tuple, Dict, Any, Union


def parse_date_string(date_str: str) -> date:
    """Parse date string in YYYY-MM-DD format to date object"""
    if not date_str:
        raise ValueError("Date string cannot be empty")
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD")


def resolve_range(range_type: str, params: Dict[str, Any]) -> Tuple[date, date, str]:
    """
    Resolve date range and determine aggregation strategy
    
    Args:
        range_type: "daily", "weekly", "monthly", or "custom"
        params: Dictionary containing date parameters
        
    Returns:
        Tuple of (date_from, date_to, granularity) where granularity ∈ {"day","week","month","custom"}
        
    Raises:
        ValueError: If required parameters are missing or invalid
    """
    today = date.today()

    if range_type == "daily":
        date_param = params.get("date")
        if not date_param:
            raise ValueError("date required for daily range")
        
        target_date = parse_date_string(date_param) if isinstance(date_param, str) else date_param
        return (target_date, target_date, "day")

    elif range_type == "weekly":
        week_start_param = params.get("week_start")
        if not week_start_param:
            raise ValueError("week_start (Monday) required for weekly range")
        
        week_start = parse_date_string(week_start_param) if isinstance(week_start_param, str) else week_start_param
        
        # Validate it's a Monday
        if week_start.weekday() != 0:
            raise ValueError("week_start must be a Monday")
            
        # Calculate week end (inclusive Sunday)
        week_end = week_start + timedelta(days=6)
        return (week_start, week_end, "week")

    elif range_type == "monthly":
        year_month_param = params.get("year_month")
        if not year_month_param:
            raise ValueError("year_month (YYYY-MM format) required for monthly range")
        
        try:
            year, month = map(int, year_month_param.split("-"))
        except ValueError:
            raise ValueError("year_month must be in YYYY-MM format")
            
        # Calculate first and last day of month
        first_day = date(year, month, 1)
        last_day_num = calendar.monthrange(year, month)[1]
        last_day = date(year, month, last_day_num)
        
        return (first_day, last_day, "month")

    elif range_type == "custom":
        date_from_param = params.get("date_from")
        date_to_param = params.get("date_to")
        
        if not date_from_param or not date_to_param:
            raise ValueError("date_from and date_to required for custom range")
        
        date_from = parse_date_string(date_from_param) if isinstance(date_from_param, str) else date_from_param
        date_to = parse_date_string(date_to_param) if isinstance(date_to_param, str) else date_to_param
        
        # Swap if needed
        if date_from > date_to:
            date_from, date_to = date_to, date_from
            
        return (date_from, date_to, "custom")

    else:
        raise ValueError(f"Invalid range_type: {range_type}. Must be one of: daily, weekly, monthly, custom")


def get_aggregation_strategy(date_from: date, date_to: date, range_type: str) -> str:
    """
    Determine aggregation strategy based on date range and type
    
    Args:
        date_from: Start date
        date_to: End date  
        range_type: The original range type requested
        
    Returns:
        Aggregation strategy: "daily", "weekly", or "monthly"
    """
    if range_type == "daily":
        return "daily"
    elif range_type == "weekly":
        return "weekly"
    elif range_type == "monthly":
        return "monthly"
    elif range_type == "custom":
        # Custom range logic: ≤31 days = daily, >31 days = weekly
        days_diff = (date_to - date_from).days + 1  # +1 for inclusive range
        return "daily" if days_diff <= 31 else "weekly"
    else:
        raise ValueError(f"Unknown range_type: {range_type}")


def get_week_boundaries(target_date: date) -> Tuple[date, date]:
    """
    Get Monday-Sunday boundaries for a given date
    
    Args:
        target_date: Any date within the target week
        
    Returns:
        Tuple of (monday_date, sunday_date)
    """
    days_since_monday = target_date.weekday()
    monday = target_date - timedelta(days=days_since_monday)
    sunday = monday + timedelta(days=6)
    return (monday, sunday)


def get_month_boundaries(target_date: date) -> Tuple[date, date]:
    """
    Get first and last day of month for a given date
    
    Args:
        target_date: Any date within the target month
        
    Returns:
        Tuple of (first_day, last_day)
    """
    first_day = target_date.replace(day=1)
    last_day_num = calendar.monthrange(target_date.year, target_date.month)[1]
    last_day = target_date.replace(day=last_day_num)
    return (first_day, last_day)


def format_date_range_for_display(date_from: date, date_to: date, range_type: str, locale: str = "ar") -> str:
    """
    Format date range for display in UI
    
    Args:
        date_from: Start date
        date_to: End date
        range_type: Original range type
        locale: Display locale ("ar" for Arabic, "en" for English)
        
    Returns:
        Formatted date range string
    """
    if locale == "ar":
        months_ar = [
            "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
            "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
        ]
        
        if range_type == "daily":
            return f"{date_from.day} {months_ar[date_from.month-1]} {date_from.year}"
        elif range_type == "monthly" and date_from.month == date_to.month:
            return f"{months_ar[date_from.month-1]} {date_from.year}"
        else:
            from_str = f"{date_from.day} {months_ar[date_from.month-1]} {date_from.year}"
            to_str = f"{date_to.day} {months_ar[date_to.month-1]} {date_to.year}"
            return f"من {from_str} إلى {to_str}"
    else:
        # English format
        if range_type == "daily":
            return date_from.strftime("%B %d, %Y")
        elif range_type == "monthly" and date_from.month == date_to.month:
            return date_from.strftime("%B %Y")
        else:
            return f"{date_from.strftime('%B %d, %Y')} to {date_to.strftime('%B %d, %Y')}"


def generate_export_filename(module: str, project_code: str, date_from: date, date_to: date, extension: str = "pdf") -> str:
    """
    Generate filename for report exports
    
    Format: breeding_{module}_{projectCode|all}_{YYYY-MM-DD}_to_{YYYY-MM-DD}.pdf
    Example: breeding_checkup_PRJ-ALPHA_2025-09-01_to_2025-09-30.pdf
    
    Args:
        module: Report module ("checkup" or "feeding")
        project_code: Project code or "all" for all projects
        date_from: Start date
        date_to: End date
        extension: File extension (default: "pdf")
        
    Returns:
        Generated filename
    """
    project_part = project_code if project_code else "all"
    date_from_str = date_from.strftime("%Y-%m-%d")
    date_to_str = date_to.strftime("%Y-%m-%d")
    
    return f"breeding_{module}_{project_part}_{date_from_str}_to_{date_to_str}.{extension}"


def validate_range_params(range_type: str, params: Dict[str, Any]) -> Dict[str, str]:
    """
    Validate and return normalized range parameters
    
    Args:
        range_type: The range type to validate
        params: Raw parameters from request
        
    Returns:
        Dictionary of validation errors (empty if valid)
    """
    errors = {}
    
    if range_type == "daily":
        if not params.get("date"):
            errors["date"] = "التاريخ مطلوب للتقرير اليومي"
        else:
            try:
                parse_date_string(params["date"])
            except ValueError:
                errors["date"] = "تنسيق التاريخ غير صحيح"
                
    elif range_type == "weekly":
        if not params.get("week_start"):
            errors["week_start"] = "بداية الأسبوع مطلوبة للتقرير الأسبوعي"
        else:
            try:
                week_start = parse_date_string(params["week_start"])
                if week_start.weekday() != 0:
                    errors["week_start"] = "بداية الأسبوع يجب أن تكون يوم الاثنين"
            except ValueError:
                errors["week_start"] = "تنسيق تاريخ بداية الأسبوع غير صحيح"
                
    elif range_type == "monthly":
        if not params.get("year_month"):
            errors["year_month"] = "الشهر والسنة مطلوبان للتقرير الشهري"
        else:
            try:
                year, month = map(int, params["year_month"].split("-"))
                if not (1 <= month <= 12):
                    errors["year_month"] = "رقم الشهر غير صحيح"
                if year < 2020 or year > 2030:  # Reasonable range
                    errors["year_month"] = "السنة خارج النطاق المسموح"
            except (ValueError, AttributeError):
                errors["year_month"] = "تنسيق الشهر والسنة غير صحيح (YYYY-MM)"
                
    elif range_type == "custom":
        if not params.get("date_from"):
            errors["date_from"] = "تاريخ البداية مطلوب للفترة المخصصة"
        if not params.get("date_to"):
            errors["date_to"] = "تاريخ النهاية مطلوب للفترة المخصصة"
            
        if not errors.get("date_from") and not errors.get("date_to"):
            try:
                date_from = parse_date_string(params["date_from"])
                date_to = parse_date_string(params["date_to"])
                
                if date_from > date_to:
                    errors["date_range"] = "تاريخ البداية يجب أن يكون قبل تاريخ النهاية"
                    
                # Check for reasonable range (max 1 year)
                if (date_to - date_from).days > 365:
                    errors["date_range"] = "الفترة الزمنية لا يمكن أن تتجاوز سنة واحدة"
                    
            except ValueError as e:
                errors["date_format"] = "تنسيق التاريخ غير صحيح"
                
    else:
        errors["range_type"] = f"نوع الفترة غير صحيح: {range_type}"
    
    return errors
"""
Amount extraction and calculation module
"""
import re
import logging
from typing import List
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)


def extract_amount_candidates(ocr_text: str) -> List[Decimal]:
    """
    Extract numeric amount candidates from OCR text
    
    Args:
        ocr_text: Text extracted from OCR
        
    Returns:
        List of amount candidates sorted in descending order
    """
    if not ocr_text:
        return []
    
    # Pattern to match various numeric formats
    # Matches: 1,234.56 / 1.234,56 / 1 234.56 / 1234.56 / 1234 etc.
    pattern = r'(\d{1,3}(?:[,.\s]\d{3})*(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?)'
    
    candidates = set()
    
    for match in re.finditer(pattern, ocr_text):
        token = match.group(0)
        parsed_values = parse_numeric(token)
        
        for value in parsed_values:
            # Filter reasonable amounts (1 to 10,000,000)
            if Decimal('1') <= value <= Decimal('10000000'):
                candidates.add(value)
    
    # Sort in descending order (largest amounts first)
    sorted_candidates = sorted(candidates, reverse=True)
    
    logger.info(f"Found {len(sorted_candidates)} amount candidates")
    return sorted_candidates


def parse_numeric(token: str) -> List[Decimal]:
    """
    Parse numeric token with ambiguous formats
    
    Args:
        token: Numeric string token
        
    Returns:
        List of possible decimal values (handles ambiguous cases)
    """
    if not token:
        return []
    
    results = []
    
    # Remove spaces
    token = token.replace(' ', '')
    
    # Count dots and commas
    dot_count = token.count('.')
    comma_count = token.count(',')
    
    try:
        if dot_count == 0 and comma_count == 0:
            # Simple integer
            results.append(Decimal(token))
            
        elif dot_count == 1 and comma_count == 0:
            # Dot as decimal separator
            results.append(Decimal(token))
            
        elif dot_count == 0 and comma_count == 1:
            # Check if comma is thousand separator or decimal separator
            parts = token.split(',')
            if len(parts[1]) == 3:
                # Likely thousand separator (e.g., 1,234)
                results.append(Decimal(token.replace(',', '')))
            else:
                # Likely decimal separator (e.g., 12,34)
                results.append(Decimal(token.replace(',', '.')))
                
        elif dot_count > 0 and comma_count > 0:
            # Mixed format - determine which is decimal separator
            last_dot = token.rfind('.')
            last_comma = token.rfind(',')
            
            if last_dot > last_comma:
                # Dot is decimal separator, comma is thousand separator
                normalized = token.replace(',', '').replace(' ', '')
                results.append(Decimal(normalized))
            else:
                # Comma is decimal separator, dot is thousand separator
                normalized = token.replace('.', '').replace(',', '.')
                results.append(Decimal(normalized))
                
        elif dot_count > 1:
            # Multiple dots - thousand separators
            normalized = token.replace('.', '')
            results.append(Decimal(normalized))
            
        elif comma_count > 1:
            # Multiple commas - thousand separators
            normalized = token.replace(',', '')
            results.append(Decimal(normalized))
            
    except:
        # If parsing fails, return empty list
        pass
    
    return results


def split_per_person(total: Decimal, people: int, scale: int = 2) -> Decimal:
    """
    Calculate per-person amount for bill splitting
    
    Args:
        total: Total amount to split
        people: Number of people
        scale: Decimal places for rounding (default 2)
        
    Returns:
        Amount per person rounded to specified decimal places
    """
    if people <= 0:
        raise ValueError("Number of people must be positive")
    
    per_person = total / Decimal(people)
    
    # Round to specified decimal places using banker's rounding
    quantize_exp = Decimal(10) ** -scale
    rounded = per_person.quantize(quantize_exp, rounding=ROUND_HALF_UP)
    
    return rounded
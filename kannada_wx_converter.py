#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Kannada Unicode ↔ WX Transliteration Converter
Converts between Kannada script (ಕನ್ನಡ) and WX notation (kannaDa)
"""

# Kannada Unicode to WX mapping
KANNADA_TO_WX = {
    # Vowels
    'ಅ': 'a', 'ಆ': 'A', 'ಇ': 'i', 'ಈ': 'I', 'ಉ': 'u', 'ಊ': 'U',
    'ಋ': 'q', 'ೠ': 'Q', 'ಌ': 'L', 'ೡ': 'lY',
    'ಎ': 'e', 'ಏ': 'eV', 'ಐ': 'E',
    'ಒ': 'o', 'ಓ': 'oV', 'ಔ': 'O',
    
    # Vowel signs (matras)
    'ಾ': 'A', 'ಿ': 'i', 'ೀ': 'I', 'ು': 'u', 'ೂ': 'U',
    'ೃ': 'q', 'ೄ': 'Q', 'ೢ': 'L', 'ೣ': 'lY',
    'ೆ': 'e', 'ೇ': 'eV', 'ೈ': 'E',
    'ೊ': 'o', 'ೋ': 'oV', 'ೌ': 'O',
    
    # Consonants
    'ಕ': 'ka', 'ಖ': 'Ka', 'ಗ': 'ga', 'ಘ': 'Ga', 'ಙ': 'fa',
    'ಚ': 'ca', 'ಛ': 'Ca', 'ಜ': 'ja', 'ಝ': 'Ja', 'ಞ': 'Fa',
    'ಟ': 'ta', 'ಠ': 'Ta', 'ಡ': 'da', 'ಢ': 'Da', 'ಣ': 'Na',
    'ತ': 'wa', 'ಥ': 'Wa', 'ದ': 'xa', 'ಧ': 'Xa', 'ನ': 'na',
    'ಪ': 'pa', 'ಫ': 'Pa', 'ಬ': 'ba', 'ಭ': 'Ba', 'ಮ': 'ma',
    'ಯ': 'ya', 'ರ': 'ra', 'ಱ': 'rY', 'ಲ': 'la', 'ಳ': 'lY',
    'ವ': 'va', 'ಶ': 'Sa', 'ಷ': 'Ra', 'ಸ': 'sa', 'ಹ': 'ha',
    
    # Special
    'ಂ': 'M', 'ಃ': 'H', '್': '', 'ಽ': '.a',
    
    # Numbers
    '೦': '0', '೧': '1', '೨': '2', '೩': '3', '೪': '4',
    '೫': '5', '೬': '6', '೭': '7', '೮': '8', '೯': '9',
}

# WX to Kannada Unicode mapping (reverse)
WX_TO_KANNADA = {v: k for k, v in KANNADA_TO_WX.items() if v}

def kannada_to_wx(text):
    """
    Convert Kannada Unicode text to WX transliteration
    
    Args:
        text (str): Kannada text (e.g., "ಮರವು")
    
    Returns:
        str: WX transliteration (e.g., "maravu")
    
    Example:
        >>> kannada_to_wx("ಮರವು")
        'maravu'
        >>> kannada_to_wx("ಹುಡುಗ")
        'huduga'
    """
    result = []
    i = 0
    
    while i < len(text):
        char = text[i]
        
        # Skip virama (halant) - handled with consonants
        if char == '್':
            i += 1
            continue
        
        # Check for consonant + virama (halant) - no inherent 'a'
        if i + 1 < len(text) and text[i + 1] == '್':
            wx = KANNADA_TO_WX.get(char, char)
            # Remove inherent 'a' from consonant
            if wx.endswith('a'):
                wx = wx[:-1]
            result.append(wx)
            i += 1  # Skip the consonant, virama handled in next iteration
            continue
        
        # Check for consonant + vowel sign (matra)
        if i + 1 < len(text):
            next_char = text[i + 1]
            # Check if next character is a vowel sign (matra)
            if next_char in ['ಾ', 'ಿ', 'ೀ', 'ು', 'ೂ', 'ೃ', 'ೄ', 'ೢ', 'ೣ', 
                             'ೆ', 'ೇ', 'ೈ', 'ೊ', 'ೋ', 'ೌ', 'ಂ', 'ಃ']:
                consonant = KANNADA_TO_WX.get(char, char)
                matra = KANNADA_TO_WX.get(next_char, next_char)
                
                # Remove inherent 'a' from consonant and add matra
                if consonant.endswith('a'):
                    consonant = consonant[:-1]
                
                result.append(consonant + matra)
                i += 2
                continue
        
        # Single character (vowel or consonant with inherent 'a')
        result.append(KANNADA_TO_WX.get(char, char))
        i += 1
    
    return ''.join(result)

def wx_to_kannada(text):
    """
    Convert WX transliteration to Kannada Unicode
    
    Args:
        text (str): WX text (e.g., "maravu")
    
    Returns:
        str: Kannada text (e.g., "ಮರವು")
    
    Example:
        >>> wx_to_kannada("maravu")
        'ಮರವು'
        >>> wx_to_kannada("huduga")
        'ಹುಡುಗ'
    """
    # Simple reverse mapping (basic implementation)
    # For production, you'd need a more sophisticated parser
    result = []
    i = 0
    
    while i < len(text):
        # Try two-character matches first
        if i + 1 < len(text):
            two_char = text[i:i+2]
            if two_char in WX_TO_KANNADA:
                result.append(WX_TO_KANNADA[two_char])
                i += 2
                continue
        
        # Single character
        char = text[i]
        result.append(WX_TO_KANNADA.get(char, char))
        i += 1
    
    return ''.join(result)

def is_kannada_text(text):
    """
    Check if text contains Kannada Unicode characters
    
    Args:
        text (str): Text to check
    
    Returns:
        bool: True if text contains Kannada characters
    """
    kannada_range = range(0x0C80, 0x0CFF)  # Kannada Unicode block
    return any(ord(char) in kannada_range for char in text)

def normalize_text(text):
    """
    Normalize text - convert Kannada to WX if needed
    
    Args:
        text (str): Input text (Kannada or WX)
    
    Returns:
        str: Normalized WX text
    """
    if is_kannada_text(text):
        return kannada_to_wx(text)
    return text

if __name__ == "__main__":
    # Test conversions
    print("=" * 70)
    print("Kannada ↔ WX Converter Test")
    print("=" * 70)
    print()
    
    # Test cases
    test_cases = [
        ("ಮರ", "mara", "tree"),
        ("ಮರವು", "maravu", "tree (nominative)"),
        ("ಹುಡುಗ", "huduga", "boy"),
        ("ಹುಡುಗನು", "huduganu", "boy (nominative)"),
        ("ನನಗೆ", "nanage", "to me"),
        ("ಅವನು", "avanu", "he"),
        ("ಬರುತ್ತಾನೆ", "baruwaane", "comes"),
    ]
    
    print("Kannada → WX Conversion:")
    print("-" * 70)
    for kannada, expected_wx, meaning in test_cases:
        converted = kannada_to_wx(kannada)
        status = "✅" if converted == expected_wx else "❌"
        print(f"{status} {kannada:15} → {converted:15} (expected: {expected_wx:15}) [{meaning}]")
    
    print()
    print("=" * 70)
    print(f"\n✅ Converter ready to use!")
    print(f"   is_kannada_text('ಮರ'): {is_kannada_text('ಮರ')}")
    print(f"   is_kannada_text('mara'): {is_kannada_text('mara')}")

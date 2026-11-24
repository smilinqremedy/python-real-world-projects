"""
Dictionary of Supported Sign Language Gestures.
Includes linguistic definitions, finger configurations, and cultural / regional notes.
"""
from typing import Dict, Any, List

# Supported Vocabulary
SUPPORTED_SIGNS = [
    "Hello", "Thank You", "Yes", "No", "Please", "I Love You", "Good", "Peace"
]

SIGN_DICTIONARY: Dict[str, Dict[str, Any]] = {
    "Hello": {
        "class_id": 0,
        "sign_name": "Hello",
        "description": "Greeting sign: Flat open hand with all 5 fingers fully extended, palm facing forward.",
        "fingers_extended": ["Thumb", "Index", "Middle", "Ring", "Pinky"],
        "regional_note": "Standard American Sign Language (ASL) greeting; similar in many international sign systems."
    },
    "Thank You": {
        "class_id": 1,
        "sign_name": "Thank You",
        "description": "Expression of gratitude: Flat open hand starting near lips/chin, fingertips extending outward.",
        "fingers_extended": ["Index", "Middle", "Ring", "Pinky"],
        "regional_note": "In ASL, performed with one hand from chin forward. In British Sign Language (BSL), two hands are often used."
    },
    "Yes": {
        "class_id": 2,
        "sign_name": "Yes",
        "description": "Affirmation sign: Closed fist (S-handshape) nodding up and down from the wrist like a head nod.",
        "fingers_extended": [],
        "regional_note": "Standard ASL. Often accompanied by affirmative head nodding in natural discourse."
    },
    "No": {
        "class_id": 3,
        "sign_name": "No",
        "description": "Negation sign: Index and middle fingers extended together and snapping down onto the thumb.",
        "fingers_extended": ["Index", "Middle"],
        "regional_note": "ASL negation handshape; facial grammar (furrowed brow) is an integral syntactic marker."
    },
    "Please": {
        "class_id": 4,
        "sign_name": "Please",
        "description": "Politeness sign: Flat open hand rubbing in a gentle clockwise circle over the center of the chest.",
        "fingers_extended": ["Thumb", "Index", "Middle", "Ring", "Pinky"],
        "regional_note": "Standard ASL and Auslan handshape; variations occur in circular orientation."
    },
    "I Love You": {
        "class_id": 5,
        "sign_name": "I Love You",
        "description": "Affection sign: Thumb, Index, and Pinky fingers extended; Middle and Ring fingers folded down (ILY handshape).",
        "fingers_extended": ["Thumb", "Index", "Pinky"],
        "regional_note": "Internationally recognized ASL symbol combining the manual alphabet letters I, L, and Y."
    },
    "Good": {
        "class_id": 6,
        "sign_name": "Good",
        "description": "Approval / Thumbs-up sign: Closed fist with thumb pointing upright.",
        "fingers_extended": ["Thumb"],
        "regional_note": "Widely understood gesture; in formal ASL discourse, 'Good' extends from chin down into opposite palm."
    },
    "Peace": {
        "class_id": 7,
        "sign_name": "Peace",
        "description": "Victory / Peace sign (V-handshape): Index and Middle fingers extended in a V-shape; Ring, Pinky, and Thumb folded.",
        "fingers_extended": ["Index", "Middle"],
        "regional_note": "Universal manual sign; Palm must face forward in British / Commonwealth culture."
    }
}

ETHICAL_LINGUISTIC_DISCLAIMER = (
    "NOTICE ON SIGN LANGUAGE COMPLEXITY & ETHICAL SCOPE: Natural sign languages (such as ASL, "
    "BSL, or LSF) are full, sophisticated natural human languages with rich spatial grammars, "
    "dynamic facial expressions, torso shifts, and morphological inflections. Recognizing an isolated "
    "vocabulary of manual hand postures is an engineering gesture-classification aid, NOT a full "
    "conversational translation system. We do not claim this replaces certified human sign language interpreters."
)

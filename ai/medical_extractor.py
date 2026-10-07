import re

def extract_medical_info(text: str) -> dict:
    """
    Extract structured medical information from text.
    Do NOT diagnose.
    Handle missing information safely.
    """
    result = {
        'patient_info': {},
        'symptoms': [],
        'medications': [],
        'test_names': [],
        'test_values': [],
        'units': [],
        'dates': [],
        'observations': []
    }
    
    if not text:
        return result
        
    text_lower = text.lower()
    
    symptoms_list = ['fever', 'headache', 'chest pain', 'difficulty breathing', 'severe bleeding', 'nausea']
    medications_list = ['aspirin', 'ibuprofen', 'amoxicillin', 'lisinopril']
    tests_list = ['blood pressure', 'heart rate', 'glucose', 'cholesterol', 'hba1c']
    
    for sym in symptoms_list:
        if sym in text_lower:
            result['symptoms'].append(sym)
            
    for med in medications_list:
        if med in text_lower:
            result['medications'].append(med)
            
    for test in tests_list:
        if test in text_lower:
            result['test_names'].append(test)
            
    dates = re.findall(r'\b\d{4}-\d{2}-\d{2}\b|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{1,2}\b', text_lower)
    result['dates'].extend(dates)
    
    measurements = re.findall(r'(\d+(?:\.\d+)?(?:/\d+)?)\s*(mg/dl|mmhg|bpm|%)', text_lower)
    for val, unit in measurements:
        result['test_values'].append(val)
        result['units'].append(unit)
        
    sentences = re.split(r'[.!?]+', text)
    for s in sentences:
        s_lower = s.lower()
        if 'observed' in s_lower or 'noted' in s_lower or 'appears' in s_lower:
            result['observations'].append(s.strip())
            
    return result

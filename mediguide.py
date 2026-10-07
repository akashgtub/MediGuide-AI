from ai.patient_agent import process_patient_request
import json

def welcome_message():
    return "Welcome to MediGuide AI"

def main():
    print(welcome_message())
    sample_text = """
    Patient notes from 2023-10-12:
    The patient complains of a severe headache and nausea. 
    They have been taking ibuprofen for the pain.
    Blood pressure is 130/85 mmHg and heart rate is 88 bpm.
    It was noted that the patient appears fatigued.
    """
    print("Processing sample document:\n", sample_text)
    result = process_patient_request(sample_text)
    print("\nResult:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

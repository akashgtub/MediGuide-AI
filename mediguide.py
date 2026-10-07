from ai.patient_agent import process_patient_request

def welcome_message():
    return "Welcome to MediGuide AI"

def main():
    print(welcome_message())
    sample_text = "I have a severe headache and fever."
    print("Processing sample document:", sample_text)
    result = process_patient_request(sample_text)
    print("\nResult:")
    import json
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
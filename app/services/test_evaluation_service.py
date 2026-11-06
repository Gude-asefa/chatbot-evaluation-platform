
from app.services.evaluation_service import save_evaluations

# TEST 1: Passed without actual response
test_passed = [
    {
        "question_id": 1,
        "actual_answer": None,
        "status": "Passed",
        "comments": "The chatbot answered correctly.",
    }
]

try:
    result = save_evaluations(test_passed)
    print("TEST 1 PASSED: Saved evaluation:", result)

except Exception as error:
    print("TEST 1 FAILED:", error)


# TEST 2: Failed without actual response
test_failed = [
    {
        "question_id": 1,
        "actual_answer": None,
        "status": "Failed",
        "comments": "The chatbot did not provide a useful answer.",
    }
]

try:
    save_evaluations(test_failed)
    print("TEST 2 FAILED: Invalid evaluation was accepted.")

except ValueError as error:
    print("TEST 2 PASSED: Validation worked.")
    print(error)

except Exception as error:
    print("TEST 2 ERROR:", error)

from mediguide import welcome_message


def test_welcome_message():
    result = welcome_message()

    assert result == "Welcome to MediGuide AI"
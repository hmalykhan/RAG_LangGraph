from backend.router import route

def test_routes():
    assert route("Can I return my damaged laptop after 10 days?") == "knowledge"
    assert route("How long does standard delivery take?") == "knowledge"
    assert route("Is accidental water damage under warranty?") == "knowledge"
    assert route("My order 1042 arrived damaged. Open a complaint.") == "support"
    assert route("What is its status?") == "support"
    assert route("Please mark ticket 1 as resolved") == "support"
    assert route("hello there") is None

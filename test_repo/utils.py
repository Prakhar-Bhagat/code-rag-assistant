import math

def calculate_distance(p1: tuple, p2: tuple) -> float:
    """Calculate Euclidean distance between two points."""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def format_currency(amount: float, currency: str = "USD") -> str:
    if currency == "INR":
        return f"₹{amount:,.2f}"
    return f"${amount:,.2f}"

def get_system_status():
    return {"status": "online", "version": "1.0.0"}
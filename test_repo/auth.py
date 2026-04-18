import time
from functools import wraps
# Testing live reload
def logger(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Executing {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

class Authenticator:
    """Handles user session logic."""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    @logger
    def validate_token(self, token: str) -> bool:
        # Simulate token validation logic
        if token == "valid-token":
            return True
        return False

    def generate_session(self, user_id: int):
        return f"session-{user_id}-{int(time.time())}"
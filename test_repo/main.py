from auth import Authenticator
from utils import get_system_status

def start_app():
    print("Initializing Application...")
    status = get_system_status()
    print(f"System is {status['status']}")
    
    auth = Authenticator(secret_key="top-secret")
    is_valid = auth.validate_token("valid-token")
    
    if is_valid:
        print("Access Granted")
    else:
        print("Access Denied")

if __name__ == "__main__":
    start_app()
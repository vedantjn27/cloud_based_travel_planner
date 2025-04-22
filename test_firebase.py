# test_firebase.py
from firebase_config import create_user, authenticate_user

def test_firebase_auth():
    # Test user creation
    email = "test@example.com"
    password = "test123456"
    user = create_user(email, password)
    
    if user:
        print("User creation successful!")
        
        # Test authentication
        auth_user = authenticate_user(email, password)
        if auth_user:
            print("Authentication successful!")
        else:
            print("Authentication failed!")
    else:
        print("User creation failed!")

if __name__ == "__main__":
    test_firebase_auth()
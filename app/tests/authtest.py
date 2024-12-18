from app.auth.security import decode_token
from app.auth.security import generate_password_hash, verify_password, create_access_token
from datetime import timedelta

"""
to test this, run in terminal: python -m app.tests.authtest
"""
# Generate password hash
hashed_password = generate_password_hash('hahahah')
print(f'Hashed Password: {hashed_password}')

# Verify password
is_verified = verify_password('hahahah', hashed_password)  # Add the hashed password as the second argument
print(f'Is Password Verified: {is_verified}')

# Create access token
expiry = timedelta(minutes=30)
user_data = {  # example data
    "uid": "123e4567-e89b-12d3-a456-426614174000",
    "username": "Ivan Ivanov",
    "email": "Ivan@gmail.com",
    "roles": ["admin"]
}

token = create_access_token(user_data, expiry=expiry, refresh=False)
print(f'This is the token: {token}')

# Decode token
decoded = decode_token(token)
print(f'This is the decoded token: {decoded}')

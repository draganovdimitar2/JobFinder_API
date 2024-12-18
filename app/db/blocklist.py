import time

JTI_EXPIRY = 3600
token_blocklist = {}  # dict to store invalided JTIs


async def add_jti_to_blocklist(jti: str) -> None:
    """
    Add a JWT ID (JTI) to the blocklist with an expiry time.
    """
    expiry_time = time.time() + JTI_EXPIRY
    token_blocklist[jti] = expiry_time  # key is the JTI, value is the calculated expiry_time


async def token_in_blocklist(jti: str) -> bool:
    """
    Check if a JWT ID (JTI) is in the blocklist and has not expired.
    """
    expiry_time = token_blocklist.get(jti)  # if JTI is not found in the dictionary returns None
    if expiry_time is None or expiry_time < time.time():  # checks if the token is not found (in the blocklist) or expired
        token_blocklist.pop(jti, None)  # Cleanup expired tokens
        return False  # If the JTI is not found or is expired (meaning the token is considered valid)
    return True  # This indicates the token is still invalid and should not be used

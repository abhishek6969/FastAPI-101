# ============ PASSWORD HASHING AND VERIFICATION UTILITIES ============
# This module handles secure password operations using the Argon2 hashing algorithm.
# 
# WHY HASH PASSWORDS?
#   - Never store plaintext passwords in databases (huge security risk)
#   - If DB is breached, attackers cannot directly use stolen passwords
#   - Hashing is one-way: cannot reverse hash to get original password
#   - Instead, verify by hashing the login attempt and comparing hashes
# 
# WHY ARGON2?
#   - Currently the most secure hashing algorithm (winner of Password Hashing Competition)
#   - Resistant to GPU/ASIC attacks due to high memory requirements
#   - Much slower than bcrypt/scrypt (forces attackers into long brute-force attempts)
#   - Industry recommended for new projects (OWASP, NIST standards)
# 
# How Password Verification Works:
#   1. User registers → plaintext password → hash_pass() → stored hash in DB
#   2. User logs in → sends plaintext password → verify_pass() → compare with stored hash
#   3. If hashes match → credentials valid
#   4. If hashes don't match → credentials invalid

from passlib.context import CryptContext

# ========== PASSWORD HASHING CONTEXT CONFIGURATION ==========
# CryptContext is configured once and reused for all operations in the application.
# 
# Parameters:
#   - schemes=["argon2"]: Use Argon2 as primary hashing algorithm
#   - deprecated="auto": If password was hashed with deprecated algorithm, auto-upgrade on next login
#                        (allows smooth migration from bcrypt → argon2, etc.)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_pass(password: str) -> str:
    """Hash a plaintext password using Argon2
    
    Args:
        password (str): The raw plaintext password from user registration
        
    Returns:
        str: The hashed password string (safe to store in database)
        
    Example:
        >>> hashed = hash_pass("MySecurePassword123!")
        >>> # Store hashed in database
        
    Note:
        The returned hash includes a random salt and algorithm metadata.
        Hashing the same password twice produces different hashes (due to random salt).
        This is expected and correct behavior.
    """
    return pwd_context.hash(password)

def verify_pass(password: str, hashed: str) -> bool:
    """Verify a plaintext password against a stored hash
    
    Args:
        password (str): The plaintext password from login attempt
        hashed (str): The stored hash from database (from hash_pass())
        
    Returns:
        bool: True if password matches hash, False otherwise
        
    Example:
        >>> hashed = hash_pass("MySecurePassword123!")
        >>> verify_pass("MySecurePassword123!", hashed)
        True
        >>> verify_pass("WrongPassword", hashed)
        False
        
    Note:
        This function is timing-safe (constant-time comparison).
        Prevents timing attacks where attackers infer password length/content from response time.
    """
    return pwd_context.verify(password, hashed)
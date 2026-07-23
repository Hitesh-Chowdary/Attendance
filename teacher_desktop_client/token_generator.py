import time
import hashlib

def generate_dynamic_token(salt: str = "proximity_campus_salt") -> tuple[str, float]:
    """
    Generates a cryptographically strong 6-digit numeric token that shifts every 5 seconds.
    Returns:
        tuple[str, float]: (6-digit token, remaining seconds in the active 5-second window)
    """
    epoch = time.time()
    interval = 10.0 # Shifting interval
    
    # Calculate the block index
    block_index = int(epoch / interval)
    time_remaining = interval - (epoch % interval)
    
    # Hash the block index and salt
    hasher = hashlib.sha256(f"{block_index}:{salt}".encode('utf-8'))
    hash_hex = hasher.hexdigest()
    
    # Extract a 6-digit number from the hash
    token_int = int(hash_hex[:8], 16) % 1000000
    token = f"{token_int:06d}"
    
    return token, time_remaining

if __name__ == "__main__":
    while True:
        token, remaining = generate_dynamic_token()
        print(f"Token: {token} | Time Remaining: {remaining:.1f}s")
        time.sleep(1)


try:
    from backend.app.models import hash_password, verify_password
    print("Import successful")
    
    h = hash_password("secret")
    print(f"Hash: {h}")
    
    v = verify_password("secret", h)
    print(f"Verify: {v}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

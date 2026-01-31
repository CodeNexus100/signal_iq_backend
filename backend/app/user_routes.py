import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from .database import get_database
from .models import UserCreate, UserResponse, UserLogin, hash_password, verify_password
from bson import ObjectId

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/register", response_model=UserResponse)
async def register_user(user_in: UserCreate):
    """Register a new user in MongoDB."""
    try:
        db = get_database()
        
        # Check if user already exists
        existing_user = await db.users.find_one({
            "$or": [
                {"email": user_in.email},
                {"username": user_in.username}
            ]
        })
        
        if existing_user:
            logger.warning(f"Registration failed: User {user_in.username} or email {user_in.email} exists")
            raise HTTPException(
                status_code=400, 
                detail="Username or email already registered"
            )

        # Prepare user data
        user_dict = user_in.model_dump(mode='json')
        password = user_dict.pop("password")
        user_dict["hashed_password"] = hash_password(password)
        
        logger.info(f"Inserting new user: {user_in.username}")
        
        # Insert into MongoDB
        result = await db.users.insert_one(user_dict)
        
        # Format response
        response_data = {
            "id": str(result.inserted_id),
            "username": user_in.username,
            "email": user_in.email,
            "role": user_in.role
        }
        
        logger.info(f"User {user_in.username} registered successfully with ID: {result.inserted_id}")
        return response_data

    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        # Return the actual error message for debugging
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.get("/", response_model=List[UserResponse])
async def list_users():
    """List all registered users."""
    db = get_database()
    users = []
    async for user in db.users.find():
        user["id"] = str(user["_id"])
        users.append(user)
    return users

@router.post("/login")
async def login_user(user_in: UserLogin):
    """Authenticate a user using username, email, and role."""
    db = get_database()
    
    logger.info(f"Login attempt for: {user_in.username}")
    
    # Find user
    user = await db.users.find_one({
        "username": user_in.username,
        "email": user_in.email
    })
    
    if not user:
        logger.warning(f"Login failed: User {user_in.username} not found")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not verify_password(user_in.password, user["hashed_password"]):
        logger.warning(f"Login failed: Incorrect password for {user_in.username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify role
    db_role = str(user.get("role"))
    input_role = str(user_in.role.value if hasattr(user_in.role, 'value') else user_in.role)
    
    if db_role != input_role:
        logger.warning(f"Login failed: Role mismatch for {user_in.username}. DB: {db_role} ({type(db_role)}), Input: {input_role} ({type(input_role)})")
        raise HTTPException(status_code=401, detail=f"Incorrect role selected. Expected {input_role}, found {db_role}")
    
    logger.info(f"User {user_in.username} logged in successfully")
    return {
        "accessToken": "mock_access_token_" + str(user["_id"]),
        "user": {
            "id": str(user["_id"]),
            "name": user["username"],
            "email": user["email"],
            "role": user["role"],
            "avatar": f"https://api.dicebear.com/7.x/avataaars/svg?seed={user['username']}"
        }
    }

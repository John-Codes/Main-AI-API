import random
import string
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
import os
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
from db import DatabaseConnection, init_db, get_db  # Import DatabaseConnection and init_db from db.py
import logging
import datetime as dt  # Import datetime module as dt to avoid confusion
from fastapi import Request

load_dotenv()

# Provide a default SECRET_KEY if not set in environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserInDB(BaseModel):
    email: EmailStr
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class PasswordReset(BaseModel):
    email: EmailStr
    new_password: str

class TokenData(BaseModel):
    email: str | None = None

class Authentication:
    @staticmethod
    def get_user(email: str, conn):
        try:
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            if user:
                return UserInDB(email=user['email'], hashed_password=user['hashed_password'])
            return None
        except Exception as e:
            print(f"Error in get_user: {e}")
            raise

    def authenticate_user(self, email: str, password: str, conn):
        try:
            user = self.get_user(email, conn)
            if not user:
                return False
            if not bcrypt.checkpw(password.encode(), user.hashed_password.encode()):
                return False
            return user
        except Exception as e:
            print(f"Error in authenticate_user: {e}")
            raise

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None):
        try:
            to_encode = data.copy()
            if expires_delta:
                expire = dt.datetime.now(dt.UTC) + expires_delta
            else:
                expire = dt.datetime.now(dt.UTC) + timedelta(minutes=15)
            to_encode.update({"exp": expire})
            encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
            return encoded_jwt
        except Exception as e:
            print(f"Error in create_access_token: {e}")
            raise

    def decode_token(self, token: str):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

    def signup(self, user: UserCreate, conn):
        try:
            if conn.execute("SELECT 1 FROM users WHERE email = ?", (user.email,)).fetchone():
                raise ValueError("Email already registered")
            hashed_password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()
            conn.execute("INSERT INTO users (email, hashed_password) VALUES (?, ?)",
                         (user.email, hashed_password))
            conn.commit()
        except Exception as e:
            conn.rollback()
            logging.error(f"Error during user signup: {e}")
            raise
        return {"message": "User created successfully"}

    def login(self, form_data: OAuth2PasswordRequestForm, conn):
        try:
            user = self.authenticate_user(form_data.username, form_data.password, conn)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = self.create_access_token(
                data={"sub": user.email}, expires_delta=access_token_expires
            )
            return {"access_token": access_token, "token_type": "bearer"}
        except Exception as e:
            logging.error(f"Error during login: {e}")
            raise

    def reset_password(self, reset_data: PasswordReset, conn):
        try:
            if not conn.execute("SELECT 1 FROM users WHERE email = ?", (reset_data.email,)).fetchone():
                raise ValueError("User not found")
            hashed_password = bcrypt.hashpw(reset_data.new_password.encode(), bcrypt.gensalt()).decode()
            conn.execute("UPDATE users SET hashed_password = ? WHERE email = ?",
                         (hashed_password, reset_data.email))
            conn.commit()
        except Exception as e:
            conn.rollback()
            logging.error(f"Error during password reset: {e}")
            raise
        return {"message": "Password reset successfully"}

    @staticmethod
    async def get_current_user(request: Request, conn = Depends(get_db)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        authorization_header = request.headers.get("Authorization")
        if not authorization_header:
            raise credentials_exception
        try:
            scheme, token = authorization_header.split()
            if scheme.lower() != "bearer":
                raise credentials_exception
            print(f"Decoding token: {token}")
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
            token_data = TokenData(email=email)
        except JWTError:
            print(f"JWTError: Could not validate credentials")
            raise credentials_exception
        except Exception as e:
            print(f"Error in get_current_user: {e}")
            raise
        with DatabaseConnection() as conn:
            user = Authentication.get_user(email=token_data.email, conn=conn)
            if user is None:
                raise credentials_exception
            return user

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.ERROR)

    # Initialize database
    with DatabaseConnection() as conn:
        init_db(conn)

    prefix = "test_"  # Optional prefix for test user email
    # Generate a random string of 8 characters
    random_string = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))

    test_user_email = f"{prefix}{random_string}@example.com"
    # Test signup
    test_user = None
    try:
        with DatabaseConnection() as conn:
            auth = Authentication()
            user_data = UserCreate(email=test_user_email, password="password123")
            auth.signup(user_data, conn)
            print("Signup successful.")
            test_user = user_data
    except ValueError as e:
        print(f"Signup failed: {e}")
    except Exception as e:
        print(f"An error occurred during signup: {e}")

    # Test login
    token = None
    if test_user:
        try:
            with DatabaseConnection() as conn:
                auth = Authentication()
                form_data = OAuth2PasswordRequestForm(username=test_user_email, password="password123")
                token_response = auth.login(form_data, conn)
                token = token_response["access_token"]
                print("Login successful. Access token:", token)
        except ValueError as e:
            print(f"Login failed: {e}")
        except Exception as e:
            print(f"An error occurred during login: {e}")

    # Test get_current_user
    if token and test_user:
        try:
            with DatabaseConnection() as conn:
                current_user = Authentication.get_current_user(token=token, conn=conn)
                assert current_user.email == test_user_email, "Current user email does not match"
                print(f"Current user: {current_user.email}")
        except ValueError as e:
            print(f"Get current user failed: {e}")
        except Exception as e:
            print(f"An error occurred during get current user: {e}")
    else:
        print("Token or user not available to test get_current_user.")

    # Test password reset
    if test_user:
        try:
            with DatabaseConnection() as conn:
                auth = Authentication()
                reset_data = PasswordReset(email=test_user_email, new_password="newpassword456")
                auth.reset_password(reset_data, conn)
                print("Password reset successful.")
        except ValueError as e:
            print(f"Password reset failed: {e}")
        except Exception as e:
            print(f"An error occurred during password reset: {e}")

    # Clean up test user
    if test_user:
        try:
            with DatabaseConnection() as conn:
                conn.execute("DELETE FROM users WHERE email = ?", (test_user_email,))
                conn.commit()
                print("Test user deleted.")
        except Exception as e:
            print(f"An error occurred during user deletion: {e}")

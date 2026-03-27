from pymongo.errors import DuplicateKeyError, ConnectionFailure
from bson import ObjectId
from datetime import datetime
from typing import Optional, Dict, Any
import secrets
import string
from passlib.context import CryptContext
from app.core.config import settings
from app.logger.app_logger import app_logger
from app.core.clients import MongoDBClient
from app.core.auth.api_key_models import UserTier, TIER_LIMITS


class DatabaseManager:
    """Database manager for MongoDB operations."""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.users_collection = None
        self.api_keys_collection = None
        self.usage_collection = None
        # Initialize password hashing context with bcrypt
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self._connect()
    
    def _connect(self):
        """Connect to MongoDB database."""
        try:
            if not settings.MONGODB_URI:
                raise ValueError("MONGODB_URI is not configured")
            
            # Use MongoDBClient for connection
            mongo_client = MongoDBClient()
            self.client = mongo_client.client
            
            # Get database name from settings or use default
            db_name = settings.MONGODB_TEST_DB or "myteacher_dev"
            self.db = self.client[db_name]
            self.users_collection = self.db.logins  # Collection name as requested
            self.api_keys_collection = self.db.api_keys
            self.usage_collection = self.db.api_usage
            
            # Create indexes for better performance
            self.users_collection.create_index("email", unique=True)
            self.users_collection.create_index("username", unique=True)
            
            # API keys indexes
            self.api_keys_collection.create_index("key_hash", unique=True)
            self.api_keys_collection.create_index("user_id")
            
            # Usage tracking indexes
            self.usage_collection.create_index([("user_id", 1), ("date", 1)], unique=True)
            self.usage_collection.create_index([("api_key", 1), ("date", 1)])
            
            app_logger.log_info(f"Successfully connected to MongoDB database: {db_name}")
            
        except ConnectionFailure as e:
            app_logger.log_error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            app_logger.log_error(f"Database connection error: {e}")
            raise
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return self.pwd_context.hash(password)
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def _is_legacy_hash(self, password_hash: str) -> bool:
        """Check if password hash is using legacy SHA-256 format."""
        # Legacy hashes are 64 characters (SHA-256 hex digest)
        return len(password_hash) == 64 and all(c in '0123456789abcdef' for c in password_hash.lower())
    
    def _verify_legacy_password(self, plain_password: str, hashed_password: str, salt: str) -> bool:
        """Verify password using legacy SHA-256 method."""
        import hashlib
        legacy_hash = hashlib.sha256((plain_password + salt).encode()).hexdigest()
        return legacy_hash == hashed_password
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user in the database."""
        try:
            # Check if user already exists
            existing_user = self.users_collection.find_one({
                "$or": [
                    {"email": user_data["email"]},
                    {"username": user_data["username"]}
                ]
            })
            
            if existing_user:
                if existing_user["email"] == user_data["email"]:
                    raise ValueError("Email already registered")
                else:
                    raise ValueError("Username already taken")
            
            # Hash password using bcrypt
            hashed_password = self._hash_password(user_data["password"])
            
            # Prepare user document
            user_doc = {
                "email": user_data["email"],
                "username": user_data["username"],
                "full_name": user_data["full_name"],
                "password_hash": hashed_password,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
                # Default tier for newly registered users
                "user_tier": UserTier.FREE.value
            }
            
            # Insert user into database
            result = self.users_collection.insert_one(user_doc)
            
            # Return user data without sensitive information
            user_doc["_id"] = str(result.inserted_id)
            user_doc.pop("password_hash", None)
            user_doc.pop("salt", None)
            
            app_logger.log_info(f"User created successfully: {user_data['email']}")
            return user_doc
            
        except DuplicateKeyError as e:
            app_logger.log_error(f"Duplicate key error while creating user: {e}")
            raise ValueError("User already exists")
        except Exception as e:
            app_logger.log_error(f"Error creating user: {e}")
            raise
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password."""
        try:
            # Find user by email
            user = self.users_collection.find_one({"email": email})
            
            if not user:
                app_logger.log_warning(f"Login attempt with non-existent email: {email}")
                return None
            
            if not user.get("is_active", True):
                app_logger.log_warning(f"Login attempt for inactive user: {email}")
                return None
            
            # Verify password
            stored_hash = user.get("password_hash")
            if not stored_hash:
                app_logger.log_warning(f"No password hash found for user: {email}")
                return None
            
            # Check if this is a legacy SHA-256 hash
            if self._is_legacy_hash(stored_hash):
                # Legacy authentication
                salt = user.get("salt", "")
                if not self._verify_legacy_password(password, stored_hash, salt):
                    app_logger.log_warning(f"Invalid password for user: {email}")
                    return None
                
                # Migrate to bcrypt on successful login
                self._migrate_user_password(user["_id"], password)
                app_logger.log_info(f"Migrated user {email} from SHA-256 to bcrypt")
            else:
                # Modern bcrypt authentication
                if not self._verify_password(password, stored_hash):
                    app_logger.log_warning(f"Invalid password for user: {email}")
                    return None
            
            # Return user data without sensitive information
            user["_id"] = str(user["_id"])
            user.pop("password_hash", None)
            
            app_logger.log_info(f"User authenticated successfully: {email}")
            return user
            
        except Exception as e:
            app_logger.log_error(f"Error authenticating user: {e}")
            raise
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            user = self.users_collection.find_one({"_id": ObjectId(user_id)})
            
            if user:
                user["_id"] = str(user["_id"])
                user.pop("password_hash", None)
                # Ensure tier field presence in returned user object
                if "user_tier" not in user:
                    user["user_tier"] = UserTier.FREE.value
            
            return user
            
        except Exception as e:
            app_logger.log_error(f"Error getting user by ID: {e}")
            raise
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        try:
            user = self.users_collection.find_one({"email": email})
            
            if user:
                user["_id"] = str(user["_id"])
                user.pop("password_hash", None)
                if "user_tier" not in user:
                    user["user_tier"] = UserTier.FREE.value
            
            return user
            
        except Exception as e:
            app_logger.log_error(f"Error getting user by email: {e}")
            raise
    
    def update_user_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """Update user password."""
        try:
            # Get user with password hash
            user = self.users_collection.find_one({"_id": ObjectId(user_id)})
            
            if not user:
                raise ValueError("User not found")
            
            # Verify current password
            stored_hash = user.get("password_hash")
            if not stored_hash:
                raise ValueError("No password hash found")
            
            # Check if this is a legacy SHA-256 hash
            if self._is_legacy_hash(stored_hash):
                salt = user.get("salt", "")
                if not self._verify_legacy_password(current_password, stored_hash, salt):
                    raise ValueError("Current password is incorrect")
            else:
                if not self._verify_password(current_password, stored_hash):
                    raise ValueError("Current password is incorrect")
            
            # Hash new password using bcrypt
            new_hashed_password = self._hash_password(new_password)
            
            # Update password in database
            result = self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "password_hash": new_hashed_password,
                        "updated_at": datetime.utcnow()
                    },
                    "$unset": {"salt": ""}  # Remove salt field for bcrypt
                }
            )
            
            if result.modified_count > 0:
                app_logger.log_info(f"Password updated successfully for user: {user.get('email')}")
                return True
            else:
                app_logger.log_error(f"Failed to update password for user: {user.get('email')}")
                return False
                
        except Exception as e:
            app_logger.log_error(f"Error updating password: {e}")
            raise
    
    def update_user_email(self, user_id: str, current_password: str, new_email: str) -> bool:
        """Update user email."""
        try:
            # Check if new email already exists
            existing_user = self.users_collection.find_one({"email": new_email})
            if existing_user:
                raise ValueError("Email already registered")
            
            # Get user with password hash
            user = self.users_collection.find_one({"_id": ObjectId(user_id)})
            
            if not user:
                raise ValueError("User not found")
            
            # Verify current password
            stored_hash = user.get("password_hash")
            if not stored_hash:
                raise ValueError("No password hash found")
            
            # Check if this is a legacy SHA-256 hash
            if self._is_legacy_hash(stored_hash):
                salt = user.get("salt", "")
                if not self._verify_legacy_password(current_password, stored_hash, salt):
                    raise ValueError("Current password is incorrect")
            else:
                if not self._verify_password(current_password, stored_hash):
                    raise ValueError("Current password is incorrect")
            
            # Update email in database
            result = self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "email": new_email,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                app_logger.log_info(f"Email updated successfully for user: {user.get('email')} -> {new_email}")
                return True
            else:
                app_logger.log_error(f"Failed to update email for user: {user.get('email')}")
                return False
                
        except Exception as e:
            app_logger.log_error(f"Error updating email: {e}")
            raise
    
    def update_user_profile(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user profile information."""
        try:
            # Check if username is being updated and if it's already taken
            if "username" in update_data:
                existing_user = self.users_collection.find_one({
                    "username": update_data["username"],
                    "_id": {"$ne": ObjectId(user_id)}
                })
                if existing_user:
                    raise ValueError("Username already taken")
            
            # Prepare update data
            update_fields = {}
            for field, value in update_data.items():
                if value is not None:
                    update_fields[field] = value
            
            if not update_fields:
                return True  # No fields to update
            
            update_fields["updated_at"] = datetime.utcnow()
            
            # Update user in database
            result = self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_fields}
            )
            
            if result.modified_count > 0:
                app_logger.log_info(f"Profile updated successfully for user: {user_id}")
                return True
            else:
                app_logger.log_warning(f"No changes made to profile for user: {user_id}")
                return True  # Consider this a success as no changes were needed
                
        except Exception as e:
            app_logger.log_error(f"Error updating profile: {e}")
            raise
    
    def _migrate_user_password(self, user_id: ObjectId, plain_password: str) -> bool:
        """Migrate user password from SHA-256 to bcrypt."""
        try:
            # Hash password using bcrypt
            new_hash = self._hash_password(plain_password)
            
            # Update password in database
            result = self.users_collection.update_one(
                {"_id": user_id},
                {
                    "$set": {
                        "password_hash": new_hash,
                        "updated_at": datetime.utcnow()
                    },
                    "$unset": {"salt": ""}  # Remove salt field for bcrypt
                }
            )
            
            if result.modified_count > 0:
                app_logger.log_info(f"Successfully migrated password for user: {user_id}")
                return True
            else:
                app_logger.log_warning(f"Failed to migrate password for user: {user_id}")
                return False
                
        except Exception as e:
            app_logger.log_error(f"Error migrating password: {e}")
            return False
    
    def migrate_all_passwords(self) -> Dict[str, int]:
        """Migrate all legacy SHA-256 passwords to bcrypt."""
        try:
            migrated_count = 0
            failed_count = 0
            
            # Find all users with legacy password hashes
            legacy_users = self.users_collection.find({
                "password_hash": {"$regex": "^[a-f0-9]{64}$"}  # SHA-256 hex pattern
            })
            
            for user in legacy_users:
                app_logger.log_info(f"Found legacy password for user: {user.get('email', 'unknown')}")
                # Note: We can't migrate without the plain password
                # This method is for informational purposes
                failed_count += 1
            
            return {
                "migrated": migrated_count,
                "failed": failed_count,
                "note": "Legacy passwords will be migrated on next login"
            }
            
        except Exception as e:
            app_logger.log_error(f"Error in password migration: {e}")
            return {"migrated": 0, "failed": 0, "error": str(e)}
    
    # API Key Management Methods
    
    def _generate_api_key(self) -> str:
        """Generate a secure API key."""
        # Generate a random 32-character API key with alphanumeric characters
        alphabet = string.ascii_letters + string.digits
        return 'sk-' + ''.join(secrets.choice(alphabet) for _ in range(48))
    
    def _hash_api_key(self, api_key: str) -> str:
        """Hash API key for secure storage."""
        import hashlib
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def create_api_key(self, user_id: str, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new API key for a user."""
        try:
            # Generate API key
            api_key = self._generate_api_key()
            key_hash = self._hash_api_key(api_key)
            
            # Get user to determine tier
            user = self.get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            
            # Determine user tier (default to free for authenticated users)
            user_tier = UserTier.FREE  # Can be upgraded later
            
            # Prepare API key document
            api_key_doc = {
                "key_hash": key_hash,
                "name": name,
                "description": description,
                "user_id": user_id,
                "user_tier": user_tier.value,
                "created_at": datetime.utcnow(),
                "last_used": None,
                "is_active": True,
                "usage_count": 0,
                "monthly_usage": 0
            }
            
            # Insert API key into database
            result = self.api_keys_collection.insert_one(api_key_doc)
            
            # Return API key data
            api_key_doc["_id"] = str(result.inserted_id)
            api_key_doc["api_key"] = api_key  # Include the actual key only in response
            api_key_doc["key_preview"] = api_key[:12] + "..." + api_key[-4:]
            
            app_logger.log_info(f"API key created for user: {user_id}")
            return api_key_doc
            
        except Exception as e:
            app_logger.log_error(f"Error creating API key: {e}")
            raise
    
    def get_api_key_by_hash(self, key_hash: str) -> Optional[Dict[str, Any]]:
        """Get API key by hash."""
        try:
            api_key = self.api_keys_collection.find_one({"key_hash": key_hash})
            if api_key:
                api_key["_id"] = str(api_key["_id"])
            return api_key
        except Exception as e:
            app_logger.log_error(f"Error getting API key: {e}")
            return None
    
    def get_user_api_keys(self, user_id: str) -> list:
        """Get all API keys for a user."""
        try:
            keys = list(self.api_keys_collection.find({"user_id": user_id}))
            for key in keys:
                key["_id"] = str(key["_id"])
                # Add key preview for frontend display
                if "key_hash" in key:
                    # Can't recreate original key from hash, so use a placeholder
                    key["key_preview"] = "sk-****" + "****" + "****"
            return keys
        except Exception as e:
            app_logger.log_error(f"Error getting user API keys: {e}")
            return []
    
    def delete_api_key(self, user_id: str, key_id: str) -> bool:
        """Delete an API key."""
        try:
            result = self.api_keys_collection.delete_one({
                "_id": ObjectId(key_id),
                "user_id": user_id
            })
            
            if result.deleted_count > 0:
                app_logger.log_info(f"API key deleted: {key_id}")
                return True
            return False
            
        except Exception as e:
            app_logger.log_error(f"Error deleting API key: {e}")
            return False
    
    def update_api_key(self, user_id: str, key_id: str, update_data: Dict[str, Any]) -> bool:
        """Update an API key."""
        try:
            update_fields = {}
            for field, value in update_data.items():
                if field in ["name", "description", "is_active"] and value is not None:
                    update_fields[field] = value
            
            if not update_fields:
                return True
            
            update_fields["updated_at"] = datetime.utcnow()
            
            result = self.api_keys_collection.update_one(
                {"_id": ObjectId(key_id), "user_id": user_id},
                {"$set": update_fields}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            app_logger.log_error(f"Error updating API key: {e}")
            return False
    
    def authenticate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Authenticate and get API key info."""
        try:
            key_hash = self._hash_api_key(api_key)
            api_key_doc = self.get_api_key_by_hash(key_hash)
            
            if not api_key_doc or not api_key_doc.get("is_active", False):
                return None
            
            # Update last used timestamp
            self.api_keys_collection.update_one(
                {"_id": ObjectId(api_key_doc["_id"])},
                {"$set": {"last_used": datetime.utcnow()}}
            )
            
            return api_key_doc
            
        except Exception as e:
            app_logger.log_error(f"Error authenticating API key: {e}")
            return None
    
    def update_user_tier(self, user_id: str, new_tier: UserTier) -> bool:
        """Update a user's tier and propagate to their API keys.
        
        Args:
            user_id: The user's ID.
            new_tier: The new tier for the user (UserTier enum).
        """
        try:
            # Update user document
            user_update_result = self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"user_tier": new_tier.value, "updated_at": datetime.utcnow()}}
            )
            if user_update_result.matched_count == 0:
                return False

            # Propagate to all API keys owned by the user
            self.api_keys_collection.update_many(
                {"user_id": user_id},
                {"$set": {"user_tier": new_tier.value, "updated_at": datetime.utcnow()}}
            )

            # Optionally, update usage docs to reflect the new tier going forward.
            # Avoid using Python date objects in filters to prevent BSON encoding issues.
            self.usage_collection.update_many(
                {"user_id": user_id},
                {"$set": {"user_tier": new_tier.value}}
            )

            app_logger.log_info(f"Updated user tier for {user_id} to {new_tier.value}")
            return True
        except Exception as e:
            app_logger.log_error(f"Error updating user tier: {e}")
            return False

    # Usage Tracking Methods
    
    def track_api_usage(self, api_key: str, user_id: str, endpoint: str) -> Dict[str, Any]:
        """Track API usage and check limits."""
        try:
            from datetime import date

            today = date.today()
            current_month = today.replace(day=1)

            # Convert date objects to datetime for MongoDB compatibility
            today_datetime = datetime.combine(today, datetime.min.time())
            current_month_datetime = datetime.combine(current_month, datetime.min.time())

            # Get or create usage document for today
            usage_doc = self.usage_collection.find_one({
                "user_id": user_id,
                "date": today_datetime
            })
            
            # Determine current tier based on context (API key tier if present, otherwise user's tier)
            api_key_doc = self.authenticate_api_key(api_key) if api_key else None
            if api_key_doc:
                current_user_tier = UserTier(api_key_doc.get("user_tier", UserTier.FREE.value))
            else:
                # No API key: use user's stored tier (defaults to FREE if absent)
                user_doc = self.users_collection.find_one({"_id": ObjectId(user_id)})
                user_tier_value = (user_doc or {}).get("user_tier", UserTier.FREE.value)
                current_user_tier = UserTier(user_tier_value)

            if not usage_doc:
                usage_doc = {
                    "user_id": user_id,
                    "api_key": api_key,
                    "user_tier": current_user_tier.value,
                    "date": today_datetime,
                    "month": current_month_datetime,
                    "daily_count": 0,
                    "monthly_count": 0,
                    "endpoints": {}
                }
                self.usage_collection.insert_one(usage_doc)
            else:
                # Keep usage tier in sync with current tier if it changed (for today's doc)
                if usage_doc.get("user_tier") != current_user_tier.value:
                    self.usage_collection.update_one(
                        {"_id": usage_doc.get("_id")},
                        {"$set": {"user_tier": current_user_tier.value}}
                    )
            
            # Get current monthly usage
            monthly_usage = list(self.usage_collection.aggregate([
                {"$match": {"user_id": user_id, "month": current_month_datetime}},
                {"$group": {"_id": None, "total": {"$sum": "$daily_count"}}}
            ]))
            
            current_monthly = monthly_usage[0]["total"] if monthly_usage else 0
            current_daily = usage_doc["daily_count"]
            
            # Check limits
            user_tier = current_user_tier
            limits = TIER_LIMITS[user_tier]
            
            # Check if limits exceeded
            if limits["daily_limit"] != -1 and current_daily >= limits["daily_limit"]:
                return {"allowed": False, "reason": "daily_limit", "tier": user_tier.value}
            
            if limits["monthly_limit"] != -1 and current_monthly >= limits["monthly_limit"]:
                return {"allowed": False, "reason": "monthly_limit", "tier": user_tier.value}
            
            # Increment usage
            self.usage_collection.update_one(
                {"user_id": user_id, "date": today_datetime},
                {
                    "$inc": {
                        "daily_count": 1,
                        f"endpoints.{endpoint}": 1
                    },
                    "$set": {"last_request": datetime.utcnow()}
                }
            )
            
            # Update API key usage count
            if api_key:
                key_hash = self._hash_api_key(api_key)
                self.api_keys_collection.update_one(
                    {"key_hash": key_hash},
                    {"$inc": {"usage_count": 1}}
                )
            
            return {
                "allowed": True,
                "daily_count": current_daily + 1,
                "monthly_count": current_monthly + 1,
                "tier": user_tier.value,
                "limits": limits
            }
            
        except Exception as e:
            app_logger.log_error(f"Error tracking API usage: {e}")
            return {"allowed": False, "reason": "error", "tier": "unauth"}
    
    def get_usage_stats(self, user_id: str) -> Dict[str, Any]:
        """Get usage statistics for a user."""
        try:
            from datetime import date
            
            today = date.today()
            current_month = today.replace(day=1)
            
            # Get today's usage
            daily_usage = self.usage_collection.find_one({
                "user_id": user_id,
                "date": today
            })
            
            # Get monthly usage
            monthly_usage = list(self.usage_collection.aggregate([
                {"$match": {"user_id": user_id, "month": current_month}},
                {"$group": {"_id": None, "total": {"$sum": "$daily_count"}}}
            ]))
            
            user_tier = UserTier.UNAUTH
            if daily_usage:
                user_tier = UserTier(daily_usage.get("user_tier", "unauth"))
            
            limits = TIER_LIMITS[user_tier]
            
            return {
                "daily_count": daily_usage["daily_count"] if daily_usage else 0,
                "monthly_count": monthly_usage[0]["total"] if monthly_usage else 0,
                "user_tier": user_tier.value,
                "daily_limit": limits["daily_limit"],
                "monthly_limit": limits["monthly_limit"],
                "daily_remaining": max(0, limits["daily_limit"] - (daily_usage["daily_count"] if daily_usage else 0)) if limits["daily_limit"] != -1 else -1,
                "monthly_remaining": max(0, limits["monthly_limit"] - (monthly_usage[0]["total"] if monthly_usage else 0)) if limits["monthly_limit"] != -1 else -1
            }
            
        except Exception as e:
            app_logger.log_error(f"Error getting usage stats: {e}")
            return {}
    
    def close_connection(self):
        """Close database connection."""
        if self.client:
            self.client.close()
            app_logger.log_info("Database connection closed")


# Global database manager instance
db_manager = DatabaseManager() 
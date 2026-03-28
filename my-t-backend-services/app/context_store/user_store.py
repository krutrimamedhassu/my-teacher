"""
User/auth/API-key storage backed by MongoDB.
Uses the shared mongo_client instead of opening its own connection.
"""
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from datetime import datetime
from typing import Optional, Dict, Any
import secrets
import string
from passlib.context import CryptContext
from app.context_store.mongo_client import get_db
from app.logger.app_logger import app_logger
from app.core.auth.api_key_models import UserTier, TIER_LIMITS


class DatabaseManager:
    """Database manager for user, API-key and usage MongoDB operations."""

    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        db = get_db()
        self.db = db
        self.users_collection = db.logins
        self.api_keys_collection = db.api_keys
        self.usage_collection = db.api_usage
        self._create_indexes()
        app_logger.log_info("[DatabaseManager] Initialized")

    def _create_indexes(self):
        self.users_collection.create_index("email", unique=True)
        self.users_collection.create_index("username", unique=True)
        self.api_keys_collection.create_index("key_hash", unique=True)
        self.api_keys_collection.create_index("user_id")
        self.usage_collection.create_index([("user_id", 1), ("date", 1)], unique=True)
        self.usage_collection.create_index([("api_key", 1), ("date", 1)])

    # ── Password helpers ──────────────────────────────────────────────────────

    def _hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def _verify_password(self, plain: str, hashed: str) -> bool:
        return self.pwd_context.verify(plain, hashed)

    def _is_legacy_hash(self, h: str) -> bool:
        return len(h) == 64 and all(c in '0123456789abcdef' for c in h.lower())

    def _verify_legacy_password(self, plain: str, hashed: str, salt: str) -> bool:
        import hashlib
        return hashlib.sha256((plain + salt).encode()).hexdigest() == hashed

    def _migrate_user_password(self, user_id, plain: str) -> bool:
        try:
            result = self.users_collection.update_one(
                {"_id": user_id},
                {"$set": {"password_hash": self._hash_password(plain), "updated_at": datetime.utcnow()}, "$unset": {"salt": ""}}
            )
            return result.modified_count > 0
        except Exception as e:
            app_logger.log_error(f"[DatabaseManager] Error migrating password: {e}")
            return False

    # ── User CRUD ─────────────────────────────────────────────────────────────

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            existing = self.users_collection.find_one({"$or": [{"email": user_data["email"]}, {"username": user_data["username"]}]})
            if existing:
                raise ValueError("Email already registered" if existing["email"] == user_data["email"] else "Username already taken")
            doc = {
                "email": user_data["email"],
                "username": user_data["username"],
                "full_name": user_data["full_name"],
                "password_hash": self._hash_password(user_data["password"]),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
                "user_tier": UserTier.FREE.value
            }
            result = self.users_collection.insert_one(doc)
            doc["_id"] = str(result.inserted_id)
            doc.pop("password_hash", None)
            app_logger.log_info(f"[DatabaseManager] User created: {user_data['email']}")
            return doc
        except DuplicateKeyError:
            raise ValueError("User already exists")
        except Exception as e:
            app_logger.log_error(f"[DatabaseManager] Error creating user: {e}")
            raise

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        try:
            user = self.users_collection.find_one({"email": email})
            if not user or not user.get("is_active", True):
                return None
            stored = user.get("password_hash")
            if not stored:
                return None
            if self._is_legacy_hash(stored):
                if not self._verify_legacy_password(password, stored, user.get("salt", "")):
                    return None
                self._migrate_user_password(user["_id"], password)
            else:
                if not self._verify_password(password, stored):
                    return None
            user["_id"] = str(user["_id"])
            user.pop("password_hash", None)
            return user
        except Exception as e:
            app_logger.log_error(f"[DatabaseManager] Error authenticating user: {e}")
            raise

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            user = self.users_collection.find_one({"_id": ObjectId(user_id)})
            if user:
                user["_id"] = str(user["_id"])
                user.pop("password_hash", None)
                user.setdefault("user_tier", UserTier.FREE.value)
            return user
        except Exception as e:
            app_logger.log_error(f"[DatabaseManager] Error getting user by ID: {e}")
            raise

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        try:
            user = self.users_collection.find_one({"email": email})
            if user:
                user["_id"] = str(user["_id"])
                user.pop("password_hash", None)
                user.setdefault("user_tier", UserTier.FREE.value)
            return user
        except Exception as e:
            app_logger.log_error(f"[DatabaseManager] Error getting user by email: {e}")
            raise

    def update_user_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        try:
            user = self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                raise ValueError("User not found")
            stored = user.get("password_hash", "")
            if self._is_legacy_hash(stored):
                if not self._verify_legacy_password(current_password, stored, user.get("salt", "")):
                    raise ValueError("Current password is incorrect")
            else:
                if not self._verify_password(current_password, stored):
                    raise ValueError("Current password is incorrect")
            result = self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"password_hash": self._hash_password(new_password), "updated_at": datetime.utcnow()}, "$unset": {"salt": ""}}
            )
            return result.modified_count > 0
        except Exception as e:
            app_logger.log_error(f"[DatabaseManager] Error updating password: {e}")
            raise

    def update_user_email(self, user_id: str, current_password: str, new_email: str) -> bool:
        try:
            if self.users_collection.find_one({"email": new_email}):
                raise ValueError("Email already registered")
            user = self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                raise ValueError("User not found")
            stored = user.get("password_hash", "")
            if self._is_legacy_hash(stored):
                if not self._verify_legacy_password(current_password, stored, user.get("salt", "")):
                    raise ValueError("Current password is incorrect")
            else:
                if not self._verify_password(current_password, stored):
                    raise ValueError("Current password is incorrect")
            result = self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"email": new_email, "updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            app_logger.log_error(f"[DatabaseManager] Error updating email: {e}")
            raise

    def update_user_profile(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        try:
            if "username" in update_data:
                existing = self.users_collection.find_one({"username": update_data["username"], "_id": {"$ne": ObjectId(user_id)}})
                if existing:
                    raise ValueError("Username already taken")
            fields = {k: v for k, v in update_data.items() if v is not None}
            if not fields:
                return True
            fields["updated_at"] = datetime.utcnow()
            self.users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": fields})
            return True
        except Exception as e:
            app_logger.log_error(f"[DatabaseManager] Error updating profile: {e}")
            raise

    def update_user_tier(self, user_id: str, new_tier: UserTier) -> bool:
        try:
            result = self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"user_tier": new_tier.value, "updated_at": datetime.utcnow()}}
            )
            if result.matched_count == 0:
                return False
            self.api_keys_collection.update_many({"user_id": user_id}, {"$set": {"user_tier": new_tier.value}})
            self.usage_collection.update_many({"user_id": user_id}, {"$set": {"user_tier": new_tier.value}})
            return True
        except Exception as e:
            app_logger.log_error(f"[DatabaseManager] Error updating user tier: {e}")
            return False

    def migrate_all_passwords(self) -> Dict[str, Any]:
        return {"migrated": 0, "failed": 0, "note": "Legacy passwords will be migrated on next login"}

    # ── API Key management ────────────────────────────────────────────────────

    def _generate_api_key(self) -> str:
        return 'sk-' + ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(48))

    def _hash_api_key(self, api_key: str) -> str:
        import hashlib
        return hashlib.sha256(api_key.encode()).hexdigest()

    def create_api_key(self, user_id: str, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            api_key = self._generate_api_key()
            doc = {
                "key_hash": self._hash_api_key(api_key),
                "name": name,
                "description": description,
                "user_id": user_id,
                "user_tier": UserTier.FREE.value,
                "created_at": datetime.utcnow(),
                "last_used": None,
                "is_active": True,
                "usage_count": 0,
                "monthly_usage": 0
            }
            result = self.api_keys_collection.insert_one(doc)
            doc["_id"] = str(result.inserted_id)
            doc["api_key"] = api_key
            doc["key_preview"] = api_key[:12] + "..." + api_key[-4:]
            return doc
        except Exception as e:
            app_logger.log_error(f"[DatabaseManager] Error creating API key: {e}")
            raise

    def get_api_key_by_hash(self, key_hash: str) -> Optional[Dict[str, Any]]:
        try:
            doc = self.api_keys_collection.find_one({"key_hash": key_hash})
            if doc:
                doc["_id"] = str(doc["_id"])
            return doc
        except Exception as e:
            app_logger.log_error(f"[DatabaseManager] Error getting API key: {e}")
            return None

    def get_user_api_keys(self, user_id: str) -> list:
        try:
            keys = list(self.api_keys_collection.find({"user_id": user_id}))
            for k in keys:
                k["_id"] = str(k["_id"])
                k["key_preview"] = "sk-****" + "****" + "****"
            return keys
        except Exception as e:
            app_logger.log_error(f"[DatabaseManager] Error getting user API keys: {e}")
            return []

    def delete_api_key(self, user_id: str, key_id: str) -> bool:
        try:
            result = self.api_keys_collection.delete_one({"_id": ObjectId(key_id), "user_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            app_logger.log_error(f"[DatabaseManager] Error deleting API key: {e}")
            return False

    def update_api_key(self, user_id: str, key_id: str, update_data: Dict[str, Any]) -> bool:
        try:
            fields = {k: v for k, v in update_data.items() if k in ("name", "description", "is_active") and v is not None}
            if not fields:
                return True
            fields["updated_at"] = datetime.utcnow()
            result = self.api_keys_collection.update_one({"_id": ObjectId(key_id), "user_id": user_id}, {"$set": fields})
            return result.modified_count > 0
        except Exception as e:
            app_logger.log_error(f"[DatabaseManager] Error updating API key: {e}")
            return False

    def authenticate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        try:
            doc = self.get_api_key_by_hash(self._hash_api_key(api_key))
            if not doc or not doc.get("is_active"):
                return None
            self.api_keys_collection.update_one({"_id": ObjectId(doc["_id"])}, {"$set": {"last_used": datetime.utcnow()}})
            return doc
        except Exception as e:
            app_logger.log_error(f"[DatabaseManager] Error authenticating API key: {e}")
            return None

    # ── Usage tracking ────────────────────────────────────────────────────────

    def track_api_usage(self, api_key: str, user_id: str, endpoint: str) -> Dict[str, Any]:
        try:
            from datetime import date
            today = date.today()
            today_dt = datetime.combine(today, datetime.min.time())
            month_dt = datetime.combine(today.replace(day=1), datetime.min.time())

            api_key_doc = self.authenticate_api_key(api_key) if api_key else None
            if api_key_doc:
                tier = UserTier(api_key_doc.get("user_tier", UserTier.FREE.value))
            else:
                user_doc = self.users_collection.find_one({"_id": ObjectId(user_id)})
                tier = UserTier((user_doc or {}).get("user_tier", UserTier.FREE.value))

            usage_doc = self.usage_collection.find_one({"user_id": user_id, "date": today_dt})
            if not usage_doc:
                usage_doc = {"user_id": user_id, "api_key": api_key, "user_tier": tier.value, "date": today_dt, "month": month_dt, "daily_count": 0, "monthly_count": 0, "endpoints": {}}
                self.usage_collection.insert_one(usage_doc)
            elif usage_doc.get("user_tier") != tier.value:
                self.usage_collection.update_one({"_id": usage_doc["_id"]}, {"$set": {"user_tier": tier.value}})

            monthly = list(self.usage_collection.aggregate([
                {"$match": {"user_id": user_id, "month": month_dt}},
                {"$group": {"_id": None, "total": {"$sum": "$daily_count"}}}
            ]))
            monthly_count = monthly[0]["total"] if monthly else 0
            daily_count = usage_doc["daily_count"]
            limits = TIER_LIMITS[tier]

            if limits["daily_limit"] != -1 and daily_count >= limits["daily_limit"]:
                return {"allowed": False, "reason": "daily_limit", "tier": tier.value}
            if limits["monthly_limit"] != -1 and monthly_count >= limits["monthly_limit"]:
                return {"allowed": False, "reason": "monthly_limit", "tier": tier.value}

            self.usage_collection.update_one(
                {"user_id": user_id, "date": today_dt},
                {"$inc": {"daily_count": 1, f"endpoints.{endpoint}": 1}, "$set": {"last_request": datetime.utcnow()}}
            )
            if api_key:
                self.api_keys_collection.update_one({"key_hash": self._hash_api_key(api_key)}, {"$inc": {"usage_count": 1}})

            return {"allowed": True, "daily_count": daily_count + 1, "monthly_count": monthly_count + 1, "tier": tier.value, "limits": limits}
        except Exception as e:
            app_logger.log_error(f"[DatabaseManager] Error tracking API usage: {e}")
            return {"allowed": False, "reason": "error", "tier": "unauth"}

    def get_usage_stats(self, user_id: str) -> Dict[str, Any]:
        try:
            from datetime import date
            today = date.today()
            today_dt = datetime.combine(today, datetime.min.time())
            month_dt = datetime.combine(today.replace(day=1), datetime.min.time())
            daily = self.usage_collection.find_one({"user_id": user_id, "date": today_dt})
            monthly = list(self.usage_collection.aggregate([
                {"$match": {"user_id": user_id, "month": month_dt}},
                {"$group": {"_id": None, "total": {"$sum": "$daily_count"}}}
            ]))
            tier = UserTier(daily.get("user_tier", "unauth")) if daily else UserTier.UNAUTH
            limits = TIER_LIMITS[tier]
            daily_count = daily["daily_count"] if daily else 0
            monthly_count = monthly[0]["total"] if monthly else 0
            return {
                "daily_count": daily_count,
                "monthly_count": monthly_count,
                "user_tier": tier.value,
                "daily_limit": limits["daily_limit"],
                "monthly_limit": limits["monthly_limit"],
                "daily_remaining": max(0, limits["daily_limit"] - daily_count) if limits["daily_limit"] != -1 else -1,
                "monthly_remaining": max(0, limits["monthly_limit"] - monthly_count) if limits["monthly_limit"] != -1 else -1
            }
        except Exception as e:
            app_logger.log_error(f"[DatabaseManager] Error getting usage stats: {e}")
            return {}

    def close_connection(self):
        app_logger.log_info("[DatabaseManager] Connection managed by shared mongo_client")


# Global instance
db_manager = DatabaseManager()

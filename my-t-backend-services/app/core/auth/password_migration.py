"""
Password Migration Utility

This module provides utilities for migrating from SHA-256 password hashing to bcrypt.
It includes functions to check migration status and provide migration statistics.
"""

from typing import Dict, List, Any
from app.logger.app_logger import app_logger


def get_migration_status() -> Dict[str, Any]:
    """
    Get the current status of password migration from SHA-256 to bcrypt.

    Returns:
        Dict containing migration statistics and status information.
    """
    app_logger.log_info(f"[PasswordMigration] Getting migration status")
    try:
        from app.core.data.database import db_manager

        # Count total users
        app_logger.log_debug(f"[PasswordMigration] Counting total users")
        total_users = db_manager.users_collection.count_documents({})
        app_logger.log_debug(f"[PasswordMigration] Total users: {total_users}")
        
        # Count users with legacy SHA-256 hashes (64 character hex strings)
        legacy_users = db_manager.users_collection.count_documents({
            "password_hash": {"$regex": "^[a-f0-9]{64}$"}
        })
        
        # Count users with bcrypt hashes (start with $2b$)
        bcrypt_users = db_manager.users_collection.count_documents({
            "password_hash": {"$regex": "^\\$2b\\$"}
        })
        
        # Count users with salt field (legacy indicator)
        users_with_salt = db_manager.users_collection.count_documents({
            "salt": {"$exists": True}
        })
        
        migration_percentage = ((total_users - legacy_users) / total_users * 100) if total_users > 0 else 0
        
        return {
            "total_users": total_users,
            "legacy_sha256_users": legacy_users,
            "bcrypt_users": bcrypt_users,
            "users_with_salt": users_with_salt,
            "migration_percentage": round(migration_percentage, 2),
            "status": "complete" if legacy_users == 0 else "in_progress" if bcrypt_users > 0 else "not_started"
        }
        
    except Exception as e:
        app_logger.log_error(f"[PasswordMigration] Error getting migration status: {e}")
        return {"error": str(e)}


def get_legacy_users() -> List[Dict[str, Any]]:
    """
    Get a list of users who still have legacy SHA-256 password hashes.
    
    Returns:
        List of user documents with legacy hashes (excluding sensitive data).
    """
    try:
        from app.core.data.database import db_manager
        
        legacy_users = db_manager.users_collection.find({
            "password_hash": {"$regex": "^[a-f0-9]{64}$"}
        }, {
            "_id": 1,
            "email": 1,
            "username": 1,
            "full_name": 1,
            "created_at": 1,
            "updated_at": 1
        })
        
        users = []
        for user in legacy_users:
            user["_id"] = str(user["_id"])
            users.append(user)
        
        return users
        
    except Exception as e:
        app_logger.log_error(f"[PasswordMigration] Error getting legacy users: {e}")
        return []


def cleanup_legacy_salt_fields() -> Dict[str, Any]:
    """
    Remove salt fields from users who have already been migrated to bcrypt.
    
    Returns:
        Dict containing cleanup statistics.
    """
    try:
        from app.core.data.database import db_manager
        
        # Find users with bcrypt hashes but still have salt fields
        users_to_cleanup = db_manager.users_collection.find({
            "password_hash": {"$regex": "^\\$2b\\$"},
            "salt": {"$exists": True}
        })
        
        cleaned_count = 0
        for user in users_to_cleanup:
            result = db_manager.users_collection.update_one(
                {"_id": user["_id"]},
                {"$unset": {"salt": ""}}
            )
            if result.modified_count > 0:
                cleaned_count += 1
        
        return {
            "cleaned_users": cleaned_count,
            "message": f"Removed salt field from {cleaned_count} migrated users"
        }
        
    except Exception as e:
        app_logger.log_error(f"[PasswordMigration] Error cleaning up salt fields: {e}")
        return {"error": str(e)}


def validate_password_security() -> Dict[str, Any]:
    """
    Validate that all passwords are using secure hashing.
    
    Returns:
        Dict containing validation results.
    """
    try:
        from app.core.data.database import db_manager
        
        # Check for any users without password hashes
        users_without_hash = db_manager.users_collection.count_documents({
            "$or": [
                {"password_hash": {"$exists": False}},
                {"password_hash": None},
                {"password_hash": ""}
            ]
        })
        
        # Check for any users with weak hashes (not bcrypt)
        weak_hash_users = db_manager.users_collection.count_documents({
            "password_hash": {
                "$not": {"$regex": "^\\$2b\\$"}
            }
        })
        
        # Check for users with both bcrypt and salt (inconsistent state)
        inconsistent_users = db_manager.users_collection.count_documents({
            "password_hash": {"$regex": "^\\$2b\\$"},
            "salt": {"$exists": True}
        })
        
        total_users = db_manager.users_collection.count_documents({})
        secure_users = total_users - users_without_hash - weak_hash_users
        
        return {
            "total_users": total_users,
            "secure_users": secure_users,
            "users_without_hash": users_without_hash,
            "weak_hash_users": weak_hash_users,
            "inconsistent_users": inconsistent_users,
            "security_score": round((secure_users / total_users * 100) if total_users > 0 else 0, 2),
            "is_secure": users_without_hash == 0 and weak_hash_users == 0
        }
        
    except Exception as e:
        app_logger.log_error(f"[PasswordMigration] Error validating password security: {e}")
        return {"error": str(e)} 
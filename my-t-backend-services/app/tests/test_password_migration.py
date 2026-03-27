"""
Test script for password migration from SHA-256 to bcrypt.

This script tests the migration functionality and verifies that:
1. New users get bcrypt hashes
2. Legacy users can still authenticate
3. Legacy users get migrated on login
4. Password updates work correctly
"""

import hashlib
import secrets
import string
from app.core.data.database import db_manager
from app.core.auth.password_migration import get_migration_status, validate_password_security
from app.logger.app_logger import app_logger


def test_password_migration():
    """Test the password migration functionality."""
    print("🧪 Testing Password Migration from SHA-256 to bcrypt")
    print("=" * 60)
    
    # Test 1: Create a new user (should use bcrypt)
    print("\n1. Testing new user creation with bcrypt...")
    try:
        new_user_data = {
            "email": "test_bcrypt@example.com",
            "username": "test_bcrypt",
            "full_name": "Test Bcrypt User",
            "password": "SecurePass123"
        }
        
        user_doc = db_manager.create_user(new_user_data)
        print(f"✅ Created new user: {user_doc['email']}")
        
        # Verify the hash is bcrypt format
        user_in_db = db_manager.users_collection.find_one({"email": user_doc["email"]})
        password_hash = user_in_db["password_hash"]
        
        if password_hash.startswith("$2b$"):
            print("✅ Password hash is in bcrypt format")
        else:
            print("❌ Password hash is not in bcrypt format")
            return False
            
    except Exception as e:
        print(f"❌ Error creating new user: {e}")
        return False
    
    # Test 2: Create a legacy user (simulate SHA-256)
    print("\n2. Testing legacy user creation...")
    try:
        legacy_user_data = {
            "email": "test_legacy@example.com",
            "username": "test_legacy",
            "full_name": "Test Legacy User",
            "password": "LegacyPass123"
        }
        
        # Manually create user with SHA-256 hash
        salt = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
        legacy_hash = hashlib.sha256((legacy_user_data["password"] + salt).encode()).hexdigest()
        
        legacy_user_doc = {
            "email": legacy_user_data["email"],
            "username": legacy_user_data["username"],
            "full_name": legacy_user_data["full_name"],
            "password_hash": legacy_hash,
            "salt": salt,
            "is_active": True
        }
        
        result = db_manager.users_collection.insert_one(legacy_user_doc)
        print(f"✅ Created legacy user: {legacy_user_data['email']}")
        
    except Exception as e:
        print(f"❌ Error creating legacy user: {e}")
        return False
    
    # Test 3: Test legacy user authentication
    print("\n3. Testing legacy user authentication...")
    try:
        auth_result = db_manager.authenticate_user(
            legacy_user_data["email"], 
            legacy_user_data["password"]
        )
        
        if auth_result:
            print("✅ Legacy user authenticated successfully")
            print("✅ User should have been migrated to bcrypt")
        else:
            print("❌ Legacy user authentication failed")
            return False
            
    except Exception as e:
        print(f"❌ Error authenticating legacy user: {e}")
        return False
    
    # Test 4: Verify migration occurred
    print("\n4. Verifying migration occurred...")
    try:
        migrated_user = db_manager.users_collection.find_one({"email": legacy_user_data["email"]})
        password_hash = migrated_user["password_hash"]
        
        if password_hash.startswith("$2b$"):
            print("✅ Legacy user successfully migrated to bcrypt")
        else:
            print("❌ Legacy user was not migrated")
            return False
            
        # Check that salt field was removed
        if "salt" not in migrated_user:
            print("✅ Salt field removed from migrated user")
        else:
            print("❌ Salt field still exists")
            
    except Exception as e:
        print(f"❌ Error verifying migration: {e}")
        return False
    
    # Test 5: Test password update
    print("\n5. Testing password update...")
    try:
        success = db_manager.update_user_password(
            user_doc["_id"],
            "SecurePass123",
            "NewSecurePass456"
        )
        
        if success:
            print("✅ Password updated successfully")
        else:
            print("❌ Password update failed")
            return False
            
    except Exception as e:
        print(f"❌ Error updating password: {e}")
        return False
    
    # Test 6: Check migration status
    print("\n6. Checking migration status...")
    try:
        migration_status = get_migration_status()
        security_validation = validate_password_security()
        
        print(f"📊 Migration Status:")
        print(f"   - Total users: {migration_status['total_users']}")
        print(f"   - Legacy users: {migration_status['legacy_sha256_users']}")
        print(f"   - Bcrypt users: {migration_status['bcrypt_users']}")
        print(f"   - Migration percentage: {migration_status['migration_percentage']}%")
        print(f"   - Status: {migration_status['status']}")
        
        print(f"🔒 Security Validation:")
        print(f"   - Security score: {security_validation['security_score']}%")
        print(f"   - Secure users: {security_validation['secure_users']}")
        print(f"   - Is secure: {security_validation['is_secure']}")
        
    except Exception as e:
        print(f"❌ Error checking migration status: {e}")
        return False
    
    # Cleanup
    print("\n7. Cleaning up test data...")
    try:
        db_manager.users_collection.delete_many({
            "email": {"$in": [user_doc["email"], legacy_user_data["email"]]}
        })
        print("✅ Test data cleaned up")
        
    except Exception as e:
        print(f"❌ Error cleaning up test data: {e}")
        return False
    
    print("\n🎉 All tests passed! Password migration is working correctly.")
    return True


if __name__ == "__main__":
    test_password_migration() 
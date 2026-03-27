#!/usr/bin/env python3
"""
Password Migration Test Runner

This script runs the password migration test to verify that the migration
from SHA-256 to bcrypt is working correctly.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from tests.test_password_migration import test_password_migration

if __name__ == "__main__":
    print("🚀 Starting Password Migration Test")
    print("=" * 50)
    
    success = test_password_migration()
    
    if success:
        print("\n✅ Migration test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Migration test failed!")
        sys.exit(1) 
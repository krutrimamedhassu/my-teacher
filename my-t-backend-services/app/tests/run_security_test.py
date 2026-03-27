#!/usr/bin/env python3
"""
Security Features Test Runner

This script runs the security features test to verify that:
1. Centralized auth dependency works correctly
2. Structured logging with request tracing is functional
3. Input size & file-type guards are working
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from tests.test_security_features import main

if __name__ == "__main__":
    print("🚀 Starting Security Features Test")
    print("=" * 50)
    
    try:
        results = main()
        
        # Check if all tests passed
        all_passed = all(result["success"] for result in results.values())
        
        if all_passed:
            print("\n✅ All security features tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some security features tests failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error running security features tests: {e}")
        sys.exit(1) 
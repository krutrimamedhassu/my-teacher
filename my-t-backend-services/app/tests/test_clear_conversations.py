#!/usr/bin/env python3
"""
Test script to delete all JSON files in the conversations/data directory.

Usage:
    python app/tests/test_clear_conversations.py
"""

import os
import glob
from pathlib import Path
from app.logger.app_logger import app_logger


def delete_conversation_jsons():
    """Delete all JSON files in the conversations/data directory."""
    
    # Get the conversations data directory path
    conversations_dir = Path(__file__).parent.parent / "conversations" / "data"
    
    if not conversations_dir.exists():
        app_logger.log_warning(f"Conversations directory does not exist: {conversations_dir}")
        return
    
    # Find all JSON files in the directory
    json_files = glob.glob(str(conversations_dir / "*.json"))
    
    if not json_files:
        print(f"No JSON files found in {conversations_dir}")
        app_logger.log_info("No JSON files found to delete")
        return
    
    print(f"Found {len(json_files)} JSON files in {conversations_dir}")
    
    # Ask for confirmation
    response = input(f"Are you sure you want to delete {len(json_files)} conversation JSON files? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("Operation cancelled")
        return
    
    # Delete each file
    deleted_count = 0
    failed_count = 0
    
    for json_file in json_files:
        try:
            os.remove(json_file)
            filename = os.path.basename(json_file)
            print(f"Deleted: {filename}")
            app_logger.log_info(f"Deleted conversation file: {filename}")
            deleted_count += 1
        except Exception as e:
            filename = os.path.basename(json_file)
            print(f"Failed to delete {filename}: {e}")
            app_logger.log_error(f"Failed to delete {filename}: {e}")
            failed_count += 1
    
    print(f"\nSummary:")
    print(f"  Successfully deleted: {deleted_count} files")
    print(f"  Failed to delete: {failed_count} files")
    
    if deleted_count > 0:
        app_logger.log_info(f"Conversation cleanup completed - deleted {deleted_count} files")


def list_conversation_files():
    """List all JSON files in the conversations/data directory."""
    
    conversations_dir = Path(__file__).parent.parent / "conversations" / "data"
    
    if not conversations_dir.exists():
        print(f"Conversations directory does not exist: {conversations_dir}")
        return
    
    json_files = glob.glob(str(conversations_dir / "*.json"))
    
    if not json_files:
        print(f"No JSON files found in {conversations_dir}")
        return
    
    print(f"Found {len(json_files)} JSON files:")
    for json_file in sorted(json_files):
        filename = os.path.basename(json_file)
        file_size = os.path.getsize(json_file)
        print(f"  {filename} ({file_size} bytes)")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        print("Listing conversation files:")
        list_conversation_files()
    elif len(sys.argv) > 1 and sys.argv[1] == "--force":
        print("Force deleting all conversation files...")
        conversations_dir = Path(__file__).parent.parent / "conversations" / "data"
        json_files = glob.glob(str(conversations_dir / "*.json"))
        deleted_count = 0
        for json_file in json_files:
            try:
                os.remove(json_file)
                deleted_count += 1
            except Exception as e:
                print(f"Failed to delete {os.path.basename(json_file)}: {e}")
        print(f"Force deleted {deleted_count} files")
    else:
        print("Clearing conversation JSON files...")
        delete_conversation_jsons()
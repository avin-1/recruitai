#!/usr/bin/env python3
"""
Script to clear all entries from the selected_candidates.db SQLite database.
This script will delete all records from the selected_candidates table.
"""

import sqlite3
import os
import sys

def clear_database():
    """Clear all entries from the selected_candidates database"""
    
    # Database path
    db_path = os.path.join('backend', 'selected_candidates.db')
    
    # Check if database file exists
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        print("Please make sure you're running this script from the project root directory.")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # First, let's check how many records exist
        cursor.execute('SELECT COUNT(*) FROM selected_candidates')
        count_before = cursor.fetchone()[0]
        
        print(f"📊 Found {count_before} records in the database")
        
        if count_before == 0:
            print("✅ Database is already empty. No action needed.")
            conn.close()
            return True
        
        # Ask for confirmation
        print(f"\n⚠️  WARNING: This will delete ALL {count_before} records from the database!")
        response = input("Are you sure you want to continue? (yes/no): ").lower().strip()
        
        if response not in ['yes', 'y']:
            print("❌ Operation cancelled by user.")
            conn.close()
            return False
        
        # Delete all records from the table
        cursor.execute('DELETE FROM selected_candidates')
        
        # Reset the auto-increment counter (optional)
        cursor.execute('DELETE FROM sqlite_sequence WHERE name="selected_candidates"')
        
        # Commit the changes
        conn.commit()
        
        # Verify the deletion
        cursor.execute('SELECT COUNT(*) FROM selected_candidates')
        count_after = cursor.fetchone()[0]
        
        if count_after == 0:
            print(f"✅ Successfully deleted {count_before} records from the database!")
            print("🗑️  Database is now empty.")
        else:
            print(f"⚠️  Warning: Expected 0 records, but found {count_after} records after deletion.")
        
        # Close the connection
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ SQLite error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def show_database_info():
    """Show current database information"""
    
    db_path = os.path.join('backend', 'selected_candidates.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("PRAGMA table_info(selected_candidates)")
        columns = cursor.fetchall()
        
        print("📋 Database Structure:")
        print("Table: selected_candidates")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Get record count
        cursor.execute('SELECT COUNT(*) FROM selected_candidates')
        count = cursor.fetchone()[0]
        print(f"\n📊 Total records: {count}")
        
        if count > 0:
            # Show sample records
            cursor.execute('SELECT * FROM selected_candidates ORDER BY selection_date DESC LIMIT 5')
            records = cursor.fetchall()
            
            print(f"\n📝 Sample records (showing up to 5 most recent):")
            for record in records:
                print(f"  ID: {record[0]}, Job: {record[2]}, Candidate: {record[3]}, Date: {record[5]}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ SQLite error: {e}")

if __name__ == "__main__":
    print("🗃️  Selected Candidates Database Manager")
    print("=" * 50)
    
    # Show current database info
    show_database_info()
    print("\n" + "=" * 50)
    
    # Clear the database
    success = clear_database()
    
    if success:
        print("\n✅ Script completed successfully!")
    else:
        print("\n❌ Script failed!")
        sys.exit(1)

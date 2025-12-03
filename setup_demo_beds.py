#!/usr/bin/env python3
"""
Quick setup script to initialize demo beds for testing.
Run this once to create test beds matching your ESP8266 BED_ID values.
"""

import models
import sys

def setup_demo_beds():
    """Create demo beds for testing"""
    print("Creating demo beds for Patient Monitoring System...\n")
    
    beds_to_create = [
        ('Bed 1', 'Room 101'),
        ('Bed 2', 'Room 102'),
        ('Bed 3', 'Room 103'),
        ('Bed 4', 'Room 201'),
        ('Bed 5', 'Room 202'),
    ]
    
    for bed_name, room in beds_to_create:
        try:
            bed_id = models.create_bed(bed_name, room)
            print(f"✓ Created: {bed_name} in {room} (ID: {bed_id})")
        except Exception as e:
            print(f"✗ Failed to create {bed_name}: {e}")
    
    # Verify
    print("\nVerifying beds...")
    all_beds = models.list_beds()
    print(f"Total beds in database: {len(all_beds)}\n")
    
    for bed in all_beds:
        print(f"  ID {bed['id']}: {bed['bed_name']} ({bed['room_no']})")
    
    print("\n✓ Setup complete!")
    print("\nNext steps:")
    print("1. Make sure ESP8266 code has matching BED_ID (1, 2, 3, etc.)")
    print("2. Upload ESP8266 code and check Serial Monitor")
    print("3. Refresh dashboard at http://localhost:5000/")
    print("4. You should see bed data within 5-10 seconds")

if __name__ == '__main__':
    try:
        setup_demo_beds()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

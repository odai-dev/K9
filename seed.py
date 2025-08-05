#!/usr/bin/env python3
"""
Quick seed script runner for the K9 Operations Management System.
"""

import subprocess
import sys
import os

def main():
    """Run the seeding script."""
    print("🌱 Running K9 Operations data seeding...")
    
    try:
        # Change to the project directory
        os.chdir('/home/runner/workspace')
        
        # Run the seed_data.py script
        result = subprocess.run([sys.executable, 'seed_data.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
            print("✅ Seeding completed successfully!")
        else:
            print("❌ Seeding failed:")
            print(result.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error running seeding: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
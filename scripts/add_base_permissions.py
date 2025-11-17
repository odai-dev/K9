#!/usr/bin/env python3
"""
Add base permissions to existing users based on their roles.
This script should be run once after deploying the new permission system.
"""

import sys

def add_base_permissions_to_users():
    """Add base permissions to all existing users who don't have them yet."""
    
    try:
        from app import app, db
        from k9.models.models import User, UserRole
        from k9.utils.default_permissions import create_base_permissions_for_user, get_base_permissions_for_role
    except ImportError as e:
        print(f"Error importing application modules: {e}")
        print("Make sure you're running this script from the application directory.")
        sys.exit(1)
    
    with app.app_context():
        print("Adding Base Permissions to Existing Users")
        print("=" * 60)
        
        try:
            # Get ALL users except GENERAL_ADMIN (they don't need DB permissions)
            # This includes inactive users for complete audit trail
            users = User.query.filter(
                User.role != UserRole.GENERAL_ADMIN
            ).all()
            
            if not users:
                print("No users found that need base permissions.")
                return
            
            print(f"Found {len(users)} users to process...")
            print()
            
            total_created = 0
            for user in users:
                print(f"Processing user: {user.username} ({user.role.value})...")
                
                # Check how many base permissions this role should have
                base_perms = get_base_permissions_for_role(user.role)
                expected_count = len(base_perms)
                
                # Create base permissions
                created = create_base_permissions_for_user(user, db.session)
                
                if created > 0:
                    print(f"  ✓ Created {created}/{expected_count} base permissions")
                    total_created += created
                else:
                    print(f"  ℹ Already has all base permissions ({expected_count})")
            
            db.session.commit()
            
            print()
            print("=" * 60)
            print(f"✓ Successfully added {total_created} base permissions!")
            print(f"  Processed {len(users)} users")
            print()
            print("Base permissions have been successfully added to all existing users.")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ Error adding base permissions: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    print("\nWARNING: This script will add base permissions to ALL existing users.")
    confirm = input("Do you want to continue? (yes/no): ").strip().lower()
    
    if confirm == "yes":
        add_base_permissions_to_users()
    else:
        print("Aborted.")
        sys.exit(0)

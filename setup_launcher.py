#!/usr/bin/env python3
"""
K9 Operations Management System - Setup Launcher

This is the main entry point for setting up the application locally.
It provides a menu-driven interface for different setup options.
"""

import os
import sys
import subprocess
from pathlib import Path

class SetupLauncher:
    def __init__(self):
        self.project_root = Path(__file__).parent
        
    def print_banner(self):
        """Print setup banner"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║                K9 Operations Management System               ║
║                      Setup Assistant                         ║
║                                                              ║
║  A comprehensive military/police canine operations          ║
║  management system with Arabic RTL support                  ║
╚══════════════════════════════════════════════════════════════╝
""")
        
    def show_menu(self):
        """Show main menu options"""
        print("Available Setup Options:")
        print()
        print("1. 🚀 Full Automated Setup (Recommended)")
        print("   Complete setup including environment, database, and admin user")
        print()
        print("2. 🔧 Fix Common Issues")
        print("   Automatically fix common setup problems")
        print()
        print("3. ✅ Verify Installation")
        print("   Check if everything is working correctly")
        print()
        print("4. 📖 View Setup Guide")
        print("   Open comprehensive setup documentation")
        print()
        print("5. 🆘 Troubleshooting Guide")
        print("   Get help with common problems")
        print()
        print("6. 🏃 Quick Start (if already set up)")
        print("   Start the application immediately")
        print()
        print("0. Exit")
        print()
        
    def run_script(self, script_name):
        """Run a Python script"""
        script_path = self.project_root / script_name
        if not script_path.exists():
            print(f"❌ Script not found: {script_name}")
            return False
            
        try:
            result = subprocess.run([sys.executable, str(script_path)], 
                                  cwd=str(self.project_root))
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Error running {script_name}: {e}")
            return False
            
    def open_guide(self, guide_name):
        """Open a guide file"""
        guide_path = self.project_root / guide_name
        if not guide_path.exists():
            print(f"❌ Guide not found: {guide_name}")
            return False
            
        # Try to open with default system editor
        try:
            import webbrowser
            if guide_name.endswith('.md'):
                # For markdown files, try to open in browser or editor
                webbrowser.open(f"file://{guide_path.absolute()}")
            else:
                # For other files, print location
                print(f"📖 Guide location: {guide_path}")
            return True
        except Exception:
            print(f"📖 Guide location: {guide_path}")
            print("💡 Open this file in your text editor or browser")
            return True
            
    def quick_start(self):
        """Quick start the application"""
        print("🏃 Starting K9 Operations Management System...")
        print()
        
        # Check if virtual environment exists
        venv_path = self.project_root / 'venv'
        if not venv_path.exists():
            print("❌ Virtual environment not found!")
            print("💡 Run 'Full Automated Setup' first")
            return False
            
        # Check if .env exists
        env_path = self.project_root / '.env'
        if not env_path.exists():
            print("❌ Environment file not found!")
            print("💡 Run 'Full Automated Setup' or 'Fix Common Issues' first")
            return False
            
        # Provide startup instructions
        if os.name == 'nt':  # Windows
            activate_cmd = f"{venv_path}\\Scripts\\activate"
            python_cmd = f"{venv_path}\\Scripts\\python.exe"
        else:
            activate_cmd = f"source {venv_path}/bin/activate"
            python_cmd = f"{venv_path}/bin/python"
            
        print("🔧 To start the application:")
        print(f"   1. Activate environment: {activate_cmd}")
        print(f"   2. Start Flask: flask run --host=0.0.0.0 --port=5000")
        print(f"   3. Open browser: http://localhost:5000")
        print(f"   4. Login: admin / password123")
        print()
        print("📝 Note: Remember to change the admin password after first login!")
        return True
        
    def run(self):
        """Run the setup launcher"""
        self.print_banner()
        
        while True:
            self.show_menu()
            try:
                choice = input("Select an option (0-6): ").strip()
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                sys.exit(0)
                
            print()
            
            if choice == '0':
                print("👋 Goodbye!")
                break
            elif choice == '1':
                print("🚀 Running Full Automated Setup...")
                success = self.run_script('setup_local.py')
                if success:
                    print("\n✅ Setup completed! You can now run option 6 to start the app.")
                else:
                    print("\n❌ Setup encountered issues. Try option 2 to fix problems.")
                    
            elif choice == '2':
                print("🔧 Running Issue Fixer...")
                self.run_script('fix_common_issues.py')
                
            elif choice == '3':
                print("✅ Running Installation Verification...")
                self.run_script('verify_setup.py')
                
            elif choice == '4':
                print("📖 Opening Setup Guide...")
                self.open_guide('LOCAL_SETUP_GUIDE.md')
                
            elif choice == '5':
                print("🆘 Opening Troubleshooting Guide...")
                self.open_guide('TROUBLESHOOTING.md')
                
            elif choice == '6':
                self.quick_start()
                
            else:
                print("❌ Invalid choice. Please select 0-6.")
                
            input("\nPress Enter to continue...")
            print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    launcher = SetupLauncher()
    launcher.run()
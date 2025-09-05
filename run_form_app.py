#!/usr/bin/env python3
"""
Script to run the Patient Intake Form Streamlit app on port 8502
Usage: python run_form_app.py
"""

import subprocess
import sys
import os

def main():
    # Change to the directory containing the form app
    script_dir = os.path.dirname(os.path.abspath(__file__))
    form_file = os.path.join(script_dir, "patient_intake_form.py")
    
    if not os.path.exists(form_file):
        print(f"❌ Error: {form_file} not found!")
        sys.exit(1)
    
    print("🏥 Starting Patient Intake Form Application...")
    print("📋 The form will be available at: http://localhost:8501")
    print("🔗 Patients can access their personalized forms via the link sent in their email")
    print("\n" + "="*60)
    
    try:
        # Run streamlit on port 8501
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            form_file,
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Patient Intake Form app stopped.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Streamlit app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script to add more doctors to the medical scheduling system
"""

import sqlite3
from datetime import datetime

def add_more_doctors():
    """Add additional doctors to the system"""
    
    print("🏥 Adding More Doctors to MediCare System")
    print("=" * 50)
    
    conn = sqlite3.connect('data/medical_scheduler.db')
    cursor = conn.cursor()
    
    # First, check current doctors
    cursor.execute("SELECT doctor_id, doctor_name, specialty FROM doctors")
    current_doctors = cursor.fetchall()
    
    print("📋 Current Doctors:")
    for doctor in current_doctors:
        print(f"   - Dr. {doctor[1]} ({doctor[2]})")
    
    print(f"\nTotal current doctors: {len(current_doctors)}")
    
    # Additional doctors to add (simplified for existing table structure)
    new_doctors = [
        # Allergy & Immunology (additional)
        ("Dr. Sarah Thompson", "Allergy & Immunology"),
        ("Dr. James Wilson", "Allergy & Immunology"),
        
        # Internal Medicine
        ("Dr. Maria Garcia", "Internal Medicine"),
        ("Dr. Robert Chen", "Internal Medicine"),
        ("Dr. Lisa Anderson", "Internal Medicine"),
        
        # Dermatology
        ("Dr. Jennifer Brown", "Dermatology"),
        ("Dr. David Lee", "Dermatology"),
        
        # Pulmonology
        ("Dr. Amanda White", "Pulmonology"),
        ("Dr. Kevin Johnson", "Pulmonology"),
        
        # Rheumatology
        ("Dr. Rachel Davis", "Rheumatology"),
        ("Dr. Thomas Miller", "Rheumatology"),
        
        # ENT (Ear, Nose, Throat)
        ("Dr. Michelle Taylor", "ENT (Otolaryngology)"),
        ("Dr. Christopher Moore", "ENT (Otolaryngology)"),
        
        # Family Medicine
        ("Dr. Patricia Clark", "Family Medicine"),
        ("Dr. Daniel Martinez", "Family Medicine"),
        ("Dr. Sandra Lewis", "Family Medicine"),
        
        # Pediatric Allergy
        ("Dr. Emily Rodriguez", "Pediatric Allergy"),
        ("Dr. Mark Hall", "Pediatric Allergy"),
        
        # Cardiology
        ("Dr. Steven Young", "Cardiology"),
        ("Dr. Nancy King", "Cardiology"),
        
        # Gastroenterology
        ("Dr. Andrew Scott", "Gastroenterology"),
        ("Dr. Jennifer Green", "Gastroenterology"),
        
        # Endocrinology
        ("Dr. William Adams", "Endocrinology"),
        ("Dr. Barbara Baker", "Endocrinology"),
    ]
    
    print(f"\n➕ Adding {len(new_doctors)} new doctors...")
    
    for doctor_name, specialty in new_doctors:
        try:
            cursor.execute("""
                INSERT INTO doctors (doctor_name, specialty)
                VALUES (?, ?)
            """, (doctor_name, specialty))
            print(f"   ✅ Added: {doctor_name} ({specialty})")
        except Exception as e:
            print(f"   ❌ Error adding {doctor_name}: {e}")
    
    conn.commit()
    
    # Show final count
    cursor.execute("SELECT COUNT(*) FROM doctors")
    total_doctors = cursor.fetchone()[0]
    
    print(f"\n🎉 Successfully updated doctor database!")
    print(f"📊 Total doctors now: {total_doctors}")
    
    # Show doctors by specialty
    cursor.execute("""
        SELECT specialty, COUNT(*) as count 
        FROM doctors 
        GROUP BY specialty 
        ORDER BY count DESC
    """)
    specialties = cursor.fetchall()
    
    print(f"\n📋 Doctors by Specialty:")
    for specialty, count in specialties:
        print(f"   - {specialty}: {count} doctors")
    
    conn.close()

if __name__ == "__main__":
    add_more_doctors()

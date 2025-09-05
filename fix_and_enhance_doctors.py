#!/usr/bin/env python3
"""
Script to fix doctor names and generate appointment slots for all doctors
"""

import sqlite3
from datetime import datetime, timedelta
import random

def fix_doctor_names_and_generate_slots():
    """Fix doctor name formatting and generate appointment slots"""
    
    print("🔧 Fixing Doctor Names & Generating Appointment Slots")
    print("=" * 60)
    
    conn = sqlite3.connect('data/medical_scheduler.db')
    cursor = conn.cursor()
    
    # 1. Fix double "Dr." prefix issue
    print("📝 Step 1: Fixing doctor name formatting...")
    cursor.execute("SELECT doctor_id, doctor_name FROM doctors WHERE doctor_name LIKE 'Dr. Dr.%'")
    duplicate_dr_names = cursor.fetchall()
    
    for doctor_id, name in duplicate_dr_names:
        fixed_name = name.replace('Dr. Dr.', 'Dr.')
        cursor.execute('UPDATE doctors SET doctor_name = ? WHERE doctor_id = ?', (fixed_name, doctor_id))
        print(f"   ✅ Fixed: {name} → {fixed_name}")
    
    conn.commit()
    print(f"   📊 Fixed {len(duplicate_dr_names)} doctor names\n")
    
    # 2. Check which doctors need appointment slots
    print("📅 Step 2: Checking appointment slot availability...")
    cursor.execute("""
        SELECT d.doctor_id, d.doctor_name, d.specialty, 
               COUNT(a.slot_id) as slot_count
        FROM doctors d
        LEFT JOIN available_slots a ON d.doctor_id = a.doctor_id
        GROUP BY d.doctor_id, d.doctor_name, d.specialty
        ORDER BY slot_count, d.doctor_name
    """)
    
    doctor_slots = cursor.fetchall()
    doctors_needing_slots = []
    
    print("   Doctor Slot Status:")
    for doctor_id, name, specialty, slot_count in doctor_slots:
        status = "✅ Has slots" if slot_count > 0 else "❌ Needs slots"
        print(f"   - {name} ({specialty}): {slot_count} slots {status}")
        
        if slot_count == 0:
            doctors_needing_slots.append((doctor_id, name, specialty))
    
    print(f"\n   📊 {len(doctors_needing_slots)} doctors need appointment slots\n")
    
    # 3. Generate appointment slots for doctors without them
    if doctors_needing_slots:
        print("🗓️ Step 3: Generating appointment slots...")
        
        # Generate slots for the next 30 days
        start_date = datetime.now().date()
        
        for doctor_id, name, specialty in doctors_needing_slots:
            print(f"   📋 Generating slots for {name}...")
            slots_created = 0
            
            for day_offset in range(30):  # Next 30 days
                current_date = start_date + timedelta(days=day_offset)
                
                # Skip weekends for most doctors
                if current_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                    continue
                
                # Generate 8-10 time slots per day (8 AM to 6 PM)
                base_times = [
                    "08:00", "09:00", "10:00", "11:00", 
                    "13:00", "14:00", "15:00", "16:00", "17:00"
                ]
                
                # Add some variation - not all doctors work all slots
                available_times = random.sample(base_times, random.randint(6, 8))
                
                for time_slot in available_times:
                    try:
                        cursor.execute("""
                            INSERT INTO available_slots (doctor_id, date, time, is_available)
                            VALUES (?, ?, ?, 1)
                        """, (doctor_id, current_date.strftime('%Y-%m-%d'), time_slot))
                        slots_created += 1
                    except sqlite3.IntegrityError:
                        # Slot already exists, skip
                        pass
            
            conn.commit()
            print(f"      ✅ Created {slots_created} appointment slots")
        
        print(f"\n   🎉 Generated appointment slots for {len(doctors_needing_slots)} doctors\n")
    
    # 4. Final verification
    print("📊 Step 4: Final verification...")
    cursor.execute("""
        SELECT d.specialty, COUNT(DISTINCT d.doctor_id) as doctor_count,
               COUNT(a.slot_id) as total_slots
        FROM doctors d
        LEFT JOIN available_slots a ON d.doctor_id = a.doctor_id
        GROUP BY d.specialty
        ORDER BY doctor_count DESC
    """)
    
    specialty_summary = cursor.fetchall()
    
    print("   📋 Final Summary by Specialty:")
    total_doctors = 0
    total_slots = 0
    
    for specialty, doctor_count, slot_count in specialty_summary:
        print(f"   - {specialty}: {doctor_count} doctors, {slot_count} total slots")
        total_doctors += doctor_count
        total_slots += slot_count
    
    print(f"\n   🏥 TOTAL: {total_doctors} doctors with {total_slots} appointment slots")
    
    # 5. Test enhanced chat assistant
    print("\n🤖 Step 5: Testing Enhanced Chat Assistant...")
    try:
        # Import and test the enhanced agent
        import sys
        import os
        sys.path.append(os.getcwd())
        
        from medical_agent_simple import EnhancedMedicalAgent
        agent = EnhancedMedicalAgent()
        
        # Test showing all doctors
        result = agent._show_all_doctors()
        print("   ✅ Enhanced chat assistant working")
        print(f"   📋 Chat shows {len(agent.get_available_doctors())} doctors")
        
        # Test specialty request handling
        specialty_result = agent.handle_specialty_request("cardiology")
        print("   ✅ Specialty request handling working")
        
    except Exception as e:
        print(f"   ⚠️ Chat assistant test failed: {e}")
    
    conn.close()
    print("\n🎉 Doctor enhancement complete!")

if __name__ == "__main__":
    fix_doctor_names_and_generate_slots()

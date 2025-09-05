import streamlit as st
import sqlite3
from datetime import datetime
import uuid
import pandas as pd

def init_database():
    """Initialize database for form submissions"""
    conn = sqlite3.connect('data/medical_scheduler.db')
    cursor = conn.cursor()
    
    # Create patient_intake_forms table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patient_intake_forms (
            form_id TEXT PRIMARY KEY,
            patient_id TEXT,
            submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            first_name TEXT,
            last_name TEXT,
            date_of_birth DATE,
            gender TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            emergency_name TEXT,
            emergency_phone TEXT,
            emergency_relationship TEXT,
            insurance_company TEXT,
            member_id TEXT,
            group_number TEXT,
            chief_complaint TEXT,
            symptom_duration TEXT,
            pain_level TEXT,
            current_medications TEXT,
            allergies TEXT,
            medical_conditions TEXT,
            other_conditions TEXT,
            family_history TEXT,
            smoking_status TEXT,
            alcohol_use TEXT,
            exercise_habits TEXT,
            consent1 BOOLEAN,
            consent2 BOOLEAN,
            consent3 BOOLEAN,
            consent4 BOOLEAN,
            digital_signature TEXT,
            signature_date DATE,
            appointment_date DATE,
            appointment_time TIME,
            doctor_name TEXT,
            specialty TEXT,
            duration INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()

def get_patient_appointment_info(patient_id):
    """Get patient and appointment information"""
    conn = sqlite3.connect('data/medical_scheduler.db')
    
    query = """
        SELECT p.*, a.appointment_date, a.appointment_time, a.duration,
               d.doctor_name, d.specialty
        FROM patients p
        LEFT JOIN appointments a ON p.patient_id = a.patient_id
        LEFT JOIN doctors d ON a.doctor_id = d.doctor_id
        WHERE p.patient_id = ?
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
        LIMIT 1
    """
    
    result = pd.read_sql_query(query, conn, params=[patient_id])
    conn.close()
    
    return result.iloc[0] if not result.empty else None

def save_intake_form(form_data):
    """Save intake form data to database"""
    conn = sqlite3.connect('data/medical_scheduler.db')
    cursor = conn.cursor()
    
    form_id = str(uuid.uuid4())
    
    cursor.execute('''
        INSERT INTO patient_intake_forms (
            form_id, patient_id, first_name, last_name, date_of_birth, gender,
            phone, email, address, emergency_name, emergency_phone, emergency_relationship,
            insurance_company, member_id, group_number, chief_complaint, symptom_duration,
            pain_level, current_medications, allergies, medical_conditions, other_conditions,
            family_history, smoking_status, alcohol_use, exercise_habits,
            consent1, consent2, consent3, consent4, digital_signature, signature_date,
            appointment_date, appointment_time, doctor_name, specialty, duration
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        form_id,
        form_data.get('patient_id'),
        form_data.get('first_name'),
        form_data.get('last_name'),
        form_data.get('date_of_birth'),
        form_data.get('gender'),
        form_data.get('phone'),
        form_data.get('email'),
        form_data.get('address'),
        form_data.get('emergency_name'),
        form_data.get('emergency_phone'),
        form_data.get('emergency_relationship'),
        form_data.get('insurance_company'),
        form_data.get('member_id'),
        form_data.get('group_number'),
        form_data.get('chief_complaint'),
        form_data.get('symptom_duration'),
        form_data.get('pain_level'),
        form_data.get('current_medications'),
        form_data.get('allergies'),
        form_data.get('medical_conditions'),
        form_data.get('other_conditions'),
        form_data.get('family_history'),
        form_data.get('smoking_status'),
        form_data.get('alcohol_use'),
        form_data.get('exercise_habits'),
        form_data.get('consent1', False),
        form_data.get('consent2', False),
        form_data.get('consent3', False),
        form_data.get('consent4', False),
        form_data.get('digital_signature'),
        form_data.get('signature_date'),
        form_data.get('appointment_date'),
        form_data.get('appointment_time'),
        form_data.get('doctor_name'),
        form_data.get('specialty'),
        form_data.get('duration')
    ))
    
    conn.commit()
    conn.close()
    
    return form_id

def main():
    st.set_page_config(
        page_title="Patient Intake Form - MediCare",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        .main-header {
            text-align: center;
            color: #2c5aa0;
            padding: 20px 0;
            border-bottom: 3px solid #2c5aa0;
            margin-bottom: 30px;
        }
        .section-header {
            color: #2c5aa0;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 10px;
            margin: 30px 0 20px 0;
        }
        .important-note {
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }
        .emergency-note {
            background-color: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }
        .appointment-info {
            background-color: #e8f4fd;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize database
    init_database()
    
    # Header
    st.markdown('<div class="main-header"><h1>🏥 Patient Intake Form</h1><h3>MediCare Allergy & Wellness Center</h3></div>', unsafe_allow_html=True)
    
    # Get patient ID from URL parameters
    query_params = st.experimental_get_query_params()
    patient_id = query_params.get('patient_id', [None])[0]
    
    if not patient_id:
        st.error("❌ Patient ID not found in URL. Please use the link provided in your appointment confirmation.")
        st.stop()
    
    # Get patient and appointment information
    patient_info = get_patient_appointment_info(patient_id)
    
    if patient_info is None:
        st.error("❌ Patient information not found. Please contact our office at (555) 123-4567.")
        st.stop()
    
    # Display appointment information
    st.markdown('<div class="appointment-info">', unsafe_allow_html=True)
    st.markdown("### 📅 Appointment Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Patient:** {patient_info['first_name']} {patient_info['last_name']}")
        st.write(f"**Appointment Date:** {patient_info['appointment_date']}")
        st.write(f"**Appointment Time:** {patient_info['appointment_time']}")
    
    with col2:
        st.write(f"**Doctor:** Dr. {patient_info['doctor_name']}")
        st.write(f"**Specialty:** {patient_info['specialty']}")
        st.write(f"**Duration:** {patient_info['duration']} minutes")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Form
    with st.form("patient_intake_form"):
        # Personal Information
        st.markdown('<h2 class="section-header">📋 Personal Information</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name *", value=patient_info['first_name'], key="first_name")
            date_of_birth = st.date_input("Date of Birth *", value=datetime.strptime(patient_info['date_of_birth'], '%Y-%m-%d').date() if patient_info['date_of_birth'] else None)
            phone = st.text_input("Phone Number *", value=patient_info['phone'], key="phone")
        
        with col2:
            last_name = st.text_input("Last Name *", value=patient_info['last_name'], key="last_name")
            gender = st.selectbox("Gender *", ["", "Male", "Female", "Other", "Prefer not to say"])
            email = st.text_input("Email Address *", value=patient_info['email'], key="email")
        
        address = st.text_area("Home Address", value=patient_info.get('address', ''), placeholder="Street Address, City, State, ZIP Code")
        
        # Emergency Contact
        st.markdown('<h2 class="section-header">🚨 Emergency Contact Information</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            emergency_name = st.text_input("Emergency Contact Name *")
            emergency_phone = st.text_input("Emergency Contact Phone *")
        
        with col2:
            emergency_relationship = st.selectbox("Relationship *", ["", "Spouse", "Parent", "Child", "Sibling", "Friend", "Other"])
        
        # Insurance Information
        st.markdown('<h2 class="section-header">🏥 Insurance Information</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            insurance_company = st.text_input("Insurance Company *")
            member_id = st.text_input("Member ID *")
        
        with col2:
            group_number = st.text_input("Group Number")
        
        # Chief Complaint
        st.markdown('<h2 class="section-header">🩺 Chief Complaint & Symptoms</h2>', unsafe_allow_html=True)
        
        chief_complaint = st.text_area("What is the main reason for your visit today? *", placeholder="Please describe your symptoms, concerns, or reason for visit")
        
        col1, col2 = st.columns(2)
        with col1:
            symptom_duration = st.selectbox("How long have you had these symptoms?", [
                "", "Less than a week", "1-2 weeks", "About a month", "2-6 months", "More than 6 months", "Several years"
            ])
        
        with col2:
            pain_level = st.selectbox("Current pain/discomfort level (0-10 scale)", [
                "", "0 - No pain", "1 - Minimal", "2 - Mild", "3 - Mild", "4 - Moderate", "5 - Moderate",
                "6 - Moderately severe", "7 - Severe", "8 - Very severe", "9 - Nearly unbearable", "10 - Unbearable"
            ])
        
        # Medical History
        st.markdown('<h2 class="section-header">📖 Medical History</h2>', unsafe_allow_html=True)
        
        current_medications = st.text_area("Current Medications *", placeholder="List all medications, vitamins, and supplements you are currently taking (include dosages if known)")
        allergies = st.text_area("Known Allergies *", placeholder="List any known allergies to medications, foods, environmental factors, etc. If none, write 'None'")
        
        st.write("**Previous Medical Conditions (check all that apply):**")
        col1, col2, col3 = st.columns(3)
        
        conditions = {}
        with col1:
            conditions['diabetes'] = st.checkbox("Diabetes")
            conditions['hypertension'] = st.checkbox("High Blood Pressure")
            conditions['heart_disease'] = st.checkbox("Heart Disease")
        
        with col2:
            conditions['asthma'] = st.checkbox("Asthma")
            conditions['cancer'] = st.checkbox("Cancer")
            conditions['kidney_disease'] = st.checkbox("Kidney Disease")
        
        with col3:
            conditions['liver_disease'] = st.checkbox("Liver Disease")
            conditions['depression'] = st.checkbox("Depression/Anxiety")
            conditions['other'] = st.checkbox("Other")
        
        selected_conditions = [k for k, v in conditions.items() if v]
        
        other_conditions = st.text_area("Other Medical Conditions or Important Medical History", placeholder="Please describe any other medical conditions, surgeries, or important medical history")
        
        # Family History
        st.markdown('<h2 class="section-header">👨‍👩‍👧‍👦 Family Medical History</h2>', unsafe_allow_html=True)
        family_history = st.text_area("Significant Family Medical History", placeholder="Please list any significant medical conditions in your immediate family (parents, siblings, children)")
        
        # Social History
        st.markdown('<h2 class="section-header">🏠 Social History</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            smoking_status = st.selectbox("Smoking Status", ["", "Never smoked", "Former smoker", "Current smoker"])
            alcohol_use = st.selectbox("Alcohol Use", ["", "None", "Occasional (1-2 drinks/week)", "Moderate (3-7 drinks/week)", "Heavy (8+ drinks/week)"])
        
        with col2:
            exercise_habits = st.selectbox("Exercise Habits", ["", "Sedentary (little to no exercise)", "Light (1-2 times/week)", "Moderate (3-4 times/week)", "Very Active (5+ times/week)"])
        
        # Important Notes
        st.markdown('''
        <div class="important-note">
            <h4>⚠️ Important Pre-Visit Instructions</h4>
            <p><strong>For Allergy Testing:</strong> If allergy testing is planned, you MUST stop the following medications 7 days before your appointment:</p>
            <ul>
                <li>All antihistamines (Claritin, Zyrtec, Allegra, Benadryl)</li>
                <li>Cold medications containing antihistamines</li>
                <li>Sleep aids like Tylenol PM</li>
            </ul>
            <p><strong>You MAY continue:</strong> Nasal sprays (Flonase, Nasacort), asthma inhalers, and prescription medications</p>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown('''
        <div class="emergency-note">
            <h4>🚨 If This is a Medical Emergency</h4>
            <p>If you are experiencing a medical emergency, please call 911 immediately or go to your nearest emergency room. Do not wait for your appointment.</p>
        </div>
        ''', unsafe_allow_html=True)
        
        # Consent and Signature
        st.markdown('<h2 class="section-header">✍️ Consent and Acknowledgment</h2>', unsafe_allow_html=True)
        
        consent1 = st.checkbox("I certify that the information provided is accurate to the best of my knowledge *")
        consent2 = st.checkbox("I understand that I should arrive 15 minutes early for my appointment *")
        consent3 = st.checkbox("I have read and understand the pre-visit instructions above *")
        consent4 = st.checkbox("I consent to receive appointment reminders via email and SMS")
        
        col1, col2 = st.columns(2)
        with col1:
            digital_signature = st.text_input("Digital Signature (type your full name) *", placeholder="Type your full name as digital signature")
        
        with col2:
            signature_date = st.date_input("Date *", value=datetime.now().date())
        
        # Submit button
        submitted = st.form_submit_button("📧 Submit Intake Form", use_container_width=True)
        
        if submitted:
            # Validation
            required_fields = [
                (first_name, "First Name"),
                (last_name, "Last Name"),
                (phone, "Phone Number"),
                (email, "Email Address"),
                (emergency_name, "Emergency Contact Name"),
                (emergency_phone, "Emergency Contact Phone"),
                (emergency_relationship, "Emergency Relationship"),
                (insurance_company, "Insurance Company"),
                (member_id, "Member ID"),
                (chief_complaint, "Chief Complaint"),
                (current_medications, "Current Medications"),
                (allergies, "Known Allergies"),
                (digital_signature, "Digital Signature")
            ]
            
            missing_fields = []
            for field_value, field_name in required_fields:
                if not field_value or field_value.strip() == "":
                    missing_fields.append(field_name)
            
            if not consent1 or not consent2 or not consent3:
                missing_fields.append("Required Consent Checkboxes")
            
            if missing_fields:
                st.error(f"❌ Please fill in the following required fields: {', '.join(missing_fields)}")
            else:
                # Save form data
                form_data = {
                    'patient_id': patient_id,
                    'first_name': first_name,
                    'last_name': last_name,
                    'date_of_birth': date_of_birth,
                    'gender': gender,
                    'phone': phone,
                    'email': email,
                    'address': address,
                    'emergency_name': emergency_name,
                    'emergency_phone': emergency_phone,
                    'emergency_relationship': emergency_relationship,
                    'insurance_company': insurance_company,
                    'member_id': member_id,
                    'group_number': group_number,
                    'chief_complaint': chief_complaint,
                    'symptom_duration': symptom_duration,
                    'pain_level': pain_level,
                    'current_medications': current_medications,
                    'allergies': allergies,
                    'medical_conditions': ', '.join(selected_conditions),
                    'other_conditions': other_conditions,
                    'family_history': family_history,
                    'smoking_status': smoking_status,
                    'alcohol_use': alcohol_use,
                    'exercise_habits': exercise_habits,
                    'consent1': consent1,
                    'consent2': consent2,
                    'consent3': consent3,
                    'consent4': consent4,
                    'digital_signature': digital_signature,
                    'signature_date': signature_date,
                    'appointment_date': patient_info['appointment_date'],
                    'appointment_time': patient_info['appointment_time'],
                    'doctor_name': patient_info['doctor_name'],
                    'specialty': patient_info['specialty'],
                    'duration': patient_info['duration']
                }
                
                try:
                    form_id = save_intake_form(form_data)
                    st.success("✅ Your intake form has been submitted successfully!")
                    st.info(f"📋 Form ID: {form_id}")
                    st.info("Thank you for completing your intake form. We'll see you at your appointment!")
                    
                    # Display next steps
                    st.markdown("""
                    ### 📍 Next Steps:
                    1. **Arrive 15 minutes early** for your appointment
                    2. **Bring your insurance card and photo ID**
                    3. **Bring your current medications list**
                    4. **Remember the pre-visit instructions** if allergy testing is planned
                    
                    ### 📞 Questions?
                    Call us at **(555) 123-4567** - We're here to help Monday-Friday, 8 AM - 5 PM
                    """)
                    
                except Exception as e:
                    st.error(f"❌ Error saving form: {str(e)}")
                    st.error("Please try again or contact our office at (555) 123-4567")

if __name__ == "__main__":
    main()

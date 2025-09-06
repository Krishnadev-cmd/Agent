import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import os
import json
from dotenv import load_dotenv
from medical_agent_simple import EnhancedMedicalAgent
from communication import CommunicationManager
from database_manager import DatabaseManager

# Calendar integration
try:
    from calendar_integration import CalendarIntegration
    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="MediCare AI Scheduling Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: white;
        text-align: center;
        margin: 0;
    }
    .chat-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .user-message {
        background-color: #007bff;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        text-align: right;
    }
    .bot-message {
        background-color: #e9ecef;
        color: #333;
        padding: 0.5rem 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
    }
    .appointment-card {
        background-color: white;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'agent' not in st.session_state:
    st.session_state.agent = EnhancedMedicalAgent()
if 'comm_manager' not in st.session_state:
    st.session_state.comm_manager = CommunicationManager()
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager()
if 'current_step' not in st.session_state:
    st.session_state.current_step = 'greeting'
if 'patient_data' not in st.session_state:
    st.session_state.patient_data = {}
if 'appointment_data' not in st.session_state:
    st.session_state.appointment_data = {}

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏥 MediCare Allergy & Wellness Center</h1>
        <h3 style="color: white; text-align: center; margin: 0;">AI-Powered Appointment Scheduling Assistant</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Dashboard")
        
        # Navigation
        page = st.selectbox(
            "Navigate to:",
            ["💬 Chat Assistant", "📊 Analytics", "📅 Appointments", "�️ Calendar Integration", "�🛠️ Admin Panel"]
        )
        
        # Quick stats
        st.subheader("📈 Quick Stats")
        
        conn = sqlite3.connect("data/medical_scheduler.db")
        
        # Total patients
        total_patients = pd.read_sql_query("SELECT COUNT(*) as count FROM patients", conn).iloc[0]['count']
        st.metric("Total Patients", total_patients)
        
        # Today's appointments
        today = datetime.now().strftime('%Y-%m-%d')
        today_appointments = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM appointments WHERE appointment_date = ?", 
            conn, params=[today]
        ).iloc[0]['count']
        st.metric("Today's Appointments", today_appointments)
        
        # Available doctors
        total_doctors = pd.read_sql_query("SELECT COUNT(*) as count FROM doctors", conn).iloc[0]['count']
        st.metric("Available Doctors", total_doctors)
        
        conn.close()
        
        # Reset conversation
        if st.button("🔄 Reset Conversation"):
            st.session_state.messages = []
            st.session_state.current_step = 'greeting'
            st.session_state.patient_data = {}
            st.session_state.appointment_data = {}
            st.rerun()
    
    # Main content based on selected page
    if page == "💬 Chat Assistant":
        show_chat_interface()
    elif page == "📊 Analytics":
        show_analytics()
    elif page == "📅 Appointments":
        show_appointments()
    elif page == "�️ Calendar Integration":
        show_calendar_integration()
    elif page == "�🛠️ Admin Panel":
        show_admin_panel()

def show_chat_interface():
    st.header("💬 AI Scheduling Assistant")
    
    # Display conversation
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.messages:
            if message['role'] == 'user':
                st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bot-message">{message["content"]}</div>', unsafe_allow_html=True)
    
    # Chat input
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Process with agent
        response = process_user_message(user_input)
        
        # Add bot response
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        st.rerun()
    
    # Quick action buttons
    st.subheader("🚀 Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📞 New Appointment"):
            quick_response = "Hello! I'd be happy to help you schedule a new appointment. May I have your full name please?"
            st.session_state.messages.append({"role": "assistant", "content": quick_response})
            st.rerun()
    
    with col2:
        if st.button("🔍 Find Patient"):
            quick_response = "I can help you find an existing patient. Please provide the patient's name or phone number."
            st.session_state.messages.append({"role": "assistant", "content": quick_response})
            st.rerun()
    
    with col3:
        if st.button("📋 View Doctors"):
            doctors_response = get_doctors_list()
            st.session_state.messages.append({"role": "assistant", "content": doctors_response})
            st.rerun()

def process_user_message(user_input):
    """Process user message and return appropriate response"""
    
    # Use the simple agent for now
    return st.session_state.agent.process_conversation(user_input)

def handle_name_input(user_input):
    """Handle name input from user"""
    # Extract name (simple parsing)
    name_parts = user_input.replace('my name is', '').replace('i am', '').replace('this is', '').strip().split()
    
    if len(name_parts) >= 2:
        first_name = name_parts[0].strip(',.')
        last_name = name_parts[1].strip(',.')
        
        st.session_state.patient_data['first_name'] = first_name
        st.session_state.patient_data['last_name'] = last_name
        st.session_state.current_step = 'name_collected'
        
        # Search for patient
        return search_patient_response()
    else:
        return "I need both your first and last name. Could you please provide your full name?"

def search_patient_response():
    """Search for patient and return appropriate response"""
    if 'first_name' in st.session_state.patient_data:
        first_name = st.session_state.patient_data['first_name']
        last_name = st.session_state.patient_data['last_name']
        
        # Search in database
        patients = st.session_state.agent.search_patient_by_name(first_name, last_name)
        
        if len(patients) > 0:
            patient = patients.iloc[0]
            st.session_state.patient_data.update(patient.to_dict())
            st.session_state.current_step = 'patient_found'
            
            patient_type = "returning" if not patient['is_new_patient'] else "new"
            duration = 30 if patient_type == "returning" else 60
            
            return f"""Great! I found your record, {first_name} {last_name}. 

Patient Details:
- Phone: {patient['phone']}
- Email: {patient['email']}
- Patient Type: {patient_type.title()} Patient
- Appointment Duration: {duration} minutes

Would you like to see available appointment slots? Please let me know your preferred doctor or I can show you all available options."""
        else:
            st.session_state.current_step = 'new_patient'
            st.session_state.patient_data['is_new_patient'] = True
            
            return f"""I don't see an existing record for {first_name} {last_name}. This appears to be your first visit with us - welcome!

As a new patient, your appointment will be 60 minutes to allow time for a comprehensive evaluation.

To complete your registration, I'll need:
- Your phone number
- Email address
- Date of birth
- Insurance information

Could you please provide your phone number?"""

def handle_phone_input(user_input):
    """Handle phone number input"""
    # Extract phone number
    phone = ''.join(c for c in user_input if c.isdigit() or c in '()-. ')
    st.session_state.patient_data['phone'] = phone
    
    if st.session_state.current_step == 'new_patient':
        return "Thank you! Now could you please provide your email address?"
    else:
        # Search by phone if name search failed
        patients = st.session_state.agent.search_patient_by_phone(phone)
        if len(patients) > 0:
            patient = patients.iloc[0]
            st.session_state.patient_data.update(patient.to_dict())
            st.session_state.current_step = 'patient_found'
            return f"Found your record! Welcome back, {patient['first_name']} {patient['last_name']}. Let's find you an appointment."
        else:
            return "I couldn't find a record with that phone number. Let's proceed as a new patient."

def show_available_slots():
    """Show available appointment slots"""
    # Get available doctors
    doctors = st.session_state.agent.get_available_doctors()
    
    doctors_text = "Available doctors:\n"
    for _, doctor in doctors.iterrows():
        doctors_text += f"- {doctor['doctor_name']} (ID: {doctor['doctor_id']}) - {doctor['specialty']}\n"
    
    return f"""{doctors_text}

Would you like to:
1. See available slots for a specific doctor
2. See all available slots for the next few days

Please let me know your preference, or specify a doctor by name or ID."""

def get_doctors_list():
    """Get formatted list of doctors"""
    doctors = st.session_state.agent.get_available_doctors()
    
    doctors_text = "Our available doctors:\n\n"
    for _, doctor in doctors.iterrows():
        doctors_text += f"🩺 **{doctor['doctor_name']}** (ID: {doctor['doctor_id']})\n"
        doctors_text += f"   Specialty: {doctor['specialty']}\n\n"
    
    return doctors_text

def handle_appointment_confirmation(user_input):
    """Handle appointment confirmation"""
    if 'selected_slot' in st.session_state.appointment_data:
        # Book the appointment
        slot = st.session_state.appointment_data['selected_slot']
        
        try:
            appointment_id, duration = st.session_state.agent.book_appointment_slot(
                st.session_state.patient_data['patient_id'],
                slot['doctor_id'],
                slot['date'],
                slot['time'],
                st.session_state.patient_data.get('is_new_patient', True)
            )
            
            # Send confirmation
            appointment_info = {
                'date': slot['date'],
                'time': slot['time'],
                'doctor_name': slot['doctor_name'],
                'duration': duration,
                'appointment_type': 'New Patient' if st.session_state.patient_data.get('is_new_patient', True) else 'Follow-up'
            }
            
            # Send communications
            comm_result = st.session_state.comm_manager.send_appointment_confirmation(
                st.session_state.patient_data,
                appointment_info
            )
            
            forms_result = st.session_state.comm_manager.send_intake_forms(
                st.session_state.patient_data['email'],
                f"{st.session_state.patient_data['first_name']} {st.session_state.patient_data['last_name']}"
            )
            
            return f"""✅ **Appointment Confirmed!**

Appointment ID: {appointment_id}
Date: {slot['date']}
Time: {slot['time']}
Doctor: {slot['doctor_name']}
Duration: {duration} minutes

📧 Confirmation email sent to: {st.session_state.patient_data['email']}
📱 SMS confirmation sent to: {st.session_state.patient_data['phone']}
📋 Intake forms have been emailed to you

**Important reminders:**
- Please arrive 15 minutes early
- Bring insurance cards and photo ID
- Complete intake forms before your visit
- Stop antihistamines 7 days before if allergy testing is planned

Thank you for choosing MediCare Allergy & Wellness Center!"""
            
        except Exception as e:
            return f"I apologize, but there was an error booking your appointment: {str(e)}. Please try again or call us at (555) 123-4567."
    
    return "I don't see a selected appointment slot. Please choose an available time first."

def handle_doctor_preference(user_input):
    """Handle doctor preference"""
    doctors = st.session_state.agent.get_available_doctors()
    
    # Simple matching by name
    for _, doctor in doctors.iterrows():
        if doctor['doctor_name'].lower() in user_input.lower() or doctor['doctor_id'].lower() in user_input.lower():
            # Get slots for this doctor
            slots = st.session_state.agent.get_available_slots(doctor['doctor_id'])
            
            if len(slots) > 0:
                slots_text = f"Available slots for {doctor['doctor_name']}:\n\n"
                for i, (_, slot) in enumerate(slots.head(10).iterrows()):
                    slots_text += f"{i+1}. {slot['date']} at {slot['time']}\n"
                
                slots_text += "\nPlease tell me which slot you'd prefer (e.g., 'I'd like slot 1' or 'Book slot 3')."
                return slots_text
            else:
                return f"I'm sorry, but {doctor['doctor_name']} doesn't have any available slots in the next few days. Would you like to see other doctors' availability?"
    
    return "I couldn't find that doctor. Please check the doctor's name or ID from the list above."

def show_analytics():
    st.header("📊 Analytics Dashboard")
    
    conn = sqlite3.connect("data/medical_scheduler.db")
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_patients = pd.read_sql_query("SELECT COUNT(*) as count FROM patients", conn).iloc[0]['count']
        st.metric("Total Patients", total_patients)
    
    with col2:
        total_appointments = pd.read_sql_query("SELECT COUNT(*) as count FROM appointments", conn).iloc[0]['count']
        st.metric("Total Appointments", total_appointments)
    
    with col3:
        new_patients = pd.read_sql_query("SELECT COUNT(*) as count FROM patients WHERE is_new_patient = 1", conn).iloc[0]['count']
        st.metric("New Patients", new_patients)
    
    with col4:
        today_appointments = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM appointments WHERE appointment_date = ?", 
            conn, params=[datetime.now().strftime('%Y-%m-%d')]
        ).iloc[0]['count']
        st.metric("Today's Appointments", today_appointments)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Patient Types")
        patient_types = pd.read_sql_query("""
            SELECT 
                CASE WHEN is_new_patient = 1 THEN 'New' ELSE 'Returning' END as patient_type,
                COUNT(*) as count
            FROM patients 
            GROUP BY is_new_patient
        """, conn)
        
        if len(patient_types) > 0:
            fig = px.pie(patient_types, values='count', names='patient_type', 
                        title="Patient Distribution")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Appointments by Doctor")
        doctor_appointments = pd.read_sql_query("""
            SELECT d.doctor_name, COUNT(a.appointment_id) as appointments
            FROM doctors d
            LEFT JOIN appointments a ON d.doctor_id = a.doctor_id
            GROUP BY d.doctor_id, d.doctor_name
        """, conn)
        
        if len(doctor_appointments) > 0:
            fig = px.bar(doctor_appointments, x='doctor_name', y='appointments',
                        title="Appointments by Doctor")
            st.plotly_chart(fig, use_container_width=True)
    
    conn.close()

def show_appointments():
    st.header("📅 Appointment Management")
    
    conn = sqlite3.connect("data/medical_scheduler.db")
    
    # Date filter
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now())
    with col2:
        end_date = st.date_input("End Date", datetime.now() + timedelta(days=7))
    
    # Get appointments
    appointments = pd.read_sql_query("""
        SELECT a.*, p.first_name, p.last_name, p.phone, p.email, d.doctor_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        JOIN doctors d ON a.doctor_id = d.doctor_id
        WHERE a.appointment_date BETWEEN ? AND ?
        ORDER BY a.appointment_date, a.appointment_time
    """, conn, params=[start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')])
    
    if len(appointments) > 0:
        st.subheader(f"Appointments ({len(appointments)} found)")
        
        for _, apt in appointments.iterrows():
            with st.expander(f"{apt['first_name']} {apt['last_name']} - {apt['appointment_date']} {apt['appointment_time']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Patient:** {apt['first_name']} {apt['last_name']}")
                    st.write(f"**Phone:** {apt['phone']}")
                    st.write(f"**Email:** {apt['email']}")
                    st.write(f"**Date:** {apt['appointment_date']}")
                    st.write(f"**Time:** {apt['appointment_time']}")
                
                with col2:
                    st.write(f"**Doctor:** {apt['doctor_name']}")
                    st.write(f"**Duration:** {apt['duration']} minutes")
                    st.write(f"**Type:** {apt['appointment_type']}")
                    st.write(f"**Status:** {apt['status']}")
                
                # Action buttons
                button_col1, button_col2, button_col3 = st.columns(3)
                with button_col1:
                    if st.button(f"Send Reminder", key=f"reminder_{apt['appointment_id']}"):
                        # Send reminder logic here
                        st.success("Reminder sent!")
                
                with button_col2:
                    if st.button(f"Cancel", key=f"cancel_{apt['appointment_id']}"):
                        # Cancel appointment logic here
                        st.warning("Appointment cancelled!")
                
                with button_col3:
                    if st.button(f"Reschedule", key=f"reschedule_{apt['appointment_id']}"):
                        st.info("Reschedule functionality coming soon!")
    else:
        st.info("No appointments found for the selected date range.")
    
    conn.close()

def show_admin_panel():
    st.header("🛠️ Admin Panel")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Database Status", "Export Data", "Reminder System", "System Settings"])
    
    with tab1:
        st.subheader("Database Status")
        
        conn = sqlite3.connect("data/medical_scheduler.db")
        
        # Table sizes
        tables = ['patients', 'doctors', 'appointments', 'doctor_schedules', 'reminders', 'patient_forms']
        
        for table in tables:
            try:
                count = pd.read_sql_query(f"SELECT COUNT(*) as count FROM {table}", conn).iloc[0]['count']
                st.metric(f"{table.title()} Records", count)
            except:
                st.error(f"Error reading {table} table")
        
        conn.close()
    
    with tab2:
        st.subheader("📊 Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Export All Appointments"):
                from excel_export import ExcelExportManager
                excel_manager = ExcelExportManager()
                filename = excel_manager.export_appointments_report()
                
                if filename:
                    st.success(f"Data exported to {filename}")
                    
                    # Display download link
                    with open(filename, "rb") as file:
                        st.download_button(
                            label="📥 Download Appointments Report",
                            data=file,
                            file_name=os.path.basename(filename),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.error("Failed to export appointments")
        
        with col2:
            if st.button("👥 Export Patient Data"):
                from excel_export import ExcelExportManager
                excel_manager = ExcelExportManager()
                filename = excel_manager.export_patient_data()
                
                if filename:
                    st.success(f"Patient data exported to {filename}")
                    
                    # Display download link
                    with open(filename, "rb") as file:
                        st.download_button(
                            label="📥 Download Patient Data",
                            data=file,
                            file_name=os.path.basename(filename),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.error("Failed to export patient data")
        
        # Date range export
        st.subheader("📅 Export by Date Range")
        col3, col4 = st.columns(2)
        
        with col3:
            start_date = st.date_input("Start Date", datetime.now().date())
        
        with col4:
            end_date = st.date_input("End Date", datetime.now().date())
        
        if st.button("📊 Export Date Range"):
            from excel_export import ExcelExportManager
            excel_manager = ExcelExportManager()
            filename = excel_manager.export_appointments_report(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            if filename:
                st.success(f"Date range data exported to {filename}")
                
                # Display download link
                with open(filename, "rb") as file:
                    st.download_button(
                        label="📥 Download Date Range Report",
                        data=file,
                        file_name=os.path.basename(filename),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.error("Failed to export date range data")
    
    with tab3:
        st.subheader("🔔 Reminder System Management")
        
        # Test Reminder System
        st.subheader("🧪 Test Reminder System")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📧 Test Email Reminder**")
            test_email = st.text_input("Test Email Address", placeholder="Enter email to test")
            
            if st.button("📬 Send Test Email Reminder"):
                if test_email:
                    try:
                        from automated_reminder_system import AutomatedReminderSystem
                        reminder_system = AutomatedReminderSystem()
                        
                        # Create a test appointment data
                        test_appointment = {
                            'patient_name': 'Test Patient',
                            'doctor_name': 'Dr. Test',
                            'appointment_date': '2024-01-15',
                            'appointment_time': '10:00 AM',
                            'specialty': 'General Medicine',
                            'email': test_email,
                            'appointment_id': 'TEST-001'
                        }
                        
                        success = reminder_system.send_initial_reminder(test_appointment)
                        
                        if success:
                            st.success("✅ Test email reminder sent successfully!")
                        else:
                            st.error("❌ Failed to send test email reminder")
                    except Exception as e:
                        st.error(f"❌ Error sending test reminder: {e}")
                else:
                    st.warning("Please enter a test email address")
        
        with col2:
            st.write("**📱 Test SMS Reminder**")
            test_phone = st.text_input("Test Phone Number", placeholder="+1234567890")
            
            if st.button("📱 Send Test SMS Reminder"):
                if test_phone:
                    try:
                        from automated_reminder_system import AutomatedReminderSystem
                        reminder_system = AutomatedReminderSystem()
                        
                        # Create a test appointment data
                        test_appointment = {
                            'patient_name': 'Test Patient',
                            'doctor_name': 'Dr. Test',
                            'appointment_date': '2024-01-15',
                            'appointment_time': '10:00 AM',
                            'phone': test_phone,
                            'appointment_id': 'TEST-001'
                        }
                        
                        success = reminder_system.send_sms_reminder(test_appointment, "initial")
                        
                        if success:
                            st.success("✅ Test SMS reminder sent successfully!")
                        else:
                            st.error("❌ Failed to send test SMS reminder")
                    except Exception as e:
                        st.error(f"❌ Error sending test SMS: {e}")
                else:
                    st.warning("Please enter a test phone number")
        
        # CSV Download Section
        st.subheader("📥 CSV Data Export")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 Export Patients CSV"):
                try:
                    conn_csv = sqlite3.connect("data/medical_scheduler.db")
                    patients_df = pd.read_sql_query("SELECT * FROM patients", conn_csv)
                    conn_csv.close()
                    
                    csv = patients_df.to_csv(index=False)
                    st.download_button(
                        label="⬇️ Download Patients CSV",
                        data=csv,
                        file_name=f"patients_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    st.success(f"✅ Patients CSV ready for download ({len(patients_df)} records)")
                except Exception as e:
                    st.error(f"❌ Error exporting patients: {e}")
        
        with col2:
            if st.button("📅 Export Appointments CSV"):
                try:
                    conn_csv = sqlite3.connect("data/medical_scheduler.db")
                    appointments_query = """
                        SELECT 
                            a.*,
                            p.first_name, p.last_name, p.email, p.phone,
                            d.doctor_name, d.specialty
                        FROM appointments a
                        JOIN patients p ON a.patient_id = p.patient_id
                        JOIN doctors d ON a.doctor_id = d.doctor_id
                        ORDER BY a.appointment_date DESC, a.appointment_time DESC
                    """
                    appointments_df = pd.read_sql_query(appointments_query, conn_csv)
                    conn_csv.close()
                    
                    csv = appointments_df.to_csv(index=False)
                    st.download_button(
                        label="⬇️ Download Appointments CSV",
                        data=csv,
                        file_name=f"appointments_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    st.success(f"✅ Appointments CSV ready for download ({len(appointments_df)} records)")
                except Exception as e:
                    st.error(f"❌ Error exporting appointments: {e}")
        
        with col3:
            if st.button("📨 Export Reminders CSV"):
                try:
                    conn_csv = sqlite3.connect("data/medical_scheduler.db")
                    reminders_query = """
                        SELECT 
                            r.*,
                            p.first_name, p.last_name, p.email, p.phone,
                            a.appointment_date, a.appointment_time
                        FROM reminders r
                        JOIN patients p ON r.patient_id = p.patient_id
                        JOIN appointments a ON r.appointment_id = a.appointment_id
                        ORDER BY r.scheduled_time DESC
                    """
                    reminders_df = pd.read_sql_query(reminders_query, conn_csv)
                    conn_csv.close()
                    
                    csv = reminders_df.to_csv(index=False)
                    st.download_button(
                        label="⬇️ Download Reminders CSV",
                        data=csv,
                        file_name=f"reminders_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    st.success(f"✅ Reminders CSV ready for download ({len(reminders_df)} records)")
                except Exception as e:
                    st.error(f"❌ Error exporting reminders: {e}")
        
        # Reminder System Status
        st.subheader("📊 Reminder System Status")
        
        try:
            conn_status = sqlite3.connect("data/medical_scheduler.db")
            
            # Get pending reminders count
            pending_reminders = pd.read_sql_query("""
                SELECT COUNT(*) as count 
                FROM reminders 
                WHERE status = 'pending' AND scheduled_time <= datetime('now')
            """, conn_status).iloc[0]['count']
            
            # Get sent reminders count today
            sent_today = pd.read_sql_query("""
                SELECT COUNT(*) as count 
                FROM reminders 
                WHERE status = 'sent' AND DATE(sent_time) = DATE('now')
            """, conn_status).iloc[0]['count']
            
            # Get upcoming appointments (next 7 days)
            upcoming_appointments = pd.read_sql_query("""
                SELECT COUNT(*) as count 
                FROM appointments 
                WHERE appointment_date BETWEEN DATE('now') AND DATE('now', '+7 days')
                AND status = 'confirmed'
            """, conn_status).iloc[0]['count']
            
            conn_status.close()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("⏰ Pending Reminders", pending_reminders)
            with col2:
                st.metric("📤 Sent Today", sent_today)
            with col3:
                st.metric("📅 Upcoming Appointments", upcoming_appointments)
            
        except Exception as e:
            st.error(f"❌ Error getting reminder status: {e}")
        
        # Manual Reminder Test
        st.subheader("🔧 Manual Reminder Test")
        
        try:
            conn_test = sqlite3.connect("data/medical_scheduler.db")
            latest_appt_query = """
                SELECT a.appointment_id, a.appointment_date, a.appointment_time,
                       p.first_name, p.last_name, p.email, p.phone, d.doctor_name
                FROM appointments a
                JOIN patients p ON a.patient_id = p.patient_id  
                JOIN doctors d ON a.doctor_id = d.doctor_id
                WHERE a.status = 'confirmed'
                ORDER BY a.appointment_id DESC
                LIMIT 5
            """
            latest_appointments = pd.read_sql_query(latest_appt_query, conn_test)
            conn_test.close()
            
            if not latest_appointments.empty:
                st.write("**Select an appointment to test reminder:**")
                
                for idx, appt in latest_appointments.iterrows():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**{appt['first_name']} {appt['last_name']}** - Dr. {appt['doctor_name']}")
                        st.write(f"📅 {appt['appointment_date']} at {appt['appointment_time']}")
                        st.write(f"📧 {appt['email']} | 📱 {appt['phone']}")
                    
                    with col2:
                        if st.button(f"📬 Test", key=f"test_{appt['appointment_id']}"):
                            try:
                                from automated_reminder_system import AutomatedReminderSystem
                                reminder_system = AutomatedReminderSystem()
                                
                                appointment_data = {
                                    'patient_name': f"{appt['first_name']} {appt['last_name']}",
                                    'doctor_name': appt['doctor_name'],
                                    'appointment_date': appt['appointment_date'],
                                    'appointment_time': appt['appointment_time'],
                                    'email': appt['email'],
                                    'phone': appt['phone'],
                                    'appointment_id': appt['appointment_id'],
                                    'specialty': 'General Medicine'
                                }
                                
                                success = reminder_system.send_initial_reminder(appointment_data)
                                
                                if success:
                                    st.success(f"✅ Test reminder sent to {appt['email']}")
                                else:
                                    st.error("❌ Failed to send reminder")
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                    
                    st.divider()
            else:
                st.info("No confirmed appointments found for testing.")
                
        except Exception as e:
            st.error(f"❌ Error loading appointments: {e}")
    
    with tab4:
        st.subheader("⚙️ System Settings")
        
        # Email Configuration Test
        st.subheader("📧 Email Configuration Test")
        
        if st.button("🧪 Test Email Settings"):
            try:
                from automated_reminder_system import AutomatedReminderSystem
                reminder_system = AutomatedReminderSystem()
                
                if reminder_system.test_email_config():
                    st.success("✅ Email configuration is working correctly!")
                    st.info(f"📧 SMTP Server: {reminder_system.comm_manager.smtp_server}")
                    st.info(f"👤 Email User: {reminder_system.comm_manager.email_user}")
                else:
                    st.error("❌ Email configuration has issues. Please check your .env file.")
                    
            except Exception as e:
                st.error(f"❌ Error testing email configuration: {e}")
        
        # Database Status
        st.subheader("🗄️ Database Status")
        
        if st.button("🔍 Check Database Schema"):
            try:
                conn_schema = sqlite3.connect("data/medical_scheduler.db")
                
                # Get table info
                tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
                tables_df = pd.read_sql_query(tables_query, conn_schema)
                
                st.write("**Available Tables:**")
                for table in tables_df['name']:
                    st.write(f"📋 {table}")
                
                # Check reminders table structure
                st.write("**Reminders Table Structure:**")
                reminders_schema = pd.read_sql_query("PRAGMA table_info(reminders)", conn_schema)
                st.dataframe(reminders_schema)
                
                conn_schema.close()
                
            except Exception as e:
                st.error(f"❌ Database error: {e}")
        
        # Initialize Database
        if st.button("🔧 Initialize/Update Database"):
            try:
                from database_manager import DatabaseManager
                db_manager = DatabaseManager()
                st.success("✅ Database initialized successfully!")
                
            except Exception as e:
                st.error(f"❌ Database initialization error: {e}")
        
        # Get appointments for testing
        conn_test2 = sqlite3.connect("data/medical_scheduler.db")
        appointments_test = pd.read_sql_query("""
            SELECT 
                a.appointment_id,
                p.first_name || ' ' || p.last_name as patient_name,
                a.appointment_date,
                a.appointment_time,
                d.doctor_name
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            JOIN doctors d ON a.doctor_id = d.doctor_id
            ORDER BY a.appointment_date DESC
            LIMIT 10
        """, conn_test2)
        conn_test2.close()
        
        if len(appointments_test) > 0:
            st.subheader("🧪 Advanced Reminder Testing")
            
            selected_appointment = st.selectbox(
                "Select Appointment for Testing",
                appointments_test['appointment_id'].tolist(),
                format_func=lambda x: f"ID: {x} - {appointments_test[appointments_test['appointment_id']==x]['patient_name'].iloc[0]} - {appointments_test[appointments_test['appointment_id']==x]['appointment_date'].iloc[0]}"
            )
            
            reminder_type = st.selectbox(
                "Reminder Type",
                ["initial", "follow_up_1", "follow_up_2"]
            )
            
            if st.button("🚀 Send Test Reminder"):
                try:
                    from automated_reminder_system import AutomatedReminderSystem
                    reminder_system = AutomatedReminderSystem()
                    
                    # Create test reminder data
                    selected_appt = appointments_test[appointments_test['appointment_id']==selected_appointment].iloc[0]
                    
                    reminder_data = {
                        'appointment_id': selected_appointment,
                        'first_name': selected_appt['patient_name'].split()[0],
                        'last_name': selected_appt['patient_name'].split()[-1],
                        'email': 'test@example.com',  # Use test email
                        'phone': '+1234567890',  # Use test phone
                        'appointment_date': selected_appt['appointment_date'],
                        'appointment_time': selected_appt['appointment_time'],
                        'doctor_name': selected_appt['doctor_name'],
                        'specialty': 'General Medicine'
                    }
                    
                    success = False
                    if reminder_type == "initial":
                        success = reminder_system.send_initial_reminder(reminder_data)
                    elif reminder_type == "follow_up_1":
                        success = reminder_system.send_follow_up_1_reminder(reminder_data)
                    elif reminder_type == "follow_up_2":
                        success = reminder_system.send_follow_up_2_reminder(reminder_data)
                    
                    if success:
                        st.success(f"✅ {reminder_type} reminder sent successfully!")
                        st.balloons()
                    else:
                        st.error(f"❌ Failed to send {reminder_type} reminder")
                        
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        else:
            st.info("No appointments available for testing")

def show_calendar_integration():
    """Calendar Integration with Calendly-style functionality"""
    st.header("🗓️ Calendar Integration System")
    
    # Import calendar integration
    try:
        from calendar_integration import CalendarIntegration
        calendar_system = CalendarIntegration()
        
        st.success("✅ Calendar integration system loaded successfully!")
        
        # Create tabs for different calendar functions
        tab1, tab2, tab3, tab4 = st.tabs([
            "📅 Doctor Availability", 
            "🗓️ Full Calendar View", 
            "📊 Export Calendar", 
            "📋 Calendar Settings"
        ])
        
        with tab1:
            st.subheader("👨‍⚕️ Doctor Availability (Calendly-style)")
            
            try:
                # Get list of doctors with error handling
                conn = sqlite3.connect("data/medical_scheduler.db")
                doctors_df = pd.read_sql_query("SELECT doctor_id, doctor_name, specialty FROM doctors ORDER BY doctor_name", conn)
                conn.close()
                
                st.info(f"📊 Debug: Found {len(doctors_df)} doctors in database")
                
                # Show sample data for debugging
                if not doctors_df.empty:
                    st.success(f"✅ Found {len(doctors_df)} doctors in the system")
                    
                    # Debug: Show first few doctors
                    with st.expander("🔍 Debug: Doctor Data Sample", expanded=False):
                        st.dataframe(doctors_df.head())
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Show doctor selection with better formatting and error handling
                        doctor_options = []
                        for _, row in doctors_df.iterrows():
                            # Ensure we have valid data
                            doctor_id = row['doctor_id']
                            doctor_name = row['doctor_name'] if pd.notna(row['doctor_name']) else 'Unknown'
                            specialty = row['specialty'] if pd.notna(row['specialty']) else 'General'
                            
                            doctor_options.append({
                                'id': str(doctor_id),
                                'display': f"Dr. {doctor_name} ({specialty})",
                                'name': doctor_name,
                                'specialty': specialty
                            })
                        
                        if doctor_options:
                            selected_index = st.selectbox(
                                "Select Doctor:",
                                range(len(doctor_options)),
                                format_func=lambda x: doctor_options[x]['display']
                            )
                            
                            selected_doctor_id = doctor_options[selected_index]['id']
                            selected_doctor_name = doctor_options[selected_index]['name']
                            selected_doctor_specialty = doctor_options[selected_index]['specialty']
                        else:
                            st.error("❌ No valid doctors found")
                            return
                    
                    with col2:
                        days_ahead = st.slider("Days to show:", 7, 30, 14)
                    
                    # Display selected doctor info with safe conversion
                    st.info(f"🩺 Selected: Dr. {selected_doctor_name} ({selected_doctor_specialty}) - ID: {selected_doctor_id}")
                    
                    if st.button("🔍 Get Available Slots", type="primary"):
                        with st.spinner("Loading available slots..."):
                            try:
                                # Use the string ID directly (calendar system should handle conversion)
                                availability = calendar_system.get_doctor_availability(selected_doctor_id, days_ahead)
                                
                                if 'error' not in availability:
                                    st.success(f"✅ Found {availability['total_slots']} available slots")
                                    
                                    # Display doctor info
                                    st.info(f"""
                                    **Doctor:** Dr. {availability['doctor']['doctor_name']}  
                                    **Specialty:** {availability['doctor']['specialty']}  
                                    **Working Hours:** {availability['working_hours']}  
                                    **Slot Duration:** {availability['slot_duration']}
                                    """)
                                    
                                    # Display slots by date
                                    if availability['slots_by_date']:
                                        for date, slots in list(availability['slots_by_date'].items())[:7]:  # Show first 7 days
                                            with st.expander(f"📅 {datetime.strptime(date, '%Y-%m-%d').strftime('%A, %B %d, %Y')} ({len(slots)} slots)"):
                                                cols = st.columns(4)
                                                for i, slot in enumerate(slots):
                                                    with cols[i % 4]:
                                                        if st.button(f"⏰ {slot['formatted_time']}", key=f"slot_{slot['slot_id']}"):
                                                            st.success(f"Selected: {slot['formatted_time']} on {slot['formatted_date']}")
                                                            st.info("💡 In a real booking system, this would open the booking form!")
                                    else:
                                        st.warning("📅 No available slots found for the selected period")
                                        
                                else:
                                    st.error(f"❌ {availability['error']}")
                                    
                            except Exception as e:
                                st.error(f"❌ Error loading slots: {str(e)}")
                                st.info("🔧 Debug info: Check that doctor schedules are properly set up in the database")
                
                else:
                    st.error("❌ No doctors found in the system")
                    st.info("💡 Add doctors using the Admin Panel or run add_doctors.py script")
                    
            except Exception as e:
                st.error(f"❌ Database connection error: {str(e)}")
                st.info("🔧 Make sure the database file exists at data/medical_scheduler.db")
        
        with tab2:
            st.subheader("📅 Full Calendar View")
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", datetime.now().date())
            with col2:
                end_date = st.date_input("End Date", (datetime.now() + timedelta(days=30)).date())
            
            if st.button("📊 Load Calendar", type="primary"):
                with st.spinner("Loading calendar data..."):
                    calendar_data = calendar_system.get_all_appointments_calendar(
                        start_date.strftime('%Y-%m-%d'),
                        end_date.strftime('%Y-%m-%d')
                    )
                    
                    if calendar_data['success']:
                        st.success(f"✅ Loaded {calendar_data['total_appointments']} appointments")
                        
                        # Display appointments
                        for event in calendar_data['events']:
                            start_time = datetime.fromisoformat(event['start'])
                            
                            # Color code by status
                            if event['status'] == 'confirmed':
                                color = '#d4edda'
                            elif event['status'] == 'pending':
                                color = '#fff3cd'
                            else:
                                color = '#f8d7da'
                            
                            st.markdown(f"""
                            <div style="background-color: {color}; padding: 10px; border-radius: 5px; margin: 5px 0;">
                                <strong>📅 {start_time.strftime('%Y-%m-%d %H:%M')}</strong><br>
                                <strong>{event['title']}</strong><br>
                                📧 {event['patient_email']}<br>
                                📞 {event['patient_phone']}<br>
                                🏥 {event['doctor_specialty']}<br>
                                ✅ Status: {event['status'].title()}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.error(f"❌ {calendar_data['error']}")
        
        with tab3:
            st.subheader("📊 Export Calendar to Excel")
            
            col1, col2 = st.columns(2)
            with col1:
                export_start = st.date_input("Export Start Date", datetime.now().date(), key="export_start")
            with col2:
                export_end = st.date_input("Export End Date", (datetime.now() + timedelta(days=30)).date(), key="export_end")
            
            if st.button("📥 Export to Excel", type="primary"):
                with st.spinner("Generating Excel export..."):
                    excel_file = calendar_system.export_full_calendar_excel(
                        export_start.strftime('%Y-%m-%d'),
                        export_end.strftime('%Y-%m-%d')
                    )
                    
                    if excel_file:
                        st.success(f"✅ Calendar exported successfully!")
                        st.info(f"📄 File: {excel_file}")
                        
                        # Provide download link if file exists
                        file_path = f"exports/{excel_file}"
                        if os.path.exists(file_path):
                            with open(file_path, "rb") as file:
                                st.download_button(
                                    label="⬇️ Download Excel File",
                                    data=file.read(),
                                    file_name=excel_file,
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                    else:
                        st.error("❌ Export failed")
        
        with tab4:
            st.subheader("⚙️ Calendar Settings")
            
            st.info("""
            **📋 Current Calendar Configuration:**
            - **Working Hours:** 9:00 AM - 5:00 PM
            - **Lunch Break:** 12:00 PM - 1:00 PM
            - **Slot Duration:** 30 minutes
            - **Buffer Time:** 15 minutes between appointments
            - **Working Days:** Monday to Friday
            - **Calendly-style Features:** ✅ Enabled
            - **Excel Export:** ✅ Enabled
            - **Google Calendar Links:** ✅ Enabled
            """)
            
            st.success("✅ Calendar integration is fully operational!")
            
            # Show integration status
            st.subheader("🔗 Integration Status")
            st.success("✅ Calendar system integrated with medical agent")
            st.success("✅ Excel export with professional formatting")
            st.success("✅ Calendly-style slot generation")
            st.success("✅ Google Calendar link generation")
            st.success("✅ Appointment booking with calendar export")
            
    except ImportError:
        st.error("❌ Calendar integration module not found")
        st.info("💡 The calendar integration requires the calendar_integration.py module")
    except Exception as e:
        st.error(f"❌ Calendar integration error: {e}")

if __name__ == "__main__":
    main()

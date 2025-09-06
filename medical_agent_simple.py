import os
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json
import re
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google Gemini imports
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage

# Calendar Integration import
try:
    from calendar_integration import CalendarIntegration
    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False
    print("⚠️  Calendar integration not available")

class EnhancedMedicalAgent:
    def __init__(self):
        self.db_path = "data/medical_scheduler.db"
        
        # Initialize Google Gemini
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not found")
            
        genai.configure(api_key=api_key)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.3,
            google_api_key=api_key,
            convert_system_message_to_human=True
        )
        
        self.conversation_context = {
            'patient_info': {},
            'appointment_details': {},
            'step': 'greeting',
            'conversation_history': [],
            'insurance_info': {},
            'scheduling_preferences': {},
            'form_sent': False,
            'reminders_scheduled': []
        }
        
        # Doctor specialties and symptoms mapping
        self.specialty_symptoms = {
            'Allergy & Immunology': [
                'allergies', 'asthma', 'eczema', 'hives', 'allergic reaction', 
                'food allergy', 'seasonal allergies', 'hay fever', 'runny nose',
                'itchy eyes', 'sneezing', 'skin rash', 'breathing problems'
            ],
            'Internal Medicine': [
                'fever', 'headache', 'fatigue', 'weight loss', 'weight gain',
                'high blood pressure', 'diabetes', 'chest pain', 'general checkup',
                'physical exam', 'routine care', 'preventive care'
            ],
            'Pulmonology': [
                'cough', 'shortness of breath', 'wheezing', 'lung problems',
                'respiratory issues', 'pneumonia', 'bronchitis', 'copd',
                'sleep apnea', 'smoking cessation'
            ],
            'Dermatology': [
                'skin problems', 'acne', 'rash', 'moles', 'skin cancer screening',
                'psoriasis', 'dermatitis', 'skin irritation', 'itchy skin'
            ]
        }
        
        # Initialize Calendar Integration
        if CALENDAR_AVAILABLE:
            self.calendar_system = CalendarIntegration()
            print("✅ Calendar integration initialized")
        else:
            self.calendar_system = None
            print("⚠️  Calendar integration disabled")
        
    def get_db_connection(self):
        return sqlite3.connect(self.db_path)
        
    def search_patient_by_name(self, first_name: str, last_name: str):
        """Search for existing patient by first and last name"""
        conn = self.get_db_connection()
        query = """
            SELECT * FROM patients 
            WHERE LOWER(first_name) LIKE LOWER(?) 
            AND LOWER(last_name) LIKE LOWER(?)
        """
        df = pd.read_sql_query(query, conn, params=[f"%{first_name}%", f"%{last_name}%"])
        conn.close()
        return df
    
    def search_patient_by_phone(self, phone: str):
        """Search for existing patient by phone number"""
        conn = self.get_db_connection()
        query = "SELECT * FROM patients WHERE phone LIKE ?"
        df = pd.read_sql_query(query, conn, params=[f"%{phone}%"])
        conn.close()
        return df
    
    def get_available_doctors(self):
        """Get list of available doctors and their specialties"""
        conn = self.get_db_connection()
        df = pd.read_sql_query("SELECT * FROM doctors", conn)
        conn.close()
        return df
    
    def get_available_slots(self, doctor_id: str, date: str = None):
        """Get available appointment slots for a specific doctor and date with calendar integration"""
        
        # Use calendar integration if available
        if self.calendar_system:
            try:
                if date:
                    # Get slots for specific date
                    slots = self.calendar_system.generate_available_slots(doctor_id, date, 1)
                    # Convert to DataFrame format for compatibility
                    slots_data = []
                    for slot in slots:
                        slots_data.append({
                            'doctor_id': doctor_id,
                            'date': slot['date'],
                            'time': slot['time'],
                            'is_available': 1,
                            'slot_id': slot['slot_id'],
                            'formatted_time': slot['formatted_time'],
                            'day_name': slot['day_name']
                        })
                    return pd.DataFrame(slots_data)
                else:
                    # Get slots for next 14 days
                    start_date = datetime.now().strftime('%Y-%m-%d')
                    slots = self.calendar_system.generate_available_slots(doctor_id, start_date, 14)
                    # Convert to DataFrame format for compatibility
                    slots_data = []
                    for slot in slots[:20]:  # Limit to 20 slots
                        slots_data.append({
                            'doctor_id': doctor_id,
                            'date': slot['date'],
                            'time': slot['time'],
                            'is_available': 1,
                            'slot_id': slot['slot_id'],
                            'formatted_time': slot['formatted_time'],
                            'day_name': slot['day_name']
                        })
                    return pd.DataFrame(slots_data)
            except Exception as e:
                print(f"Calendar integration error: {e}, falling back to database")
        
        # Fallback to original database method
        conn = self.get_db_connection()
        
        if date:
            query = """
                SELECT ds.*, d.doctor_name 
                FROM doctor_schedules ds 
                JOIN doctors d ON ds.doctor_id = d.doctor_id 
                WHERE ds.doctor_id = ? AND ds.date = ? AND ds.is_available = 1
                ORDER BY ds.time
            """
            params = [doctor_id, date]
        else:
            query = """
                SELECT ds.*, d.doctor_name 
                FROM doctor_schedules ds 
                JOIN doctors d ON ds.doctor_id = d.doctor_id 
                WHERE ds.doctor_id = ? AND ds.is_available = 1
                ORDER BY ds.date, ds.time
                LIMIT 20
            """
            params = [doctor_id]
            
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    
    def add_new_patient(self, patient_data: Dict) -> str:
        """Add a new patient to the database"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Generate a unique patient ID
            import uuid
            patient_id = str(uuid.uuid4())[:8]  # Use first 8 characters of UUID
            
            cursor.execute("""
                INSERT INTO patients (patient_id, first_name, last_name, email, phone, 
                                    date_of_birth, age, symptoms, medical_history, 
                                    preferred_location, is_new_patient)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                patient_id,  # Add the patient_id here
                patient_data.get('first_name'),
                patient_data.get('last_name'),
                patient_data.get('email'),
                patient_data.get('phone'),
                patient_data.get('date_of_birth', '1990-01-01'),
                patient_data.get('age', 0),
                patient_data.get('symptoms', ''),
                patient_data.get('medical_history', ''),
                patient_data.get('preferred_location', 'Main Office'),
                True
            ))
            
            conn.commit()
            print(f"✅ New patient created with ID: {patient_id}")
            return patient_id  # Return the actual patient_id, not rowid
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def recommend_doctors(self, symptoms: str, medical_history: str = "") -> List[Dict]:
        """Recommend doctors based on symptoms and medical history"""
        symptoms_lower = symptoms.lower()
        medical_history_lower = medical_history.lower()
        
        # Score doctors based on symptom match
        doctor_scores = {}
        doctors = self.get_available_doctors()
        
        for _, doctor in doctors.iterrows():
            specialty = doctor['specialty']
            score = 0
            
            if specialty in self.specialty_symptoms:
                for symptom_keyword in self.specialty_symptoms[specialty]:
                    if symptom_keyword in symptoms_lower or symptom_keyword in medical_history_lower:
                        score += 1
            
            doctor_scores[doctor['doctor_id']] = {
                'doctor': doctor,
                'score': score,
                'match_reasons': []
            }
        
        # Sort by score and return top recommendations
        sorted_doctors = sorted(doctor_scores.items(), key=lambda x: x[1]['score'], reverse=True)
        
        recommendations = []
        for doctor_id, data in sorted_doctors:
            doctor_info = data['doctor']
            recommendations.append({
                'doctor_id': doctor_info['doctor_id'],
                'name': doctor_info['doctor_name'],
                'specialty': doctor_info['specialty'],
                'score': data['score'],
                'available_slots': self.get_available_slots(doctor_id)
            })
        
        return recommendations
    
    def extract_patient_info(self, text: str) -> Dict:
        """Extract patient information using Gemini AI"""
        prompt = f"""
        Extract patient information from the following text. Return a JSON object with the fields:
        - first_name
        - last_name
        - email (if mentioned)
        - phone (if mentioned)
        - symptoms (if mentioned)
        - medical_history (if mentioned)
        
        Text: "{text}"
        
        Only extract information that is explicitly mentioned. If something is not mentioned, leave it empty.
        Return only valid JSON format.
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            # Clean and parse the response
            json_text = response.content.strip()
            if json_text.startswith('```json'):
                json_text = json_text[7:-3]
            elif json_text.startswith('```'):
                json_text = json_text[3:-3]
            
            return json.loads(json_text)
        except Exception as e:
            print(f"Error extracting patient info: {e}")
            return {}
    
    def generate_ai_response(self, user_input: str, context: Dict) -> str:
        """Generate AI response using Gemini"""
        conversation_step = context.get('step', 'greeting')
        patient_info = context.get('patient_info', {})
        
        # Create context-aware prompt
        system_prompt = f"""
        You are a medical appointment scheduling assistant for MediCare Allergy & Wellness Center.
        
        Current conversation step: {conversation_step}
        Patient information: {json.dumps(patient_info, indent=2)}
        
        Guidelines:
        1. Be professional, empathetic, and helpful
        2. Always confirm important information
        3. Guide patients through the appointment booking process
        4. For new patients (60-min appointments), collect: name, email, phone, symptoms, medical history
        5. For existing patients (30-min appointments), offer to book follow-up appointments
        6. Recommend appropriate doctors based on symptoms
        7. Keep responses concise but complete
        
        User input: "{user_input}"
        
        Respond appropriately based on the conversation context.
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=system_prompt)])
            return response.content
        except Exception as e:
            print(f"Error generating AI response: {e}")
            return "I apologize, but I'm having trouble processing your request. Could you please try again?"
    
    def book_appointment_slot(self, patient_id: str, doctor_id: str, date: str, time: str, is_new_patient: bool = True):
        """Book an appointment slot for a patient with calendar integration"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Determine duration based on patient type
            duration = 60 if is_new_patient else 30
            appointment_type = "New Patient" if is_new_patient else "Follow-up"
            
            # Insert appointment
            cursor.execute("""
                INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, 
                                        duration, appointment_type, status)
                VALUES (?, ?, ?, ?, ?, ?, 'scheduled')
            """, (patient_id, doctor_id, date, time, duration, appointment_type))
            
            appointment_id = cursor.lastrowid
            
            # Mark slot as unavailable in database
            cursor.execute("""
                UPDATE doctor_schedules 
                SET is_available = 0, appointment_type = 'Booked' 
                WHERE doctor_id = ? AND date = ? AND time = ?
            """, (doctor_id, date, time))
            
            conn.commit()
            
            # 🗓️ CALENDAR INTEGRATION: Export to Excel with calendar formatting
            if self.calendar_system:
                try:
                    slot_data = {
                        'patient_id': patient_id,
                        'doctor_id': doctor_id,
                        'date': date,
                        'time': time,
                        'duration': duration,
                        'appointment_type': appointment_type
                    }
                    
                    # Create calendar entry and export to Excel
                    calendar_result = self.calendar_system.book_calendly_slot(slot_data)
                    
                    if calendar_result.get('success'):
                        print(f"✅ Calendar integration successful: {calendar_result['excel_export']}")
                        # Store calendar info in conversation context for later use
                        if hasattr(self, 'conversation_context'):
                            self.conversation_context['calendar_export'] = calendar_result['excel_export']
                            self.conversation_context['calendar_link'] = calendar_result.get('calendar_link')
                    else:
                        print(f"⚠️  Calendar integration failed: {calendar_result.get('error')}")
                        
                except Exception as e:
                    print(f"⚠️  Calendar integration error: {e}")
            
            return appointment_id, duration
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _schedule_appointment_reminders_internal(self, appointment_id: int, patient_id: str, appointment_date: str, appointment_time: str):
        """Schedule three automated reminders for the appointment"""
        from datetime import datetime, timedelta
        
        appointment_datetime = datetime.strptime(f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M")
        
        reminders = [
            {
                'type': 'initial',
                'time': appointment_datetime - timedelta(days=3),
                'message': 'This is a friendly reminder about your upcoming appointment at MediCare Allergy & Wellness Center.'
            },
            {
                'type': 'follow_up_1', 
                'time': appointment_datetime - timedelta(days=1),
                'message': 'Your appointment is tomorrow. Have you completed your intake forms? Please confirm your visit.'
            },
            {
                'type': 'follow_up_2',
                'time': appointment_datetime - timedelta(hours=2),
                'message': 'Your appointment is in 2 hours. Please confirm if you will be attending or if you need to cancel.'
            }
        ]
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            for reminder in reminders:
                cursor.execute("""
                    INSERT INTO reminders (appointment_id, patient_id, reminder_type, reminder_method, 
                                         message, scheduled_time, status)
                    VALUES (?, ?, ?, 'both', ?, ?, 'pending')
                """, (appointment_id, patient_id, reminder['type'], reminder['message'], reminder['time']))
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"Error scheduling reminders: {e}")
            return False
        finally:
            conn.close()
    
    def export_appointment_to_excel(self, appointment_id: int):
        """Export appointment details to Excel format"""
        import pandas as pd
        from datetime import datetime
        
        conn = self.get_db_connection()
        
        # Get appointment details with patient and doctor info
        query = """
            SELECT 
                a.*,
                p.first_name, p.last_name, p.phone, p.email, p.date_of_birth,
                p.insurance_company, p.member_id, p.group_number,
                d.doctor_name, d.specialty
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            JOIN doctors d ON a.doctor_id = d.doctor_id
            WHERE a.appointment_id = ?
        """
        
        df = pd.read_sql_query(query, conn, params=[appointment_id])
        conn.close()
        
        if len(df) > 0:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/appointment_confirmation_{appointment_id}_{timestamp}.xlsx"
            
            # Export to Excel
            df.to_excel(filename, index=False, sheet_name='Appointment_Details')
            return filename
        
        return None
    
    def send_appointment_confirmation(self, appointment_id: int):
        """Send appointment confirmation via email and SMS"""
        from communication import CommunicationManager
        
        conn = self.get_db_connection()
        query = """
            SELECT 
                a.*,
                p.first_name, p.last_name, p.phone, p.email,
                d.doctor_name, d.specialty
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            JOIN doctors d ON a.doctor_id = d.doctor_id
            WHERE a.appointment_id = ?
        """
        
        df = pd.read_sql_query(query, conn, params=[appointment_id])
        conn.close()
        
        if len(df) > 0:
            appt = df.iloc[0]
            comm_manager = CommunicationManager()
            
            # Email confirmation
            email_subject = "Appointment Confirmation - MediCare Allergy & Wellness"
            email_body = f"""
            Dear {appt['first_name']} {appt['last_name']},
            
            Your appointment has been confirmed!
            
            Appointment Details:
            - Date: {appt['appointment_date']}
            - Time: {appt['appointment_time']}
            - Doctor: Dr. {appt['doctor_name']} ({appt['specialty']})
            - Duration: {appt['duration']} minutes
            - Type: {appt['appointment_type']}
            
            Please arrive 15 minutes early for check-in.
            
            Best regards,
            MediCare Allergy & Wellness Center
            """
            
            # SMS confirmation
            sms_message = f"Appointment confirmed! {appt['appointment_date']} at {appt['appointment_time']} with Dr. {appt['doctor_name']}. Arrive 15 min early."
            
            try:
                # Send email
                email_result = comm_manager.send_email(appt['email'], email_subject, email_body)
                
                # Send SMS
                sms_result = comm_manager.send_sms(appt['phone'], sms_message)
                
                return {'email': email_result, 'sms': sms_result}
                
            except Exception as e:
                print(f"Error sending confirmations: {e}")
                return {'email': False, 'sms': False}
        
        return None
    
    def distribute_intake_forms(self, patient_id: str, appointment_id: int):
        """Email patient intake forms after appointment confirmation"""
        from communication import CommunicationManager
        import os
        
        conn = self.get_db_connection()
        patient_query = "SELECT * FROM patients WHERE patient_id = ?"
        patient_df = pd.read_sql_query(patient_query, conn, params=[patient_id])
        
        if len(patient_df) > 0:
            patient = patient_df.iloc[0]
            comm_manager = CommunicationManager()
            
            # Check if intake form exists
            form_path = "patient_intake_form.html"
            if os.path.exists(form_path):
                # Record form distribution
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO patient_forms (patient_id, appointment_id, form_type, form_status, sent_date)
                    VALUES (?, ?, 'intake', 'sent', ?)
                """, (patient_id, appointment_id, datetime.now()))
                conn.commit()
                
                # Email the form
                subject = "Patient Intake Forms - MediCare Allergy & Wellness"
                body = f"""
                Dear {patient['first_name']} {patient['last_name']},
                
                Please complete the attached intake forms before your upcoming appointment.
                
                This will help us provide you with the best possible care during your visit.
                
                If you have any questions, please don't hesitate to contact our office.
                
                Best regards,
                MediCare Allergy & Wellness Center
                """
                
                try:
                    result = comm_manager.send_email_with_attachment(
                        patient['email'], subject, body, form_path
                    )
                    
                    self.conversation_context['form_sent'] = True
                    return result
                    
                except Exception as e:
                    print(f"Error sending forms: {e}")
                    return False
        
        conn.close()
        return False

    def process_conversation(self, user_input: str) -> str:
        """Main conversation processing method with AI integration"""
        user_lower = user_input.lower().strip()
        
        # Add to conversation history
        self.conversation_context['conversation_history'].append({
            'user': user_input,
            'timestamp': datetime.now().isoformat()
        })
        
        try:
            # Check for test reminder request
            if 'test reminder' in user_lower:
                return self._handle_test_reminder_request(user_input)
            
            # Check for search patient request
            if any(phrase in user_lower for phrase in ['find patient', 'search patient', 'existing patient', 'look up patient', 'patient lookup']):
                self.conversation_context['step'] = 'search_patient'
                return """I can help you find an existing patient record. 🔍

Please provide either:
- Patient's full name (first and last name)
- Phone number

How would you like to search?"""
            
            if self.conversation_context['step'] == 'greeting':
                return self._handle_greeting(user_input)
            
            elif self.conversation_context['step'] == 'search_patient':
                return self._handle_search_patient(user_input)
            
            elif self.conversation_context['step'] == 'waiting_for_name':
                return self._handle_name_input(user_input)
            
            elif self.conversation_context['step'] == 'patient_found':
                return self._handle_existing_patient(user_input)
            
            elif self.conversation_context['step'] == 'collecting_new_patient_info':
                return self._handle_new_patient_info(user_input)
            
            elif self.conversation_context['step'] == 'waiting_for_dob':
                return self._handle_dob_input(user_input)
            
            elif self.conversation_context['step'] == 'waiting_for_email':
                return self._handle_email_input(user_input)
            
            elif self.conversation_context['step'] == 'waiting_for_phone':
                return self._handle_phone_input(user_input)
            
            elif self.conversation_context['step'] == 'waiting_for_location':
                return self._handle_location_input(user_input)
            
            elif self.conversation_context['step'] == 'waiting_for_symptoms':
                return self._handle_symptoms_input(user_input)
            
            elif self.conversation_context['step'] == 'waiting_for_medical_history':
                return self._handle_medical_history_input(user_input)
            
            elif self.conversation_context['step'] == 'waiting_for_insurance':
                return self._handle_insurance_input(user_input)
            
            elif self.conversation_context['step'] == 'waiting_for_member_id':
                return self._handle_member_id_input(user_input)
            
            elif self.conversation_context['step'] == 'waiting_for_group_number':
                return self._handle_group_number_input(user_input)
            
            elif self.conversation_context['step'] == 'showing_doctors':
                return self._handle_doctor_selection(user_input)
            
            elif self.conversation_context['step'] == 'showing_slots':
                return self._handle_slot_selection(user_input)
            
            elif self.conversation_context['step'] == 'confirm_appointment':
                return self._handle_appointment_confirmation(user_input)
            
            else:
                return self._handle_general_query(user_input)
                
        except Exception as e:
            print(f"Error in conversation processing: {e}")
            # Enhanced error handling with Gemini AI
            try:
                error_response = self.generate_ai_response(
                    f"The user said '{user_input}' but there was a system error. Provide a helpful response that acknowledges the issue and offers to restart or get help.",
                    {'step': 'error_recovery'}
                )
                return f"{error_response}\n\nWould you like to start over? Just say 'restart' or tell me how I can help you."
            except:
                return "I apologize, but I encountered an error. Let me start over. How can I help you schedule an appointment today?"
    
    def handle_specialty_request(self, specialty_request: str) -> str:
        """Handle requests for specific medical specialties using AI"""
        try:
            # Get all doctors
            all_doctors = self.get_available_doctors()
            
            # Use Gemini AI to match specialty requests to available specialties
            available_specialties = list(all_doctors['specialty'].unique())
            
            ai_prompt = f"""
            User is looking for: "{specialty_request}"
            
            Available medical specialties:
            {chr(10).join([f"- {spec}" for spec in available_specialties])}
            
            Which specialty best matches their request? Respond with the exact specialty name from the list, or "none" if no good match.
            """
            
            ai_response = self.generate_ai_response(ai_prompt, {'step': 'specialty_matching'})
            
            # Find matching specialty
            matched_specialty = None
            for specialty in available_specialties:
                if specialty.lower() in ai_response.lower():
                    matched_specialty = specialty
                    break
            
            if matched_specialty:
                # Show doctors for that specialty
                specialty_doctors = all_doctors[all_doctors['specialty'] == matched_specialty]
                
                response = f"**🩺 {matched_specialty} Specialists:**\n\n"
                
                for i, (_, doctor) in enumerate(specialty_doctors.iterrows(), 1):
                    # Get available slots
                    try:
                        slots = self.get_available_slots(doctor['doctor_id'])
                        slot_count = len(slots)
                    except:
                        slot_count = "Unknown"
                    
                    response += f"**{i}. Dr. {doctor['doctor_name']}**\n"
                    response += f"   📅 Available Slots: {slot_count}\n\n"
                
                response += f"We have {len(specialty_doctors)} doctors in {matched_specialty}. "
                response += "To schedule with any of these doctors, please type their number or name."
                
                return response
            else:
                return f"""I couldn't find an exact match for "{specialty_request}" in our available specialties.

**Our Available Specialties:**
{chr(10).join([f"• {spec}" for spec in sorted(available_specialties)])}

Could you please specify which specialty you're looking for, or describe your symptoms so I can recommend the best doctor?"""
                
        except Exception as e:
            print(f"Error handling specialty request: {e}")
            return "I encountered an error processing your specialty request. Could you please tell me which type of doctor you're looking for?"
    
    def _handle_greeting(self, user_input: str) -> str:
        """Handle initial greeting and move to name collection"""
        self.conversation_context['step'] = 'waiting_for_name'
        return """Welcome to MediCare Allergy & Wellness Center! 🏥

I'm here to help you schedule an appointment with one of our specialists. 

To get started, may I please have your full name?"""
    
    def _handle_search_patient(self, user_input: str) -> str:
        """Handle patient search by name or phone"""
        user_input = user_input.strip()
        
        # Check if input looks like a phone number
        phone_digits = ''.join(c for c in user_input if c.isdigit())
        if len(phone_digits) >= 10:
            # Search by phone
            patients = self.search_patient_by_phone(user_input)
            if len(patients) > 0:
                patient = patients.iloc[0]
                self.conversation_context['patient_info'] = patient.to_dict()
                self.conversation_context['step'] = 'patient_found'
                
                return f"""Found patient record! ✅

**Patient Details:**
- 👤 Name: {patient['first_name']} {patient['last_name']}
- 📞 Phone: {patient['phone']}
- 📧 Email: {patient['email']}
- 🏷️ Patient Type: {'New' if patient['is_new_patient'] else 'Returning'} Patient
- ⏱️ Appointment Duration: {60 if patient['is_new_patient'] else 30} minutes

Would you like to:
1. Schedule a new appointment
2. View appointment history
3. Update patient information

What would you prefer?"""
            else:
                return f"No patient found with phone number {user_input}. Would you like to:\n1. Try searching by name instead\n2. Register as a new patient\n\nPlease let me know how you'd like to proceed."
        
        else:
            # Search by name
            words = user_input.strip().split()
            if len(words) >= 2:
                first_name = words[0]
                last_name = words[-1]
                
                patients = self.search_patient_by_name(first_name, last_name)
                if len(patients) > 0:
                    if len(patients) == 1:
                        patient = patients.iloc[0]
                        self.conversation_context['patient_info'] = patient.to_dict()
                        self.conversation_context['step'] = 'patient_found'
                        
                        return f"""Found patient record! ✅

**Patient Details:**
- 👤 Name: {patient['first_name']} {patient['last_name']}
- 📞 Phone: {patient['phone']}
- 📧 Email: {patient['email']}
- 🏷️ Patient Type: {'New' if patient['is_new_patient'] else 'Returning'} Patient
- ⏱️ Appointment Duration: {60 if patient['is_new_patient'] else 30} minutes

Would you like to:
1. Schedule a new appointment
2. View appointment history
3. Update patient information

What would you prefer?"""
                    else:
                        # Multiple patients found
                        response = f"Found {len(patients)} patients with similar names:\n\n"
                        for i, (_, patient) in enumerate(patients.iterrows(), 1):
                            response += f"{i}. {patient['first_name']} {patient['last_name']} - {patient['phone']}\n"
                        response += "\nPlease provide the phone number or more specific information to identify the correct patient."
                        return response
                else:
                    return f"No patient found with name '{first_name} {last_name}'. Would you like to:\n1. Try a different spelling\n2. Search by phone number\n3. Register as a new patient\n\nPlease let me know how you'd like to proceed."
            else:
                return "Please provide either:\n- Full name (first and last name)\n- Phone number\n\nFor example: 'John Smith' or '555-123-4567'"
    
    def _handle_name_input(self, user_input: str) -> str:
        """Handle name input and patient lookup"""
        # Extract name using AI
        extracted_info = self.extract_patient_info(user_input)
        
        if not extracted_info.get('first_name') or not extracted_info.get('last_name'):
            # Try manual extraction
            words = user_input.strip().split()
            if len(words) >= 2:
                extracted_info['first_name'] = words[0]
                extracted_info['last_name'] = words[-1]
            else:
                return "I need both your first and last name. Could you please provide your full name? For example: 'John Smith'"
        
        first_name = extracted_info['first_name']
        last_name = extracted_info['last_name']
        
        # Search for existing patient
        patients = self.search_patient_by_name(first_name, last_name)
        
        if len(patients) > 0:
            # Existing patient found
            patient = patients.iloc[0]
            self.conversation_context['patient_info'] = patient.to_dict()
            self.conversation_context['step'] = 'patient_found'
            
            return f"""Great! I found your record, {first_name} {last_name}. ✅

**Patient Details:**
- 📞 Phone: {patient['phone']}
- 📧 Email: {patient['email']}
- 🏷️ Patient Type: Returning Patient
- ⏱️ Appointment Duration: 30 minutes

Since you're a returning patient, would you like to:
1. Book a follow-up appointment (30 minutes)
2. Update your information first
3. See available doctors and time slots

What would you prefer?"""
        else:
            # New patient
            self.conversation_context['patient_info'] = {
                'first_name': first_name, 
                'last_name': last_name, 
                'is_new_patient': True
            }
            self.conversation_context['step'] = 'waiting_for_dob'
            
            return f"""Welcome {first_name}! I don't see an existing record, so this will be your first visit with us. 🎉

As a new patient, your appointment will be **60 minutes** to ensure we have adequate time for a comprehensive evaluation.

To complete your registration, I'll need a few details:

**Step 1 of 6:** What's your date of birth? (Please use MM/DD/YYYY format)"""
    
    def _handle_existing_patient(self, user_input: str) -> str:
        """Handle existing patient options"""
        user_lower = user_input.lower()
        
        if any(word in user_lower for word in ['1', 'book', 'appointment', 'follow', 'schedule', 'new appointment', 'yes']):
            self.conversation_context['step'] = 'showing_doctors'
            return self._show_doctor_recommendations()
        
        elif any(word in user_lower for word in ['2', 'update', 'information', 'info']):
            return f"""Let me help you update your information. Current details:

**Current Information:**
- 👤 Name: {self.conversation_context['patient_info']['first_name']} {self.conversation_context['patient_info']['last_name']}
- 📞 Phone: {self.conversation_context['patient_info']['phone']}
- 📧 Email: {self.conversation_context['patient_info']['email']}

What would you like to update?
1. Phone number
2. Email address
3. Medical history
4. Continue to book appointment

Please let me know what you'd like to change."""
        
        elif any(word in user_lower for word in ['3', 'history', 'view', 'appointments']):
            # Get appointment history
            conn = self.get_db_connection()
            history_query = """
                SELECT a.*, d.doctor_name 
                FROM appointments a 
                JOIN doctors d ON a.doctor_id = d.doctor_id 
                WHERE a.patient_id = ? 
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
                LIMIT 5
            """
            history_df = pd.read_sql_query(history_query, conn, params=[self.conversation_context['patient_info']['patient_id']])
            conn.close()
            
            if len(history_df) > 0:
                response = "📋 **Recent Appointment History:**\n\n"
                for _, appt in history_df.iterrows():
                    response += f"• {appt['appointment_date']} at {appt['appointment_time']} - Dr. {appt['doctor_name']} ({appt['status']})\n"
                response += "\nWould you like to schedule a new appointment?"
                return response
            else:
                return "No appointment history found. Would you like to schedule your first appointment?"
        
        else:
            return """I can help you with:

1. **Schedule a new appointment** (30 minutes for returning patients)
2. **Update your information** (phone, email, medical history)
3. **View appointment history** (recent appointments)

What would you like to do? Please type 1, 2, 3, or describe what you need."""
    
    def _handle_dob_input(self, user_input: str) -> str:
        """Handle date of birth input with validation"""
        # Try to parse different date formats
        date_patterns = [
            r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})',  # MM/DD/YYYY or MM-DD-YYYY
            r'(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})',  # YYYY/MM/DD or YYYY-MM-DD
            r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2})'   # MM/DD/YY or MM-DD-YY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, user_input)
            if match:
                try:
                    if len(match.group(3)) == 2:  # Two-digit year
                        year = int(match.group(3))
                        if year < 30:  # Assume years 00-29 are 2000-2029
                            year += 2000
                        else:  # Assume years 30-99 are 1930-1999
                            year += 1900
                        month, day = int(match.group(1)), int(match.group(2))
                    elif pattern.startswith(r'(\d{4})'):  # YYYY format
                        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    else:  # MM/DD/YYYY format
                        month, day, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    
                    # Validate date
                    birth_date = datetime(year, month, day)
                    if birth_date > datetime.now():
                        return "The date of birth cannot be in the future. Please enter a valid date of birth (MM/DD/YYYY)."
                    
                    # Calculate age
                    age = (datetime.now() - birth_date).days // 365
                    if age > 120:
                        return "Please check the date - the age seems unusually high. Please enter your correct date of birth (MM/DD/YYYY)."
                    
                    self.conversation_context['patient_info']['date_of_birth'] = birth_date.strftime('%Y-%m-%d')
                    self.conversation_context['patient_info']['age'] = age
                    self.conversation_context['step'] = 'waiting_for_email'
                    
                    return f"""Thank you! I have your date of birth recorded. ✅

**Step 2 of 6:** What's your email address?"""
                    
                except ValueError:
                    continue
        
        return "I couldn't understand the date format. Please enter your date of birth in MM/DD/YYYY format (for example: 03/15/1990)."
    
    def _handle_location_input(self, user_input: str) -> str:
        """Handle location preference input"""
        user_lower = user_input.lower()
        
        # Define available locations
        locations = {
            '1': 'Main Office - Downtown Medical Center',
            '2': 'North Branch - Northside Clinic', 
            '3': 'South Branch - Wellness Center South',
            '4': 'West Branch - Medical Plaza West'
        }
        
        if user_lower in ['1', 'main', 'downtown']:
            selected_location = locations['1']
        elif user_lower in ['2', 'north', 'northside']:
            selected_location = locations['2']
        elif user_lower in ['3', 'south', 'wellness']:
            selected_location = locations['3']
        elif user_lower in ['4', 'west', 'plaza']:
            selected_location = locations['4']
        else:
            return """Please select your preferred location:

1. **Main Office** - Downtown Medical Center
2. **North Branch** - Northside Clinic  
3. **South Branch** - Wellness Center South
4. **West Branch** - Medical Plaza West

Please type 1, 2, 3, or 4 to select your preferred location."""
        
        self.conversation_context['patient_info']['preferred_location'] = selected_location
        self.conversation_context['step'] = 'waiting_for_symptoms'
        
        return f"""Great! I've noted your preferred location: {selected_location} ✅

**Step 5 of 6:** What symptoms or health concerns would you like to discuss during your visit? (This helps me recommend the best doctor for you)"""
    
    def _handle_email_input(self, user_input: str) -> str:
        """Handle email input"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, user_input)
        
        if email_match:
            email = email_match.group()
            self.conversation_context['patient_info']['email'] = email
            self.conversation_context['step'] = 'waiting_for_phone'
            
            return f"""Perfect! I've recorded your email as: {email} ✅

**Step 3 of 6:** What's your phone number?"""
        else:
            return "I need a valid email address. Please provide your email (e.g., john.smith@email.com):"
    
    def _handle_phone_input(self, user_input: str) -> str:
        """Handle phone input"""
        # Extract phone number (simple pattern)
        phone_pattern = r'[\d\-\(\)\s\+]{10,}'
        phone_match = re.search(phone_pattern, user_input)
        
        if phone_match:
            phone = re.sub(r'[^\d]', '', phone_match.group())
            if len(phone) >= 10:
                self.conversation_context['patient_info']['phone'] = phone
                self.conversation_context['step'] = 'waiting_for_location'
                
                return f"""Great! Phone number recorded: {phone} ✅

**Step 4 of 6:** Which location would you prefer for your appointment?

1. **Main Office** - Downtown Medical Center
2. **North Branch** - Northside Clinic  
3. **South Branch** - Wellness Center South
4. **West Branch** - Medical Plaza West

Please type 1, 2, 3, or 4 to select your preferred location."""
            else:
                return "Please provide a valid phone number with at least 10 digits."
        else:
            return "I need a valid phone number. Please provide your phone number."
    
    def _handle_symptoms_input(self, user_input: str) -> str:
        """Handle symptoms input"""
        self.conversation_context['patient_info']['symptoms'] = user_input
        self.conversation_context['step'] = 'waiting_for_medical_history'
        
        return f"""Thank you for sharing your symptoms. ✅

**Step 6 of 6:** Do you have any relevant medical history, current medications, or allergies I should know about?

(If none, just type "none" or "no medical history")"""
    
    def _handle_medical_history_input(self, user_input: str) -> str:
        """Handle medical history input and move to insurance collection"""
        self.conversation_context['patient_info']['medical_history'] = user_input
        self.conversation_context['step'] = 'waiting_for_insurance'
        
        return f"""Thank you! I've recorded your medical history. ✅

Now I need to collect your insurance information to complete your registration:

**Insurance Information:**
What's your insurance carrier/provider? (e.g., Blue Cross Blue Shield, Aetna, Cigna, etc.)"""
    
    def _handle_insurance_input(self, user_input: str) -> str:
        """Handle insurance carrier input"""
        self.conversation_context['insurance_info']['carrier'] = user_input.strip()
        self.conversation_context['step'] = 'waiting_for_member_id'
        
        return f"""Great! I've recorded your insurance carrier: {user_input} ✅

Now please provide your **Member ID** (usually found on your insurance card)."""
    
    def _handle_member_id_input(self, user_input: str) -> str:
        """Handle insurance member ID input"""
        self.conversation_context['insurance_info']['member_id'] = user_input.strip()
        self.conversation_context['step'] = 'waiting_for_group_number'
        
        return f"""Perfect! Member ID recorded. ✅

Finally, please provide your **Group Number** (also found on your insurance card)."""
    
    def _handle_group_number_input(self, user_input: str) -> str:
        """Handle insurance group number and complete registration"""
        self.conversation_context['insurance_info']['group_number'] = user_input.strip()
        
        # Add patient to database
        try:
            patient_id = self.add_new_patient(self.conversation_context['patient_info'])
            self.conversation_context['patient_info']['patient_id'] = patient_id
            self.conversation_context['step'] = 'showing_doctors'
            
            return f"""**Registration Complete!** ✅

Your patient information has been saved securely. Now let me recommend the best specialists for your needs based on your symptoms: "{self.conversation_context['patient_info']['symptoms']}"

{self._show_doctor_recommendations()}"""
            
        except Exception as e:
            print(f"Error adding patient: {e}")
            return "I encountered an error saving your information. Please try again or contact our office directly."
    
    def _show_doctor_recommendations(self) -> str:
        """Show recommended doctors based on symptoms with Gemini AI enhancement"""
        patient_info = self.conversation_context['patient_info']
        symptoms = patient_info.get('symptoms', '')
        medical_history = patient_info.get('medical_history', '')
        
        recommendations = self.recommend_doctors(symptoms, medical_history)
        
        if not recommendations:
            return "I apologize, but I couldn't find available doctors at the moment. Please contact our office directly."
        
        # Use Gemini AI to provide intelligent recommendations
        try:
            ai_context = f"""
            Patient symptoms: {symptoms}
            Medical history: {medical_history}
            Available doctors: {len(recommendations)} total doctors
            """
            
            ai_recommendation = self.generate_ai_response(
                f"Based on the patient's symptoms '{symptoms}' and medical history '{medical_history}', provide a brief, professional explanation of why certain medical specialties would be most appropriate.",
                {'step': 'doctor_recommendation', 'ai_context': ai_context}
            )
        except Exception as e:
            print(f"AI recommendation failed: {e}")
            ai_recommendation = ""
        
        # Show more doctors (increased from 3 to 8) with better organization
        response = "**🩺 Recommended Specialists:**\n\n"
        
        if ai_recommendation and len(ai_recommendation) < 200:
            response += f"*{ai_recommendation}*\n\n"
        
        # Group doctors by specialty for better display
        specialty_groups = {}
        for doctor in recommendations[:12]:  # Show top 12 doctors
            specialty = doctor['specialty']
            if specialty not in specialty_groups:
                specialty_groups[specialty] = []
            specialty_groups[specialty].append(doctor)
        
        doctor_number = 1
        for specialty, doctors in list(specialty_groups.items())[:6]:  # Show up to 6 specialties
            response += f"**🏥 {specialty}:**\n"
            for doctor in doctors[:3]:  # Max 3 doctors per specialty
                available_slots = len(doctor['available_slots'])
                match_indicator = "⭐ BEST MATCH" if doctor['score'] > 0 else "Available"
                
                response += f"""   **{doctor_number}. Dr. {doctor['name']}** ({match_indicator})
      📅 Available Slots: {available_slots} upcoming appointments
"""
                doctor_number += 1
            response += "\n"
        
        total_shown = min(doctor_number - 1, len(recommendations))
        response += f"**Showing {total_shown} of {len(recommendations)} available doctors**\n\n"
        
        response += """To see available time slots for any doctor, please type:
- The doctor's number (1, 2, 3, etc.)
- Or the doctor's name
- Or "show slots for Dr. [Name]"
- Or "show all doctors" to see complete list

Which doctor would you prefer?"""
        
        return response
    
    def _handle_doctor_selection(self, user_input: str) -> str:
        """Handle doctor selection and show available slots with Gemini AI enhancement"""
        user_lower = user_input.lower()
        
        # Handle "show all doctors" request
        if "show all" in user_lower or "all doctors" in user_lower:
            return self._show_all_doctors()
        
        # Get doctor recommendations again
        patient_info = self.conversation_context['patient_info']
        symptoms = patient_info.get('symptoms', '')
        medical_history = patient_info.get('medical_history', '')
        recommendations = self.recommend_doctors(symptoms, medical_history)
        
        selected_doctor = None
        
        # Try to match by number (now supporting up to 20 doctors)
        for i in range(1, min(21, len(recommendations) + 1)):
            if str(i) in user_input and len(recommendations) >= i:
                selected_doctor = recommendations[i-1]
                break
        
        # If no number match, try to match by name or use Gemini AI
        if not selected_doctor:
            # Try exact name matching first
            for doctor in recommendations:
                if doctor['name'].lower() in user_lower:
                    selected_doctor = doctor
                    break
            
            # If still no match, use Gemini AI for intelligent parsing
            if not selected_doctor:
                try:
                    ai_prompt = f"""
                    The user said: "{user_input}"
                    
                    Available doctors:
                    {[f"{i+1}. Dr. {doc['name']} ({doc['specialty']})" for i, doc in enumerate(recommendations[:10])]}
                    
                    Which doctor is the user trying to select? Respond with just the number (1-{min(10, len(recommendations))}) or "none" if unclear.
                    """
                    
                    ai_response = self.generate_ai_response(ai_prompt, {'step': 'doctor_parsing'})
                    
                    # Extract number from AI response
                    for i in range(1, min(11, len(recommendations) + 1)):
                        if str(i) in ai_response:
                            selected_doctor = recommendations[i-1]
                            break
                            
                except Exception as e:
                    print(f"AI doctor selection failed: {e}")
        
        if selected_doctor:
            self.conversation_context['selected_doctor'] = selected_doctor
            self.conversation_context['step'] = 'showing_slots'
            
            slots = selected_doctor['available_slots']
            if len(slots) == 0:
                return f"I apologize, but Dr. {selected_doctor['name']} has no available slots currently. Would you like to see another doctor?"
            
            response = f"""**Excellent choice!** Dr. {selected_doctor['name']} ({selected_doctor['specialty']})

**📅 Available Appointments:**

"""
            
            # Group slots by date
            slots_by_date = {}
            for _, slot in slots.iterrows():
                date = slot['date']
                if date not in slots_by_date:
                    slots_by_date[date] = []
                slots_by_date[date].append(slot['time'])
            
            slot_number = 1
            for date, times in list(slots_by_date.items())[:5]:  # Show next 5 days
                response += f"**{date}:**\n"
                for time in times[:4]:  # Show up to 4 slots per day
                    response += f"   {slot_number}. {time}\n"
                    slot_number += 1
                response += "\n"
            
            response += """To book an appointment, please type the number of your preferred time slot.

For example: "1" or "I'd like slot 3"

Which time works best for you?"""
            
            return response
        else:
            # Use Gemini AI to provide helpful suggestions
            try:
                ai_suggestion = self.generate_ai_response(
                    f"The user said '{user_input}' when trying to select a doctor. Provide a helpful, brief response guiding them to make a clear selection.",
                    {'step': 'doctor_selection_help'}
                )
                return f"{ai_suggestion}\n\nPlease type a doctor number (1, 2, 3, etc.) or doctor's name, or say 'show all doctors' to see the complete list."
            except:
                return "I didn't understand which doctor you'd prefer. Please type a doctor number (1, 2, 3, etc.), the doctor's name, or 'show all doctors' to see the complete list."
    
    def _show_all_doctors(self) -> str:
        """Show all available doctors organized by specialty"""
        try:
            all_doctors = self.get_available_doctors()
            
            if len(all_doctors) == 0:
                return "I apologize, but no doctors are currently available. Please contact our office directly."
            
            # Group doctors by specialty
            specialty_groups = {}
            for _, doctor in all_doctors.iterrows():
                specialty = doctor['specialty']
                if specialty not in specialty_groups:
                    specialty_groups[specialty] = []
                specialty_groups[specialty].append(doctor)
            
            response = f"**🏥 All Available Doctors ({len(all_doctors)} total):**\n\n"
            
            doctor_number = 1
            for specialty, doctors in specialty_groups.items():
                response += f"**🩺 {specialty} ({len(doctors)} doctors):**\n"
                for doctor in doctors:
                    # Get available slots count
                    try:
                        slots = self.get_available_slots(doctor['doctor_id'])
                        available_slots = len(slots)
                    except:
                        available_slots = "Unknown"
                    
                    response += f"   **{doctor_number}. Dr. {doctor['doctor_name']}**\n"
                    response += f"      📅 Available Slots: {available_slots}\n"
                    doctor_number += 1
                response += "\n"
            
            response += """To select a doctor, please type:
- The doctor's number (1, 2, 3, etc.)
- Or the doctor's name (e.g., "Dr. Smith")
- Or ask for recommendations: "recommend doctor for [your symptoms]"

Which doctor would you prefer?"""
            
            return response
            
        except Exception as e:
            print(f"Error showing all doctors: {e}")
            return "I encountered an error retrieving the doctor list. Please try again or contact our office directly."
    
    def _handle_slot_selection(self, user_input: str) -> str:
        """Handle appointment slot selection and booking"""
        try:
            # Extract slot number
            slot_num = None
            for word in user_input.split():
                if word.isdigit():
                    slot_num = int(word)
                    break
            
            if slot_num is None:
                return "Please specify which time slot you'd like by typing the number (e.g., '1', '2', '3'):"
            
            # Get selected doctor and available slots
            selected_doctor = self.conversation_context.get('selected_doctor')
            if not selected_doctor:
                return "I seem to have lost track of your doctor selection. Let me show you the doctors again."
            
            slots = selected_doctor['available_slots']
            
            if slot_num < 1 or slot_num > len(slots):
                return f"Please choose a slot number between 1 and {len(slots)}:"
            
            # Get the selected slot
            selected_slot = slots.iloc[slot_num - 1]
            
            # Book the appointment
            patient_info = self.conversation_context['patient_info']
            patient_id = patient_info.get('patient_id')
            is_new_patient = patient_info.get('is_new_patient', False)
            
            # Debug: Check if patient_id is valid
            if patient_id is None:
                print(f"❌ Error: Patient ID is None. Patient info: {patient_info}")
                # For new patients without ID, try to save them now
                if is_new_patient:
                    try:
                        print("🔄 Attempting to save new patient to database...")
                        patient_id = self.add_new_patient(patient_info)
                        self.conversation_context['patient_info']['patient_id'] = patient_id
                        print(f"✅ Patient saved successfully with ID: {patient_id}")
                    except Exception as e:
                        print(f"❌ Failed to save patient: {e}")
                        return "❌ Sorry, there was an error saving your information. Please start over."
                else:
                    return "❌ Sorry, there was an error with your patient information. Please start over."
            
            appointment_id, duration = self.book_appointment_slot(
                patient_id=str(patient_id),
                doctor_id=selected_doctor['doctor_id'],
                date=selected_slot['date'],
                time=selected_slot['time'],
                is_new_patient=is_new_patient
            )
            
            # 1. EXCEL EXPORT - Export appointment details
            excel_file = self.export_appointment_to_excel(appointment_id)
            
            # 2. APPOINTMENT CONFIRMATION - Send email and SMS
            confirmation_result = self.send_appointment_confirmation(appointment_id)
            
            # 3. FORM DISTRIBUTION - Send intake forms (only after confirmation)
            from form_distribution_system import FormDistributionSystem
            form_manager = FormDistributionSystem()
            forms_result = None
            if is_new_patient:
                forms_sent = form_manager.distribute_intake_forms(str(patient_id), appointment_id)
                forms_result = forms_sent
                self.conversation_context['form_sent'] = forms_sent
            
            # 4. REMINDER SYSTEM - Schedule 3 automated reminders
            from automated_reminder_system import AutomatedReminderSystem
            reminder_system = AutomatedReminderSystem()
            reminder_appointment_data = {
                'appointment_id': appointment_id,
                'patient_id': str(patient_id),
                'appointment_date': selected_slot['date'],
                'appointment_time': selected_slot['time']
            }
            
            # Debug: Print the data being sent to reminder system
            print(f"📋 DEBUG: Reminder data: {reminder_appointment_data}")
            
            reminders_scheduled = reminder_system.schedule_appointment_reminders(reminder_appointment_data)
            
            # Reset conversation
            self.conversation_context['step'] = 'greeting'
            
            # Build comprehensive confirmation message
            confirmation_msg = ""
            if confirmation_result:
                if confirmation_result.get('email') and confirmation_result.get('sms'):
                    confirmation_msg = "✅ Confirmation sent via email and SMS"
                elif confirmation_result.get('email'):
                    confirmation_msg = "✅ Confirmation sent via email"
                elif confirmation_result.get('sms'):
                    confirmation_msg = "✅ Confirmation sent via SMS"
                else:
                    confirmation_msg = "⚠️ Confirmation may have failed to send"
            
            forms_msg = ""
            if is_new_patient and forms_result:
                forms_msg = "\n✅ Patient intake forms emailed with pre-visit instructions"
            elif is_new_patient:
                forms_msg = "\n⚠️ Intake forms will be sent separately"
            
            excel_msg = ""
            if excel_file:
                excel_msg = f"\n✅ Appointment details exported to Excel: {excel_file}"
            
            reminders_msg = ""
            if reminders_scheduled:
                reminders_msg = "\n✅ 3 automated reminders scheduled (3 days, 1 day, 2 hours before)"
            
            return f"""🎉 **Appointment Successfully Booked & Confirmed!**

**Appointment Details:**
- 👨‍⚕️ Doctor: Dr. {selected_doctor['name']}
- 🏥 Specialty: {selected_doctor['specialty']}  
- 📅 Date: {selected_slot['date']}
- ⏰ Time: {selected_slot['time']}
- ⏱️ Duration: {duration} minutes
- 🆔 Appointment ID: {appointment_id}
- 📍 Location: {patient_info.get('preferred_location', 'Main Office')}

**✅ AUTOMATED SYSTEMS ACTIVATED:**
{confirmation_msg}{forms_msg}{excel_msg}{reminders_msg}

**📋 REMINDER SCHEDULE:**
1. **3 Days Before:** General appointment reminder
2. **1 Day Before:** Form completion check + visit confirmation  
3. **2 Hours Before:** Final confirmation or cancellation request

**Insurance Information Confirmed:**
- Carrier: {self.conversation_context.get('insurance_info', {}).get('carrier', 'Not provided')}
- Member ID: {self.conversation_context.get('insurance_info', {}).get('member_id', 'Not provided')}

**Before Your Visit:**
- Arrive 15 minutes early for check-in  
- Bring valid ID and insurance card
- Complete intake forms (emailed to you)
- List current medications
- Review pre-visit instructions

**📞 Contact Us:** (555) 123-4567 for any questions or changes

**🧪 Test Reminder System:**
To test the reminder system, go to Admin Panel → Reminder System → Test Reminder System in the Streamlit app.

Is there anything else I can help you with today?"""
            
        except Exception as e:
            print(f"Error booking appointment: {e}")
            return "I encountered an error while booking your appointment. Please try again or contact our office directly."
    
    def _handle_general_query(self, user_input: str) -> str:
        """Handle general queries using enhanced Gemini AI with edge case handling"""
        try:
            # Enhanced context for better AI responses
            current_step = self.conversation_context.get('step', 'greeting')
            patient_info = self.conversation_context.get('patient_info', {})
            
            # Special edge case handling
            user_lower = user_input.lower()
            
            # Handle doctor-related queries
            if any(word in user_lower for word in ['doctor', 'physician', 'specialist', 'dr.']):
                if any(word in user_lower for word in ['all', 'list', 'show', 'available']):
                    return self._show_all_doctors()
                elif any(word in user_lower for word in ['recommend', 'suggest', 'best']):
                    if 'symptoms' in patient_info:
                        return self._show_doctor_recommendations()
                    else:
                        return "I'd be happy to recommend doctors! First, could you tell me about your symptoms or health concerns?"
            
            # Handle appointment-related queries
            if any(word in user_lower for word in ['appointment', 'schedule', 'book', 'time', 'slot']):
                if current_step == 'greeting':
                    return "I'd be happy to help you schedule an appointment! Let's start with your full name."
                elif 'selected_doctor' in self.conversation_context:
                    return "You've selected a doctor. Please choose from the available time slots I showed you earlier."
                elif 'patient_info' in self.conversation_context and self.conversation_context['patient_info']:
                    return self._show_doctor_recommendations()
            
            # Handle form-related queries
            if any(word in user_lower for word in ['form', 'intake', 'paperwork', 'fill']):
                return """Our patient intake forms will be automatically emailed to you after your appointment is confirmed. 
The forms include:
- Medical history questionnaire
- Current medications list
- Insurance information verification
- Symptom assessment

You can also access forms online at: http://localhost:8503"""
            
            # Use enhanced AI prompt with context
            enhanced_prompt = f"""
            You are a medical appointment scheduling assistant at MediCare Allergy & Wellness Center.
            
            Current conversation step: {current_step}
            Patient information collected: {json.dumps(patient_info, indent=2) if patient_info else 'None'}
            
            Context:
            - We have 28+ doctors across 11 specialties
            - New patients get 60-minute appointments, returning patients get 30-minute
            - We offer automated reminders and online intake forms
            - Our system can handle complex scheduling requests
            
            User input: "{user_input}"
            
            Provide a helpful, professional response that:
            1. Addresses their query directly
            2. Guides them toward scheduling if appropriate
            3. Mentions relevant services
            4. Keeps response under 150 words
            5. Maintains a friendly, medical office tone
            
            If they're asking about something unclear, ask clarifying questions.
            If they seem frustrated, acknowledge their concern and offer assistance.
            """
            
            response = self.generate_ai_response(enhanced_prompt, self.conversation_context)
            
            # Add helpful suggestions for common edge cases
            if any(word in user_lower for word in ['help', 'confused', 'don\'t understand', 'stuck']):
                response += "\n\n**Quick Options:**\n- Say 'schedule appointment' to start booking\n- Say 'show all doctors' to see our full roster\n- Say 'help with forms' for intake information"
            
            return response
            
        except Exception as e:
            print(f"Error in general query handling: {e}")
            return """I apologize for the confusion. Let me help you get back on track:

**Available Options:**
- **Schedule an appointment**: Just say "I need an appointment"
- **See all doctors**: Say "show all doctors" 
- **Get help**: Say "I need help"
- **Start over**: Say "restart" or "begin again"

What would you like to do?"""
    
    def _handle_test_reminder_request(self, user_input: str) -> str:
        """Handle test reminder requests"""
        try:
            # Get the most recent appointment
            conn = self.get_db_connection()
            query = """
                SELECT a.appointment_id, a.patient_id, p.first_name, p.last_name
                FROM appointments a
                JOIN patients p ON a.patient_id = p.patient_id
                ORDER BY a.created_at DESC
                LIMIT 1
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if len(df) > 0:
                appointment = df.iloc[0]
                appointment_id = appointment['appointment_id']
                
                # Send test reminder
                from automated_reminder_system import AutomatedReminderSystem
                reminder_system = AutomatedReminderSystem()
                
                result = reminder_system.test_send_reminder_now(appointment_id, 'initial')
                
                if result:
                    return f"""✅ **Test Reminder Sent Successfully!**

**Details:**
- Appointment ID: {appointment_id}
- Patient: {appointment['first_name']} {appointment['last_name']}
- Reminder Type: Initial (3-day reminder)

The test reminder has been sent via email and SMS. Check your email/phone to confirm receipt!

**Note:** This was a test of the reminder system. The actual reminders will be sent automatically at the scheduled times.

Would you like to test a different reminder type? Available options:
- Type 'test follow up 1' for 1-day reminder
- Type 'test follow up 2' for 2-hour reminder"""
                else:
                    return "❌ Test reminder failed to send. Please check the logs for more details."
            else:
                return "❌ No appointments found to test reminders with. Please book an appointment first."
                
        except Exception as e:
            return f"❌ Error testing reminder system: {str(e)}"

if __name__ == "__main__":
    agent = EnhancedMedicalAgent()
    print("Enhanced Medical Agent with Google Gemini AI initialized successfully!")
    
    # Test conversation flow
    print("\n--- Test Conversation ---")
    response = agent.process_conversation("Hello, I'd like to schedule an appointment")
    print(f"Agent: {response}")
    
    print("\n--- Test with Name ---")
    response = agent.process_conversation("My name is John Smith")
    print(f"Agent: {response}")
    
    print("\n--- Test New Patient Flow ---")
    agent.conversation_context = {
        'patient_info': {},
        'appointment_details': {},
        'step': 'greeting',
        'conversation_history': []
    }
    
    response = agent.process_conversation("Hi, I need an appointment")
    print(f"Agent: {response}")
    
    response = agent.process_conversation("Alice Johnson")
    print(f"Agent: {response}")
    
    response = agent.process_conversation("alice.johnson@email.com")
    print(f"Agent: {response}")
    
    response = agent.process_conversation("555-123-4567")
    print(f"Agent: {response}")
    
    response = agent.process_conversation("I have seasonal allergies and breathing problems")
    print(f"Agent: {response}")
    
    response = agent.process_conversation("No significant medical history")
    print(f"Agent: {response}")
    
    print("\n=== Enhanced Medical Agent Test Complete ===")

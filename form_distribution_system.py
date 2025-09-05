import sqlite3
import pandas as pd
from datetime import datetime
import os
from communication import CommunicationManager
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

class FormDistributionSystem:
    def __init__(self, db_path="data/medical_scheduler.db"):
        self.db_path = db_path
        self.comm_manager = CommunicationManager()
        self.forms_directory = "forms/"
        
        # Ensure forms directory exists
        os.makedirs(self.forms_directory, exist_ok=True)
        
    def distribute_intake_forms(self, patient_id, appointment_id):
        """Email patient intake forms after appointment confirmation"""
        
        # Get patient information
        conn = sqlite3.connect(self.db_path)
        patient_query = "SELECT * FROM patients WHERE patient_id = ?"
        patient_df = pd.read_sql_query(patient_query, conn, params=[patient_id])
        
        if len(patient_df) == 0:
            print(f"❌ Patient {patient_id} not found")
            return False
            
        patient = patient_df.iloc[0]
        
        # Get appointment information
        appt_query = """
            SELECT a.*, d.doctor_name, d.specialty 
            FROM appointments a 
            JOIN doctors d ON a.doctor_id = d.doctor_id 
            WHERE a.appointment_id = ?
        """
        appt_df = pd.read_sql_query(appt_query, conn, params=[appointment_id])
        
        if len(appt_df) == 0:
            print(f"❌ Appointment {appointment_id} not found")
            conn.close()
            return False
            
        appointment = appt_df.iloc[0]
        
        try:
            # Record form distribution in database (no need to create HTML file)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO patient_forms (patient_id, appointment_id, form_type, form_status, sent_date)
                VALUES (?, ?, 'intake', 'sent', ?)
            """, (patient_id, appointment_id, datetime.now()))
            
            form_id = cursor.lastrowid
            conn.commit()
            
            # Send the form URL via email
            result = self.send_intake_forms_email(patient, appointment, form_id)
            
            if result:
                print(f"✅ Intake forms sent successfully to {patient['email']}")
                return True
            else:
                print(f"❌ Failed to send intake forms to {patient['email']}")
                return False
                
        except Exception as e:
            print(f"❌ Error distributing forms: {e}")
            return False
        finally:
            conn.close()
            
    def create_patient_intake_form(self, patient, appointment):
        """Create a personalized patient intake form"""
        form_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Patient Intake Form - MediCare Allergy & Wellness Center</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 3px solid #2c5aa0;
        }}
        .header h1 {{
            color: #2c5aa0;
            margin: 0;
            font-size: 28px;
        }}
        .patient-info {{
            background-color: #e8f4fd;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section h2 {{
            color: #2c5aa0;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .form-group {{
            margin-bottom: 20px;
        }}
        .form-group label {{
            display: block;
            font-weight: bold;
            margin-bottom: 5px;
            color: #333;
        }}
        .form-group input, .form-group textarea, .form-group select {{
            width: 100%;
            padding: 10px;
            border: 2px solid #e9ecef;
            border-radius: 5px;
            font-size: 16px;
            box-sizing: border-box;
        }}
        .form-group textarea {{
            height: 100px;
            resize: vertical;
        }}
        .checkbox-group {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .checkbox-item {{
            display: flex;
            align-items: center;
            margin-right: 20px;
            margin-bottom: 10px;
        }}
        .checkbox-item input[type="checkbox"] {{
            width: auto;
            margin-right: 8px;
        }}
        .important-note {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
        }}
        .emergency {{
            background-color: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 15px;
            margin: 20px 0;
        }}
        .submit-section {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e9ecef;
        }}
        .submit-btn {{
            background-color: #2c5aa0;
            color: white;
            padding: 15px 40px;
            border: none;
            border-radius: 5px;
            font-size: 18px;
            cursor: pointer;
            margin: 10px;
        }}
        .submit-btn:hover {{
            background-color: #1e3f73;
        }}
        .required {{
            color: #dc3545;
        }}
        .two-column {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        @media (max-width: 600px) {{
            .two-column {{
                grid-template-columns: 1fr;
            }}
            .container {{
                padding: 15px;
                margin: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏥 Patient Intake Form</h1>
            <h3>MediCare Allergy & Wellness Center</h3>
        </div>
        
        <div class="patient-info">
            <h3>📅 Appointment Information</h3>
            <p><strong>Patient:</strong> {patient['first_name']} {patient['last_name']}</p>
            <p><strong>Appointment Date:</strong> {appointment['appointment_date']}</p>
            <p><strong>Appointment Time:</strong> {appointment['appointment_time']}</p>
            <p><strong>Doctor:</strong> Dr. {appointment['doctor_name']}</p>
            <p><strong>Specialty:</strong> {appointment['specialty']}</p>
            <p><strong>Duration:</strong> {appointment['duration']} minutes</p>
        </div>
        
        <form id="intakeForm" action="#" method="post">
            
            <!-- Personal Information -->
            <div class="section">
                <h2>📋 Personal Information</h2>
                <div class="two-column">
                    <div class="form-group">
                        <label for="firstName">First Name <span class="required">*</span></label>
                        <input type="text" id="firstName" name="firstName" value="{patient['first_name']}" required>
                    </div>
                    <div class="form-group">
                        <label for="lastName">Last Name <span class="required">*</span></label>
                        <input type="text" id="lastName" name="lastName" value="{patient['last_name']}" required>
                    </div>
                </div>
                
                <div class="two-column">
                    <div class="form-group">
                        <label for="dob">Date of Birth <span class="required">*</span></label>
                        <input type="date" id="dob" name="dob" value="{patient.get('date_of_birth', '')}" required>
                    </div>
                    <div class="form-group">
                        <label for="gender">Gender <span class="required">*</span></label>
                        <select id="gender" name="gender" required>
                            <option value="">Select Gender</option>
                            <option value="male">Male</option>
                            <option value="female">Female</option>
                            <option value="other">Other</option>
                            <option value="prefer-not-to-say">Prefer not to say</option>
                        </select>
                    </div>
                </div>
                
                <div class="two-column">
                    <div class="form-group">
                        <label for="phone">Phone Number <span class="required">*</span></label>
                        <input type="tel" id="phone" name="phone" value="{patient.get('phone', '')}" required>
                    </div>
                    <div class="form-group">
                        <label for="email">Email Address <span class="required">*</span></label>
                        <input type="email" id="email" name="email" value="{patient.get('email', '')}" required>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="address">Home Address</label>
                    <textarea id="address" name="address" placeholder="Street Address, City, State, ZIP Code">{patient.get('address', '')}</textarea>
                </div>
            </div>
            
            <!-- Emergency Contact -->
            <div class="section">
                <h2>🚨 Emergency Contact Information</h2>
                <div class="two-column">
                    <div class="form-group">
                        <label for="emergencyName">Emergency Contact Name <span class="required">*</span></label>
                        <input type="text" id="emergencyName" name="emergencyName" value="{patient.get('emergency_contact_name', '')}" required>
                    </div>
                    <div class="form-group">
                        <label for="emergencyPhone">Emergency Contact Phone <span class="required">*</span></label>
                        <input type="tel" id="emergencyPhone" name="emergencyPhone" value="{patient.get('emergency_contact_phone', '')}" required>
                    </div>
                </div>
                <div class="form-group">
                    <label for="emergencyRelationship">Relationship <span class="required">*</span></label>
                    <select id="emergencyRelationship" name="emergencyRelationship" required>
                        <option value="">Select Relationship</option>
                        <option value="spouse">Spouse</option>
                        <option value="parent">Parent</option>
                        <option value="child">Child</option>
                        <option value="sibling">Sibling</option>
                        <option value="friend">Friend</option>
                        <option value="other">Other</option>
                    </select>
                </div>
            </div>
            
            <!-- Insurance Information -->
            <div class="section">
                <h2>🏥 Insurance Information</h2>
                <div class="two-column">
                    <div class="form-group">
                        <label for="insuranceCompany">Insurance Company <span class="required">*</span></label>
                        <input type="text" id="insuranceCompany" name="insuranceCompany" value="{patient.get('insurance_company', '')}" required>
                    </div>
                    <div class="form-group">
                        <label for="memberId">Member ID <span class="required">*</span></label>
                        <input type="text" id="memberId" name="memberId" value="{patient.get('member_id', '')}" required>
                    </div>
                </div>
                <div class="form-group">
                    <label for="groupNumber">Group Number</label>
                    <input type="text" id="groupNumber" name="groupNumber" value="{patient.get('group_number', '')}">
                </div>
            </div>
            
            <!-- Chief Complaint -->
            <div class="section">
                <h2>🩺 Chief Complaint & Symptoms</h2>
                <div class="form-group">
                    <label for="chiefComplaint">What is the main reason for your visit today? <span class="required">*</span></label>
                    <textarea id="chiefComplaint" name="chiefComplaint" placeholder="Please describe your symptoms, concerns, or reason for visit" required>{patient.get('symptoms', '')}</textarea>
                </div>
                
                <div class="form-group">
                    <label for="symptomDuration">How long have you had these symptoms?</label>
                    <select id="symptomDuration" name="symptomDuration">
                        <option value="">Select Duration</option>
                        <option value="less-than-week">Less than a week</option>
                        <option value="1-2-weeks">1-2 weeks</option>
                        <option value="1-month">About a month</option>
                        <option value="2-6-months">2-6 months</option>
                        <option value="6-months-plus">More than 6 months</option>
                        <option value="years">Several years</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="painLevel">Current pain/discomfort level (0-10 scale)</label>
                    <select id="painLevel" name="painLevel">
                        <option value="">Select Level</option>
                        <option value="0">0 - No pain</option>
                        <option value="1">1 - Minimal</option>
                        <option value="2">2 - Mild</option>
                        <option value="3">3 - Mild</option>
                        <option value="4">4 - Moderate</option>
                        <option value="5">5 - Moderate</option>
                        <option value="6">6 - Moderately severe</option>
                        <option value="7">7 - Severe</option>
                        <option value="8">8 - Very severe</option>
                        <option value="9">9 - Nearly unbearable</option>
                        <option value="10">10 - Unbearable</option>
                    </select>
                </div>
            </div>
            
            <!-- Medical History -->
            <div class="section">
                <h2>📖 Medical History</h2>
                <div class="form-group">
                    <label for="currentMedications">Current Medications <span class="required">*</span></label>
                    <textarea id="currentMedications" name="currentMedications" placeholder="List all medications, vitamins, and supplements you are currently taking (include dosages if known)">{patient.get('medical_history', '')}</textarea>
                </div>
                
                <div class="form-group">
                    <label for="allergies">Known Allergies <span class="required">*</span></label>
                    <textarea id="allergies" name="allergies" placeholder="List any known allergies to medications, foods, environmental factors, etc. If none, write 'None'">{patient.get('allergies', '')}</textarea>
                </div>
                
                <div class="form-group">
                    <label>Previous Medical Conditions (check all that apply):</label>
                    <div class="checkbox-group">
                        <div class="checkbox-item">
                            <input type="checkbox" id="diabetes" name="conditions[]" value="diabetes">
                            <label for="diabetes">Diabetes</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="hypertension" name="conditions[]" value="hypertension">
                            <label for="hypertension">High Blood Pressure</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="heart-disease" name="conditions[]" value="heart-disease">
                            <label for="heart-disease">Heart Disease</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="asthma" name="conditions[]" value="asthma">
                            <label for="asthma">Asthma</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="cancer" name="conditions[]" value="cancer">
                            <label for="cancer">Cancer</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="kidney-disease" name="conditions[]" value="kidney-disease">
                            <label for="kidney-disease">Kidney Disease</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="liver-disease" name="conditions[]" value="liver-disease">
                            <label for="liver-disease">Liver Disease</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="depression" name="conditions[]" value="depression">
                            <label for="depression">Depression/Anxiety</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="other-condition" name="conditions[]" value="other">
                            <label for="other-condition">Other (specify below)</label>
                        </div>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="otherConditions">Other Medical Conditions or Important Medical History:</label>
                    <textarea id="otherConditions" name="otherConditions" placeholder="Please describe any other medical conditions, surgeries, or important medical history"></textarea>
                </div>
            </div>
            
            <!-- Family History -->
            <div class="section">
                <h2>👨‍👩‍👧‍👦 Family Medical History</h2>
                <div class="form-group">
                    <label for="familyHistory">Significant Family Medical History</label>
                    <textarea id="familyHistory" name="familyHistory" placeholder="Please list any significant medical conditions in your immediate family (parents, siblings, children)"></textarea>
                </div>
            </div>
            
            <!-- Social History -->
            <div class="section">
                <h2>🏠 Social History</h2>
                <div class="two-column">
                    <div class="form-group">
                        <label for="smoking">Smoking Status</label>
                        <select id="smoking" name="smoking">
                            <option value="">Select Status</option>
                            <option value="never">Never smoked</option>
                            <option value="former">Former smoker</option>
                            <option value="current">Current smoker</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="alcohol">Alcohol Use</label>
                        <select id="alcohol" name="alcohol">
                            <option value="">Select Usage</option>
                            <option value="none">None</option>
                            <option value="occasional">Occasional (1-2 drinks/week)</option>
                            <option value="moderate">Moderate (3-7 drinks/week)</option>
                            <option value="heavy">Heavy (8+ drinks/week)</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="exercise">Exercise Habits</label>
                    <select id="exercise" name="exercise">
                        <option value="">Select Level</option>
                        <option value="sedentary">Sedentary (little to no exercise)</option>
                        <option value="light">Light (1-2 times/week)</option>
                        <option value="moderate">Moderate (3-4 times/week)</option>
                        <option value="active">Very Active (5+ times/week)</option>
                    </select>
                </div>
            </div>
            
            <!-- Important Notes -->
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
            
            <div class="emergency">
                <h4>🚨 If This is a Medical Emergency</h4>
                <p>If you are experiencing a medical emergency, please call 911 immediately or go to your nearest emergency room. Do not wait for your appointment.</p>
            </div>
            
            <!-- Consent and Signature -->
            <div class="section">
                <h2>✍️ Consent and Acknowledgment</h2>
                <div class="checkbox-item">
                    <input type="checkbox" id="consent1" name="consent1" required>
                    <label for="consent1">I certify that the information provided is accurate to the best of my knowledge <span class="required">*</span></label>
                </div>
                <div class="checkbox-item">
                    <input type="checkbox" id="consent2" name="consent2" required>
                    <label for="consent2">I understand that I should arrive 15 minutes early for my appointment <span class="required">*</span></label>
                </div>
                <div class="checkbox-item">
                    <input type="checkbox" id="consent3" name="consent3" required>
                    <label for="consent3">I have read and understand the pre-visit instructions above <span class="required">*</span></label>
                </div>
                <div class="checkbox-item">
                    <input type="checkbox" id="consent4" name="consent4">
                    <label for="consent4">I consent to receive appointment reminders via email and SMS</label>
                </div>
                
                <div class="two-column" style="margin-top: 20px;">
                    <div class="form-group">
                        <label for="signature">Digital Signature (type your full name) <span class="required">*</span></label>
                        <input type="text" id="signature" name="signature" placeholder="Type your full name as digital signature" required>
                    </div>
                    <div class="form-group">
                        <label for="signatureDate">Date <span class="required">*</span></label>
                        <input type="date" id="signatureDate" name="signatureDate" value="{datetime.now().strftime('%Y-%m-%d')}" required>
                    </div>
                </div>
            </div>
            
            <!-- Submit Section -->
            <div class="submit-section">
                <h3>📧 How to Submit Your Form</h3>
                <p>You can submit this form in one of the following ways:</p>
                
                <button type="button" class="submit-btn" onclick="printForm()">🖨️ Print & Bring to Appointment</button>
                <button type="button" class="submit-btn" onclick="saveAsPDF()">📄 Save as PDF</button>
                
                <p style="margin-top: 20px;">
                    <strong>Or email completed form to:</strong> 
                    <a href="mailto:intake@medicare-wellness.com">intake@medicare-wellness.com</a>
                </p>
                
                <p><small>
                    <strong>Questions?</strong> Call us at (555) 123-4567<br>
                    We're here to help Monday-Friday, 8 AM - 5 PM
                </small></p>
            </div>
        </form>
    </div>
    
    <script>
        function printForm() {{
            window.print();
        }}
        
        function saveAsPDF() {{
            // Simple implementation - in real app, would use proper PDF generation
            alert('Please use your browser\\'s "Print" function and select "Save as PDF" as the destination.');
            window.print();
        }}
        
        // Auto-save form data to localStorage
        function saveFormData() {{
            const formData = new FormData(document.getElementById('intakeForm'));
            const data = {{}};
            for (let [key, value] of formData.entries()) {{
                data[key] = value;
            }}
            localStorage.setItem('intakeFormData', JSON.stringify(data));
        }}
        
        // Auto-save every 30 seconds
        setInterval(saveFormData, 30000);
        
        // Save on form change
        document.getElementById('intakeForm').addEventListener('change', saveFormData);
    </script>
</body>
</html>
"""
        
        # Save form to file
        form_filename = f"patient_intake_form_{patient['patient_id']}_{appointment['appointment_id']}.html"
        form_path = os.path.join(self.forms_directory, form_filename)
        
        with open(form_path, 'w', encoding='utf-8') as f:
            f.write(form_content)
            
        return form_path
        
    def send_intake_forms_email(self, patient, appointment, form_id):
        """Send intake forms via email with Streamlit form URL"""
        subject = "📋 Patient Intake Forms - Complete Online Before Your Visit"
        
        # Generate Streamlit form URL with patient ID
        streamlit_form_url = f"http://localhost:8503?patient_id={patient['patient_id']}"
        
        email_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c5aa0;">📋 Complete Your Intake Forms Online</h2>
                
                <p>Dear {patient['first_name']} {patient['last_name']},</p>
                
                <p>Thank you for scheduling your appointment with us! To ensure we provide you with the best possible care, please complete your intake forms online <strong>before your visit</strong>.</p>
                
                <div style="background-color: #e8f4fd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #2c5aa0;">📅 Your Appointment Details:</h3>
                    <p><strong>Date:</strong> {appointment['appointment_date']}</p>
                    <p><strong>Time:</strong> {appointment['appointment_time']}</p>
                    <p><strong>Doctor:</strong> Dr. {appointment['doctor_name']}</p>
                    <p><strong>Specialty:</strong> {appointment['specialty']}</p>
                    <p><strong>Duration:</strong> {appointment['duration']} minutes</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0; padding: 20px; background-color: #d4edda; border-radius: 10px;">
                    <h3 style="color: #155724; margin-top: 0;">🖱️ Click to Complete Your Forms Online</h3>
                    <a href="{streamlit_form_url}" 
                       style="background-color: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; font-size: 18px; font-weight: bold;">
                        📝 Complete Intake Forms
                    </a>
                    <p style="margin: 15px 0 0 0; font-size: 14px; color: #6c757d;">
                        Your personalized form is ready and pre-filled with your appointment details
                    </p>
                </div>
                
                <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
                    <h4 style="margin-top: 0;">📝 How to Complete Your Forms:</h4>
                    <ol>
                        <li><strong>Click the button above</strong> to access your personalized form</li>
                        <li><strong>Fill out all required fields</strong> (marked with red asterisks)</li>
                        <li><strong>Submit the form online</strong> - it will be automatically saved to your record</li>
                        <li><strong>You'll receive a confirmation</strong> when your form is successfully submitted</li>
                    </ol>
                    <p><strong>⚠️ Important:</strong> Complete your forms at least 24 hours before your appointment to avoid delays.</p>
                </div>
                
                <div style="background-color: #d4edda; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #28a745;">
                    <h4 style="margin-top: 0;">⚠️ Important Pre-Visit Instructions:</h4>
                    <p><strong>For Allergy Testing:</strong> If allergy testing is planned, you MUST stop these medications 7 days before your appointment:</p>
                    <ul>
                        <li>All antihistamines (Claritin, Zyrtec, Allegra, Benadryl)</li>
                        <li>Cold medications containing antihistamines</li>
                        <li>Sleep aids like Tylenol PM</li>
                    </ul>
                    <p><strong>You MAY continue:</strong> Nasal sprays, asthma inhalers, prescription medications</p>
                </div>
                
                <div style="background-color: #f8d7da; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #dc3545;">
                    <h4 style="margin-top: 0;">🚨 What to Bring:</h4>
                    <ul>
                        <li>✅ Insurance card and photo ID</li>
                        <li>✅ List of current medications</li>
                        <li>✅ Any previous test results or medical records</li>
                        <li>✅ Payment method for copay</li>
                    </ul>
                    <p><strong>Note:</strong> Your intake forms will be completed online, so no need to bring printed forms!</p>
                </div>
                
                <div style="background-color: #e2e3e5; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h4 style="margin-top: 0;">🔗 Form Access Information:</h4>
                    <p><strong>Direct Link:</strong> <a href="{streamlit_form_url}">{streamlit_form_url}</a></p>
                    <p><strong>Form Tracking ID:</strong> #{form_id}</p>
                    <p><strong>Patient ID:</strong> {patient['patient_id']}</p>
                    <p style="font-size: 12px; color: #6c757d;"><em>Keep this information for your records</em></p>
                </div>
                
                <p style="text-align: center; margin: 30px 0;">
                    <strong>Questions about the forms or technical issues?</strong><br>
                    <a href="tel:555-123-4567" style="background-color: #2c5aa0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">📞 Call Us: (555) 123-4567</a>
                </p>
                
                <p>We look forward to seeing you soon!</p>
                
                <p>Best regards,<br>
                <strong>MediCare Allergy & Wellness Center Team</strong></p>
                
                <hr>
                <p style="font-size: 12px; color: #666;">
                    This email contains important medical information. Please keep it confidential.
                </p>
            </div>
                MediCare Allergy & Wellness Center<br>
                📍 123 Medical Plaza, Health City<br>
                📞 (555) 123-4567</p>
            </div>
        </body>
        </html>
        """
        
        # Send email without attachment (using Streamlit URL instead)
        try:
            result = self.comm_manager.send_email(
                to_email=patient['email'],
                subject=subject,
                body=email_body
            )
            
            return result[0] if isinstance(result, tuple) else result
            
        except Exception as e:
            print(f"❌ Error sending intake forms email: {e}")
            return False
            
    def check_form_completion_status(self, patient_id, appointment_id):
        """Check if patient has completed their intake forms"""
        conn = sqlite3.connect(self.db_path)
        
        query = """
            SELECT form_status, sent_date, completed_date
            FROM patient_forms 
            WHERE patient_id = ? AND appointment_id = ? AND form_type = 'intake'
            ORDER BY sent_date DESC
            LIMIT 1
        """
        
        result = pd.read_sql_query(query, conn, params=[patient_id, appointment_id])
        conn.close()
        
        if len(result) > 0:
            form = result.iloc[0]
            return {
                'sent': True,
                'status': form['form_status'],
                'sent_date': form['sent_date'],
                'completed_date': form['completed_date']
            }
        else:
            return {
                'sent': False,
                'status': 'not_sent',
                'sent_date': None,
                'completed_date': None
            }
            
    def mark_form_completed(self, patient_id, appointment_id, form_data=None):
        """Mark a form as completed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE patient_forms 
            SET form_status = 'completed', completed_date = ?, form_data = ?
            WHERE patient_id = ? AND appointment_id = ? AND form_type = 'intake'
        """, (datetime.now(), form_data, patient_id, appointment_id))
        
        conn.commit()
        conn.close()
        
        return cursor.rowcount > 0

if __name__ == "__main__":
    # Test the form distribution system
    print("🧪 Testing Form Distribution System...")
    
    form_system = FormDistributionSystem()
    
    # Test with a sample patient and appointment
    # This would be called after an appointment is booked
    # form_system.distribute_intake_forms("patient_id", "appointment_id")
    
    print("✅ Form Distribution System initialized successfully!")

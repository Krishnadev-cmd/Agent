import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from twilio.rest import Client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class CommunicationManager:
    def __init__(self):
        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        
        # Twilio configuration
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        # Initialize Twilio client
        if self.twilio_account_sid and self.twilio_auth_token:
            self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
        
    def send_email(self, to_email: str, subject: str, body: str, attachment_path: str = None):
        """Send email with optional attachment"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body to email
            msg.attach(MIMEText(body, 'html'))
            
            # Add attachment if provided
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(attachment_path)}'
                )
                msg.attach(part)
            
            # Connect to server and send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            text = msg.as_string()
            server.sendmail(self.email_user, to_email, text)
            server.quit()
            
            return True, "Email sent successfully"
            
        except Exception as e:
            return False, f"Error sending email: {str(e)}"
    
    def send_email_with_attachment(self, to_email: str, subject: str, body: str, attachment_path: str):
        """Send email with attachment"""
        return self.send_email(to_email, subject, body, attachment_path)
    
    def send_sms(self, to_phone: str, message: str):
        """Send SMS using Twilio"""
        try:
            if not self.twilio_client:
                return False, "Twilio not configured"
            
            message = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone_number,
                to=to_phone
            )
            
            return True, f"SMS sent successfully. SID: {message.sid}"
            
        except Exception as e:
            return False, f"Error sending SMS: {str(e)}"
    
    def send_appointment_confirmation(self, patient_info: dict, appointment_info: dict):
        """Send appointment confirmation via email and SMS"""
        # Create confirmation email
        subject = "Appointment Confirmation - MediCare Allergy & Wellness Center"
        
        email_body = f"""
        <html>
        <body>
            <h2>Appointment Confirmation</h2>
            <p>Dear {patient_info['first_name']} {patient_info['last_name']},</p>
            
            <p>Your appointment has been successfully scheduled:</p>
            
            <div style="background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>Appointment Details:</h3>
                <p><strong>Date:</strong> {appointment_info['date']}</p>
                <p><strong>Time:</strong> {appointment_info['time']}</p>
                <p><strong>Doctor:</strong> {appointment_info['doctor_name']}</p>
                <p><strong>Duration:</strong> {appointment_info['duration']} minutes</p>
                <p><strong>Type:</strong> {appointment_info['appointment_type']}</p>
            </div>
            
            <h3>Important Pre-Visit Instructions:</h3>
            <p>If allergy testing is planned, you MUST stop the following medications 7 days before your appointment:</p>
            <ul>
                <li>All antihistamines (Claritin, Zyrtec, Allegra, Benadryl)</li>
                <li>Cold medications containing antihistamines</li>
                <li>Sleep aids like Tylenol PM</li>
            </ul>
            <p>You MAY continue: Nasal sprays (Flonase, Nasacort), asthma inhalers, and prescription medications</p>
            
            <h3>What to Bring:</h3>
            <ul>
                <li>Insurance cards and photo ID</li>
                <li>List of current medications</li>
                <li>Completed intake forms (will be sent separately)</li>
            </ul>
            
            <p>Please arrive 15 minutes early for your appointment.</p>
            
            <p>If you need to reschedule or have any questions, please call us at (555) 123-4567.</p>
            
            <p>Best regards,<br>
            MediCare Allergy & Wellness Center<br>
            456 Healthcare Boulevard, Suite 300</p>
        </body>
        </html>
        """
        
        # Send email
        email_result = self.send_email(patient_info['email'], subject, email_body)
        
        # Create SMS message
        sms_message = f"""
MediCare Allergy & Wellness - Appointment Confirmed

Date: {appointment_info['date']}
Time: {appointment_info['time']}
Doctor: {appointment_info['doctor_name']}

Please arrive 15 minutes early.
Call (555) 123-4567 for questions.
        """
        
        # Send SMS
        sms_result = self.send_sms(patient_info['phone'], sms_message)
        
        return {
            'email': email_result,
            'sms': sms_result
        }
    
    def send_intake_forms(self, patient_email: str, patient_name: str):
        """Send intake forms to patient"""
        subject = "Patient Intake Forms - MediCare Allergy & Wellness Center"
        
        email_body = f"""
        <html>
        <body>
            <h2>Patient Intake Forms</h2>
            <p>Dear {patient_name},</p>
            
            <p>Thank you for scheduling your appointment with MediCare Allergy & Wellness Center.</p>
            
            <p>Please complete the attached intake forms and submit them 24 hours before your appointment 
            or arrive 15 minutes early if completing at the office.</p>
            
            <h3>Required Forms:</h3>
            <ul>
                <li>New Patient Intake Form</li>
                <li>Medical History Form</li>
                <li>Insurance Information Form</li>
            </ul>
            
            <p>If you have any questions about the forms, please don't hesitate to contact us at 
            (555) 123-4567.</p>
            
            <p>We look forward to seeing you!</p>
            
            <p>Best regards,<br>
            MediCare Allergy & Wellness Center<br>
            456 Healthcare Boulevard, Suite 300</p>
        </body>
        </html>
        """
        
        # Note: In a real implementation, you would attach actual form files
        return self.send_email(patient_email, subject, email_body)
    
    def send_reminder(self, patient_info: dict, appointment_info: dict, reminder_type: str):
        """Send appointment reminders"""
        if reminder_type == "first":
            subject = "Appointment Reminder - Tomorrow"
            days_text = "tomorrow"
        elif reminder_type == "second":
            subject = "Appointment Reminder - Today"
            days_text = "today"
        else:
            subject = "Final Appointment Reminder"
            days_text = "in a few hours"
        
        email_body = f"""
        <html>
        <body>
            <h2>Appointment Reminder</h2>
            <p>Dear {patient_info['first_name']} {patient_info['last_name']},</p>
            
            <p>This is a reminder that you have an appointment {days_text}:</p>
            
            <div style="background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>Appointment Details:</h3>
                <p><strong>Date:</strong> {appointment_info['date']}</p>
                <p><strong>Time:</strong> {appointment_info['time']}</p>
                <p><strong>Doctor:</strong> {appointment_info['doctor_name']}</p>
            </div>
            
            <p>Please confirm your attendance by replying to this email or calling (555) 123-4567.</p>
            
            <p>If you need to cancel or reschedule, please let us know as soon as possible.</p>
            
            <p>Have you completed your intake forms? If not, please do so before your visit.</p>
            
            <p>Best regards,<br>
            MediCare Allergy & Wellness Center</p>
        </body>
        </html>
        """
        
        # Send email reminder
        email_result = self.send_email(patient_info['email'], subject, email_body)
        
        # Send SMS reminder
        sms_message = f"""
MediCare Reminder: Appointment {days_text}
Date: {appointment_info['date']}
Time: {appointment_info['time']}
Doctor: {appointment_info['doctor_name']}

Please confirm attendance. Call (555) 123-4567 if changes needed.
        """
        
        sms_result = self.send_sms(patient_info['phone'], sms_message)
        
        return {
            'email': email_result,
            'sms': sms_result
        }

if __name__ == "__main__":
    # Test communication
    comm = CommunicationManager()
    print("Communication Manager initialized successfully!")
    
    # Test data
    patient_info = {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@example.com',
        'phone': '+1234567890'
    }
    
    appointment_info = {
        'date': '2024-02-10',
        'time': '10:00',
        'doctor_name': 'Dr. Smith',
        'duration': 60,
        'appointment_type': 'New Patient'
    }
    
    # Test sending confirmation
    result = comm.send_appointment_confirmation(patient_info, appointment_info)
    print("Confirmation result:", result)

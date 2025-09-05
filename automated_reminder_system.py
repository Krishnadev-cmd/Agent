import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import schedule
import time
import threading
from communication import CommunicationManager
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

class AutomatedReminderSystem:
    def __init__(self, db_path="data/medical_scheduler.db"):
        self.db_path = db_path
        self.comm_manager = CommunicationManager()
        self.running = False
        
        # Debug flag for testing
        self.debug_mode = True
        
    def log_debug(self, message):
        """Debug logging for troubleshooting"""
        if self.debug_mode:
            print(f"[{datetime.now()}] REMINDER DEBUG: {message}")
            
    def test_email_config(self):
        """Test email configuration"""
        try:
            self.log_debug("Testing email configuration...")
            
            # Check if email credentials are set
            if not self.comm_manager.email_user:
                self.log_debug("ERROR: EMAIL_USER not set in environment")
                return False
                
            if not self.comm_manager.email_password:
                self.log_debug("ERROR: EMAIL_PASSWORD not set in environment")
                return False
                
            self.log_debug(f"Email user: {self.comm_manager.email_user}")
            self.log_debug(f"SMTP server: {self.comm_manager.smtp_server}:{self.comm_manager.smtp_port}")
            
            return True
            
        except Exception as e:
            self.log_debug(f"Email configuration error: {e}")
            return False
            
    def start_scheduler(self):
        """Start the automated reminder scheduler"""
        # Schedule checks every hour
        schedule.every().hour.do(self.check_and_send_reminders)
        
        self.running = True
        print("🤖 Automated Reminder System Started!")
        print("⏰ Checking for reminders every hour...")
        
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.running = False
        schedule.clear()
        print("⏹️ Automated Reminder System Stopped!")
        
    def check_and_send_reminders(self):
        """Check for pending reminders and send them"""
        current_time = datetime.now()
        
        conn = sqlite3.connect(self.db_path)
        
        # Get pending reminders that are due (including overdue ones for testing)
        query = """
            SELECT r.*, p.first_name, p.last_name, p.email, p.phone,
                   a.appointment_date, a.appointment_time, d.doctor_name, d.specialty
            FROM reminders r
            JOIN patients p ON r.patient_id = p.patient_id
            JOIN appointments a ON r.appointment_id = a.appointment_id
            JOIN doctors d ON a.doctor_id = d.doctor_id
            WHERE r.status = 'pending' 
            ORDER BY r.scheduled_time
        """
        
        reminders_df = pd.read_sql_query(query, conn)
        
        print(f"📋 Found {len(reminders_df)} pending reminders to send...")
        
        for _, reminder in reminders_df.iterrows():
            try:
                if reminder['reminder_type'] == 'initial':
                    self.send_initial_reminder(reminder)
                elif reminder['reminder_type'] == 'follow_up_1':
                    self.send_follow_up_1_reminder(reminder)
                elif reminder['reminder_type'] == 'follow_up_2':
                    self.send_follow_up_2_reminder(reminder)
                
                # Mark as sent
                self.mark_reminder_sent(reminder['reminder_id'])
                print(f"✅ Sent {reminder['reminder_type']} reminder to {reminder['first_name']} {reminder['last_name']}")
                
            except Exception as e:
                print(f"❌ Error sending reminder {reminder['reminder_id']}: {e}")
                self.mark_reminder_failed(reminder['reminder_id'], str(e))
        
        conn.close()
        
    def send_initial_reminder(self, reminder):
        """Send initial reminder (3 days before)"""
        try:
            self.log_debug(f"Sending initial reminder for appointment {reminder.get('appointment_id', 'N/A')}")
            
            # Test email configuration first
            if not self.test_email_config():
                self.log_debug("Email configuration test failed")
                return False
            
            subject = "🏥 Appointment Reminder - MediCare Allergy & Wellness Center"
            
            email_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c5aa0;">Appointment Reminder</h2>
                    
                    <p>Dear {reminder['first_name']} {reminder['last_name']},</p>
                    
                    <p>This is a friendly reminder about your upcoming appointment at MediCare Allergy & Wellness Center.</p>
                    
                    <div style="background-color: #e8f4fd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #2c5aa0;">📅 Appointment Details:</h3>
                        <p><strong>Date:</strong> {reminder['appointment_date']}</p>
                        <p><strong>Time:</strong> {reminder['appointment_time']}</p>
                        <p><strong>Doctor:</strong> Dr. {reminder['doctor_name']}</p>
                        <p><strong>Specialty:</strong> {reminder['specialty']}</p>
                    </div>
                    
                    <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <h4 style="margin-top: 0; color: #856404;">📋 Please Remember:</h4>
                        <ul>
                            <li>Arrive 15 minutes early for check-in</li>
                            <li>Bring your insurance card and ID</li>
                            <li>Complete any required forms</li>
                            <li>Bring a list of current medications</li>
                        </ul>
                    </div>
                    
                    <p>If you need to reschedule or cancel, please call us at <strong>(555) 123-4567</strong></p>
                    
                    <p style="margin-top: 30px; color: #666; font-size: 0.9em;">
                        Thank you for choosing MediCare!<br>
                        <em>This is an automated reminder. Please do not reply to this email.</em>
                    </p>
                </div>
            </body>
            </html>
            """
            
            self.log_debug(f"Sending email to: {reminder['email']}")
            success = self.comm_manager.send_email(reminder['email'], subject, email_body)
            
            if success:
                self.log_debug(f"Initial reminder email sent successfully to {reminder['email']}")
            else:
                self.log_debug(f"Failed to send initial reminder email to {reminder['email']}")
                
            return success
            
        except Exception as e:
            self.log_debug(f"Error sending initial reminder: {e}")
            return False

    def send_follow_up_1_reminder(self, reminder):
        """Send follow-up reminder 1 (1 day before) - Ask about forms and confirmation"""
        try:
            subject = "🔔 Tomorrow's Appointment - MediCare (Action Required)"
            
            email_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #e67e22;">Your Appointment is Tomorrow! 📅</h2>
                    
                    <p>Dear {reminder['first_name']} {reminder['last_name']},</p>
                    
                    <p>This is a friendly reminder that your appointment is scheduled for <strong>tomorrow</strong>.</p>
                    
                    <div style="background-color: #e8f4fd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #2c5aa0;">📅 Appointment Details:</h3>
                        <p><strong>Date:</strong> {reminder['appointment_date']} (Tomorrow)</p>
                        <p><strong>Time:</strong> {reminder['appointment_time']}</p>
                        <p><strong>Doctor:</strong> Dr. {reminder['doctor_name']}</p>
                        <p><strong>Specialty:</strong> {reminder['specialty']}</p>
                    </div>
                    
                    <div style="background-color: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h4 style="margin-top: 0; color: #856404;">❓ Action Required - Please Confirm:</h4>
                        <ol>
                            <li><strong>Have you filled the forms?</strong><br>
                                <small>Please complete your intake forms if you haven't already</small>
                            </li>
                            <li><strong>Is your visit confirmed or not?</strong><br>
                                <small>If not, please mention the reason for cancellation by calling (555) 123-4567</small>
                            </li>
                        </ol>
                        <p style="margin-top: 15px; font-weight: bold; color: #d9534f;">
                            📞 Please call us at (555) 123-4567 if you need to cancel or have any concerns.
                        </p>
                    </div>
                    
                    <div style="background-color: #d4edda; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <h4 style="margin-top: 0; color: #155724;">✅ Final Reminders:</h4>
                        <ul>
                            <li>Arrive 15 minutes early</li>
                            <li>Bring insurance card and photo ID</li>
                            <li>Complete forms if not already done</li>
                            <li>Bring current medication list</li>
                        </ul>
                    </div>
                    
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="tel:555-123-4567" style="background-color: #e67e22; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">📞 Call if Changes Needed</a>
                    </p>
                    
                    <p style="margin-top: 30px; color: #666; font-size: 0.9em;">
                        Thank you for choosing MediCare!<br>
                        <em>This is an automated reminder. Please call us for any changes.</em>
                    </p>
                </div>
            </body>
            </html>
            """
            
            success = self.comm_manager.send_email(reminder['email'], subject, email_body)
            return success
            
        except Exception as e:
            print(f"Error sending follow-up 1 reminder: {e}")
            return False

    def send_follow_up_2_reminder(self, reminder):
        """Send follow-up reminder 2 (2 hours before) - Final confirmation"""
        try:
            subject = "⏰ Final Reminder - Your Appointment is in 2 Hours!"
            
            email_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #dc3545;">⏰ Your Appointment is in 2 Hours!</h2>
                    
                    <p>Dear {reminder['first_name']} {reminder['last_name']},</p>
                    
                    <p>This is your final reminder - your appointment is scheduled in approximately <strong>2 hours</strong>.</p>
                    
                    <div style="background-color: #f8d7da; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #dc3545;">
                        <h3 style="margin-top: 0; color: #721c24;">🚨 URGENT - Appointment Details:</h3>
                        <p><strong>TODAY at {reminder['appointment_time']}</strong></p>
                        <p><strong>Doctor:</strong> Dr. {reminder['doctor_name']}</p>
                        <p><strong>Location:</strong> MediCare Allergy & Wellness Center</p>
                    </div>
                    
                    <div style="background-color: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h4 style="margin-top: 0; color: #856404;">🔍 Action Required - Final Confirmation:</h4>
                        <ol>
                            <li><strong>Have you filled the forms?</strong><br>
                                <small>⚠️ Incomplete forms may delay your appointment</small>
                            </li>
                            <li><strong>Is your visit confirmed or not?</strong><br>
                                <small>If not, please mention the reason for cancellation by calling NOW: (555) 123-4567</small>
                            </li>
                        </ol>
                        <p style="margin-top: 15px; font-weight: bold; color: #d9534f;">
                            📞 URGENT: Call (555) 123-4567 immediately if you need to cancel or have concerns.
                        </p>
                    </div>
                    
                    <div style="background-color: #d1ecf1; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <h4 style="margin-top: 0; color: #0c5460;">📍 What to Bring:</h4>
                        <ul>
                            <li>✅ Photo ID</li>
                            <li>✅ Insurance card</li>
                            <li>✅ Completed forms</li>
                            <li>✅ Current medications list</li>
                            <li>✅ Payment method for copay</li>
                        </ul>
                    </div>
                    
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="tel:555-123-4567" style="background-color: #dc3545; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">🚨 URGENT: Call if Canceling</a>
                    </p>
                    
                    <p style="margin-top: 30px; color: #666; font-size: 0.9em; text-align: center;">
                        <strong>MediCare Allergy & Wellness Center</strong><br>
                        📍 123 Medical Plaza, Health City<br>
                        📞 (555) 123-4567<br>
                        <em>See you soon!</em>
                    </p>
                </div>
            </body>
            </html>
            """
            
            success = self.comm_manager.send_email(reminder['email'], subject, email_body)
            
            # Also send SMS for urgent reminder
            if reminder.get('phone'):
                sms_message = f"🚨 REMINDER: Your appointment with Dr. {reminder['doctor_name']} is in 2 HOURS at {reminder['appointment_time']}. Please call (555) 123-4567 if you need to cancel. - MediCare"
                self.send_sms_reminder(reminder, sms_message)
            
            return success
            
        except Exception as e:
            print(f"Error sending follow-up 2 reminder: {e}")
            return False

    def send_sms_reminder(self, appointment_data, custom_message=None):
        """Send SMS reminder using Twilio"""
        try:
            if not appointment_data.get('phone'):
                self.log_debug("No phone number provided for SMS")
                return False
                
            if custom_message:
                message = custom_message
            else:
                message = f"Reminder: You have an appointment with Dr. {appointment_data['doctor_name']} on {appointment_data['appointment_date']} at {appointment_data['appointment_time']}. Call (555) 123-4567 for changes. - MediCare"
            
            success = self.comm_manager.send_sms(appointment_data['phone'], message)
            
            if success:
                self.log_debug(f"SMS reminder sent successfully to {appointment_data['phone']}")
            else:
                self.log_debug(f"Failed to send SMS reminder to {appointment_data['phone']}")
                
            return success
            
        except Exception as e:
            self.log_debug(f"Error sending SMS reminder: {e}")
            return False

    def mark_reminder_sent(self, reminder_id):
        """Mark reminder as sent in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE reminders 
                SET status = 'sent', sent_time = ? 
                WHERE reminder_id = ?
            """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), reminder_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error marking reminder as sent: {e}")

    def mark_reminder_failed(self, reminder_id, error_message):
        """Mark reminder as failed in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE reminders 
                SET status = 'failed', sent_time = ?, response = ? 
                WHERE reminder_id = ?
            """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), error_message, reminder_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error marking reminder as failed: {e}")

    def schedule_appointment_reminders(self, appointment_data):
        """Schedule all three reminders for an appointment"""
        try:
            # Try different time formats
            time_str = f"{appointment_data['appointment_date']} {appointment_data['appointment_time']}"
            
            # Try 12-hour format first, then 24-hour format
            try:
                appointment_datetime = datetime.strptime(time_str, "%Y-%m-%d %I:%M %p")
            except ValueError:
                try:
                    appointment_datetime = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                except ValueError:
                    # If both fail, log the exact format received
                    self.log_debug(f"Failed to parse datetime: '{time_str}'. Expected formats: 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD HH:MM AM/PM'")
                    return False
            
            # Calculate reminder times - TESTING MODE: Immediate scheduling
            current_time = datetime.now()
            
            # For testing: Schedule reminders just a few seconds apart (SUPER FAST)
            initial_reminder_time = current_time + timedelta(seconds=5)      # 5 seconds from now
            followup_1_reminder_time = current_time + timedelta(seconds=15)  # 15 seconds from now  
            followup_2_reminder_time = current_time + timedelta(seconds=25)  # 25 seconds from now
            
            self.log_debug(f"TEST MODE: Scheduling reminders at:")
            self.log_debug(f"  - Initial: {initial_reminder_time} (10 seconds - regular reminder)")
            self.log_debug(f"  - Follow-up 1: {followup_1_reminder_time} (30 seconds - with form/confirmation checks)")
            self.log_debug(f"  - Follow-up 2: {followup_2_reminder_time} (60 seconds - with form/confirmation checks)")
            
            # Production timings (commented out for testing):
            # initial_reminder_time = appointment_datetime - timedelta(days=3)
            # followup_1_reminder_time = appointment_datetime - timedelta(days=1)
            # followup_2_reminder_time = appointment_datetime - timedelta(hours=2)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            reminders = [
                ('initial', initial_reminder_time),
                ('follow_up_1', followup_1_reminder_time),
                ('follow_up_2', followup_2_reminder_time)
            ]
            
            for reminder_type, reminder_time in reminders:
                cursor.execute("""
                    INSERT INTO reminders (
                        appointment_id, patient_id, reminder_type, 
                        reminder_method, scheduled_time, status
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    appointment_data['appointment_id'],
                    appointment_data['patient_id'],
                    reminder_type,
                    'email',
                    reminder_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'pending'
                ))
            
            conn.commit()
            conn.close()
            
            self.log_debug(f"Scheduled 3 reminders for appointment {appointment_data['appointment_id']}")
            return True
            
        except Exception as e:
            self.log_debug(f"Error scheduling reminders: {e}")
            return False

    def send_pending_reminders_now(self):
        """Send all pending reminders immediately for testing"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all pending reminders
            cursor.execute("""
                SELECT r.*, p.first_name, p.last_name, p.email, p.phone,
                       a.appointment_date, a.appointment_time, d.doctor_name
                FROM reminders r
                JOIN appointments a ON r.appointment_id = a.appointment_id
                JOIN patients p ON r.patient_id = p.patient_id
                JOIN doctors d ON a.doctor_id = d.doctor_id
                WHERE r.status = 'pending'
                ORDER BY r.scheduled_time
            """)
            
            reminders = cursor.fetchall()
            
            if not reminders:
                self.log_debug("No pending reminders found")
                return False
            
            self.log_debug(f"Found {len(reminders)} pending reminders")
            
            for reminder in reminders:
                reminder_id = reminder[0]
                appointment_id = reminder[1]
                patient_id = reminder[2]
                reminder_type = reminder[3]
                
                # Extract patient info
                patient_info = {
                    'first_name': reminder[10],
                    'last_name': reminder[11],
                    'email': reminder[12],
                    'phone': reminder[13]
                }
                
                # Extract appointment info
                appointment_info = {
                    'date': reminder[14],
                    'time': reminder[15],
                    'doctor_name': reminder[16]
                }
                
                self.log_debug(f"Sending {reminder_type} reminder to {patient_info['first_name']} {patient_info['last_name']}")
                
                # Send reminder
                result = self.comm_manager.send_reminder(patient_info, appointment_info, reminder_type)
                
                if result.get('email') or result.get('sms'):
                    # Mark as sent
                    cursor.execute("""
                        UPDATE reminders 
                        SET status = 'sent', sent_time = ? 
                        WHERE reminder_id = ?
                    """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), reminder_id))
                    
                    self.log_debug(f"✅ {reminder_type} reminder sent successfully")
                else:
                    self.log_debug(f"❌ Failed to send {reminder_type} reminder")
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            self.log_debug(f"Error sending pending reminders: {e}")
            return False

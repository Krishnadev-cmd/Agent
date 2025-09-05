import sqlite3
import pandas as pd
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="data/medical_scheduler.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database with required tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create patients table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                patient_id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                date_of_birth TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                phone TEXT,
                email TEXT,
                address TEXT,
                city TEXT,
                state TEXT,
                zip_code TEXT,
                insurance_company TEXT,
                member_id TEXT,
                group_number TEXT,
                is_new_patient BOOLEAN DEFAULT 1,
                allergies TEXT,
                symptoms TEXT,
                medical_history TEXT,
                preferred_location TEXT,
                emergency_contact_name TEXT,
                emergency_contact_phone TEXT,
                emergency_contact_relationship TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add missing columns to existing patients table if they don't exist
        self._add_missing_columns(cursor)
        
        # Create insurance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS insurance_info (
                insurance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT,
                carrier TEXT,
                member_id TEXT,
                group_number TEXT,
                policy_number TEXT,
                effective_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
            )
        """)
        
        # Create reminders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                reminder_id INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_id INTEGER,
                patient_id TEXT,
                reminder_type TEXT, -- 'initial', 'follow_up_1', 'follow_up_2'
                reminder_method TEXT, -- 'email', 'sms', 'both'
                message TEXT,
                scheduled_time TIMESTAMP,
                sent_time TIMESTAMP,
                status TEXT DEFAULT 'pending', -- 'pending', 'sent', 'failed'
                response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (appointment_id) REFERENCES appointments (appointment_id),
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
            )
        """)
        
        # Create patient_forms table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patient_forms (
                form_id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT,
                appointment_id INTEGER,
                form_type TEXT, -- 'intake', 'medical_history', 'consent'
                form_status TEXT DEFAULT 'sent', -- 'sent', 'completed', 'pending'
                sent_date TIMESTAMP,
                completed_date TIMESTAMP,
                form_data TEXT, -- JSON string of form responses
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id),
                FOREIGN KEY (appointment_id) REFERENCES appointments (appointment_id)
            )
        """)
        
        # Create doctors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                doctor_id TEXT PRIMARY KEY,
                doctor_name TEXT NOT NULL,
                specialty TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create doctor schedules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS doctor_schedules (
                schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                doctor_id TEXT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                is_available BOOLEAN DEFAULT 1,
                appointment_type TEXT DEFAULT 'Available',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
            )
        """)
        
        # Create appointments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT,
                doctor_id TEXT,
                appointment_date TEXT NOT NULL,
                appointment_time TEXT NOT NULL,
                duration INTEGER DEFAULT 30,
                appointment_type TEXT,
                status TEXT DEFAULT 'scheduled',
                chief_complaint TEXT,
                symptoms TEXT,
                current_medications TEXT,
                medical_history TEXT,
                forms_sent BOOLEAN DEFAULT 0,
                forms_completed BOOLEAN DEFAULT 0,
                reminder_count INTEGER DEFAULT 0,
                last_reminder_sent TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
                FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
            )
        """)
        
        # Create reminders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                reminder_id INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_id INTEGER,
                patient_id TEXT,
                reminder_type TEXT, -- 'initial', 'follow_up_1', 'follow_up_2'
                reminder_method TEXT, -- 'email', 'sms', 'both'
                message TEXT,
                scheduled_time TIMESTAMP,
                sent_time TIMESTAMP,
                status TEXT DEFAULT 'pending', -- 'pending', 'sent', 'failed'
                response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (appointment_id) REFERENCES appointments (appointment_id),
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
            )
        """)
        
        conn.commit()
        conn.close()
        print("Database initialized successfully")
    
    def _add_missing_columns(self, cursor):
        """Add missing columns to existing tables"""
        
        # Update patients table
        cursor.execute("PRAGMA table_info(patients)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        # Define new columns to add to patients table
        new_columns = [
            ('age', 'INTEGER'),
            ('symptoms', 'TEXT'),
            ('medical_history', 'TEXT'),
            ('preferred_location', 'TEXT'),
            ('is_new_patient', 'INTEGER DEFAULT 0'),
            ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        ]
        
        # Add missing columns to patients table
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE patients ADD COLUMN {column_name} {column_type}")
                    print(f"Added column '{column_name}' to patients table")
                except Exception as e:
                    print(f"Error adding column '{column_name}': {e}")
        
        # Update appointments table
        cursor.execute("PRAGMA table_info(appointments)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        # Add created_at to appointments if missing
        if 'created_at' not in existing_columns:
            try:
                cursor.execute("ALTER TABLE appointments ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                print("Added column 'created_at' to appointments table")
            except Exception as e:
                print(f"Error adding created_at to appointments: {e}")
        
    def load_sample_data(self):
        """Load sample data from CSV and Excel files"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Load patients data
            if os.path.exists('data/patients.csv'):
                patients_df = pd.read_csv('data/patients.csv')
                patients_df.to_sql('patients', conn, if_exists='replace', index=False)
                print(f"Loaded {len(patients_df)} patients")
            
            # Load doctor schedule data
            if os.path.exists('data/doctor_schedules.xlsx'):
                schedule_df = pd.read_excel('data/doctor_schedules.xlsx')
                
                # Extract unique doctors
                doctors_df = schedule_df[['doctor_id', 'doctor_name', 'specialty']].drop_duplicates()
                doctors_df.to_sql('doctors', conn, if_exists='replace', index=False)
                print(f"Loaded {len(doctors_df)} doctors")
                
                # Load schedules
                schedule_df = schedule_df[['doctor_id', 'date', 'time', 'is_available', 'appointment_type']]
                schedule_df.to_sql('doctor_schedules', conn, if_exists='replace', index=False)
                print(f"Loaded {len(schedule_df)} schedule slots")
                
        except Exception as e:
            print(f"Error loading sample data: {e}")
        finally:
            conn.close()
            
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
        
    def search_patient(self, first_name=None, last_name=None, phone=None, email=None):
        """Search for patient by various criteria"""
        conn = self.get_connection()
        query = "SELECT * FROM patients WHERE 1=1"
        params = []
        
        if first_name:
            query += " AND LOWER(first_name) LIKE LOWER(?)"
            params.append(f"%{first_name}%")
        if last_name:
            query += " AND LOWER(last_name) LIKE LOWER(?)"
            params.append(f"%{last_name}%")
        if phone:
            query += " AND phone LIKE ?"
            params.append(f"%{phone}%")
        if email:
            query += " AND LOWER(email) LIKE LOWER(?)"
            params.append(f"%{email}%")
            
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
        
    def get_available_slots(self, doctor_id=None, date=None):
        """Get available appointment slots"""
        conn = self.get_connection()
        query = """
            SELECT ds.*, d.doctor_name, d.specialty 
            FROM doctor_schedules ds 
            JOIN doctors d ON ds.doctor_id = d.doctor_id 
            WHERE ds.is_available = 1
        """
        params = []
        
        if doctor_id:
            query += " AND ds.doctor_id = ?"
            params.append(doctor_id)
        if date:
            query += " AND ds.date = ?"
            params.append(date)
            
        query += " ORDER BY ds.date, ds.time"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
        
    def book_appointment(self, patient_id, doctor_id, date, time, duration=30, appointment_type="Regular"):
        """Book an appointment"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Insert appointment
            cursor.execute("""
                INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, 
                                        duration, appointment_type, status)
                VALUES (?, ?, ?, ?, ?, ?, 'scheduled')
            """, (patient_id, doctor_id, date, time, duration, appointment_type))
            
            appointment_id = cursor.lastrowid
            
            # Mark slot as unavailable
            cursor.execute("""
                UPDATE doctor_schedules 
                SET is_available = 0, appointment_type = 'Booked' 
                WHERE doctor_id = ? AND date = ? AND time = ?
            """, (doctor_id, date, time))
            
            conn.commit()
            print(f"Appointment booked successfully with ID: {appointment_id}")
            return appointment_id
            
        except Exception as e:
            conn.rollback()
            print(f"Error booking appointment: {e}")
            return None
        finally:
            conn.close()

if __name__ == "__main__":
    db_manager = DatabaseManager()
    db_manager.load_sample_data()
    print("Database setup complete!")

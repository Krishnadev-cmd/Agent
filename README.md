# MediCare AI Scheduling Agent with Calendly-Style Integration

## Project Overview

A comprehensive AI-powered medical appointment scheduling system for MediCare Allergy & Wellness Center featuring **Calendly-style calendar integration**, automated patient booking, and streamlined clinic operations with professional documentation capabilities.

## 🚀 Quick Setup

### 1. Clone and Install
```bash
git clone https://github.com/Krishnadev-cmd/Agent.git
cd Agent
pip install -r requirements.txt
```

### 2. Environment Setup
```bash
# Copy the environment template
cp .env.template .env

# Edit .env with your actual credentials
# - Email settings for sending reminders
# - Twilio settings for SMS (optional)
```

### 3. Run the Applications
```bash
# Main scheduling app (port 8502)
streamlit run app.py

# Patient intake forms (port 8501)
python run_form_app.py

# Generate technical documentation
python generate_compact_technical_document.py
```

### 4. Access the System
- **Main App**: http://localhost:8502
- **Patient Forms**: http://localhost:8501?patient_id=<PATIENT_ID>
- **Calendar Export**: Available in `/exports` folder

## 🏥 Features

### ✨ **NEW: Calendly-Style Calendar Integration**
- ✅ **Interactive Calendar View** - Visual appointment slot selection
- ✅ **Real-Time Availability** - Live conflict detection and buffer time management
- ✅ **Multi-Doctor Coordination** - Synchronized scheduling across 28 doctors in 11 specialties
- ✅ **Professional Excel Export** - Formatted calendar exports with appointment details
- ✅ **Automated Conflict Resolution** - Intelligent slot algorithms preventing double-booking
- ✅ **Buffer Time Management** - 15-minute intervals with automatic spacing

### Core Features (Production Ready)
- ✅ **Patient Greeting & Data Collection** - Collect name, DOB, doctor preferences, and location
- ✅ **Patient Lookup System** - Search EMR database for existing vs. new patients
- ✅ **Smart Scheduling Logic** - 60min slots for new patients, 30min for returning patients
- ✅ **Insurance Collection** - Capture carrier, member ID, and group information
- ✅ **Appointment Confirmation** - Export to Excel and send confirmations
- ✅ **Form Distribution** - Email patient intake forms after confirmation
- ✅ **Automated Reminder System** - 3-tier automated reminders via email and SMS
- ✅ **Technical Documentation** - Professional PDF documentation generation

### Technical Implementation
- **Framework**: LangChain + Google Gemini AI (1.5 Flash)
- **Frontend**: Streamlit web application with calendar integration
- **Database**: SQLite with ACID compliance and transaction management
- **Calendar System**: Custom CalendarIntegration class with Calendly-style functionality
- **Communication**: Email (SMTP) + SMS (Twilio) with retry mechanisms
- **Export**: Professional Excel and PDF report generation
- **Documentation**: Automated technical approach document generation

## 📁 Project Structure

```
agent/
├── app.py                          # Main Streamlit application
├── medical_agent_simple.py         # Core AI scheduling agent
├── calendar_integration.py         # 🆕 Calendly-style calendar system
├── database_manager.py             # Database operations
├── communication.py                # Email & SMS functionality
├── automated_reminder_system.py    # 3-tier reminder automation
├── form_distribution_system.py     # Patient form management
├── generate_compact_technical_document.py  # 🆕 Technical documentation generator
├── add_doctors.py                  # Doctor database management
├── generate_doctor_schedules.py    # Doctor schedule generation
├── patient_intake_form.py          # Patient intake form handler
├── run_form_app.py                 # Form application runner
├── .env                           # Environment variables
├── requirements.txt               # Python dependencies
├── FORM_SETUP_GUIDE.md           # Form configuration guide
├── IMPLEMENTATION_SUMMARY.md      # Implementation overview
├── Technical_Approach_Document_Compact_*.pdf  # 🆕 Generated technical docs
├── data/
│   ├── medical_scheduler.db       # SQLite database
│   ├── patients.csv              # Patient data
│   ├── doctor_schedules.xlsx     # Doctor availability schedules
│   └── appointment_confirmation_*.xlsx  # Individual appointment exports
├── exports/
│   ├── medical_calendar_export_*.xlsx   # 🆕 Calendar exports
│   └── patient_data_*.xlsx              # Patient data exports
├── forms/
│   └── patient_intake_form.html   # Patient intake form template
└── __pycache__/                   # Python cache files
```

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.8+
- Virtual environment capability
- Google Gemini API key
- Gmail account for SMTP
- Twilio account for SMS (optional)

### Installation

1. **Clone and Navigate**
   ```bash
   cd c:\Krishnadev\New_Projects\agent
   ```

2. **Environment Setup**
   ```bash
   # Virtual environment is already configured
   # Activate if needed: .\.venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**
   Configure the `.env` file with your credentials:
   ```env
   # AI Configuration
   GEMINI_API_KEY=your_gemini_api_key
   
   # Email Configuration
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   EMAIL_USER=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   
   # SMS Configuration (Optional)
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_token
   TWILIO_PHONE_NUMBER=your_twilio_phone
   ```

5. **Database Setup**
   ```bash
   python database_manager.py
   ```

6. **Generate Sample Data**
   ```bash
   python generate_data.py
   ```

### Running the Application

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

## 💻 Usage Guide

### For Patients
1. **Start Conversation**: Click on the chat interface
2. **Provide Information**: Share your name and basic details
3. **Select Doctor**: Choose from available specialists
4. **Pick Time Slot**: Select from available appointments
5. **Confirm Booking**: Review and confirm appointment details
6. **Complete Forms**: Fill out emailed intake forms

### For Staff (Admin Panel)
1. **View Analytics**: Monitor appointment metrics
2. **Manage Appointments**: View, reschedule, or cancel appointments
3. **Export Reports**: Generate Excel reports for review
4. **Send Reminders**: Manual reminder management
5. **System Status**: Monitor database and integrations

## 🔧 Core Components

### 1. AI Scheduling Agent
- **Location**: `medical_agent_simple.py`
- **Function**: Handles conversation flow and appointment logic
- **Features**: Patient lookup, slot availability, booking confirmation

### 2. 🆕 Calendar Integration System
- **Location**: `calendar_integration.py`
- **Function**: Calendly-style scheduling with real-time availability
- **Features**: 
  - Visual slot generation with 15-minute intervals
  - Multi-doctor coordination across 11 specialties
  - Automatic conflict detection and resolution
  - Professional Excel export with formatting
  - Buffer time management and scheduling optimization

### 3. Database Manager
- **Location**: `database_manager.py`
- **Function**: SQLite database operations with ACID compliance
- **Tables**: Patients, Doctors, Schedules, Appointments, Reminders
- **Features**: Transaction management, data validation, backup systems

### 4. Communication System
- **Location**: `communication.py`
- **Function**: Multi-channel email and SMS notifications
- **Features**: Confirmations, 3-tier reminders, form distribution, retry mechanisms

### 5. 🆕 Technical Documentation Generator
- **Location**: `generate_compact_technical_document.py`
- **Function**: Automated professional PDF documentation creation
- **Features**: Architecture overview, framework analysis, integration strategy, challenges & solutions

### 6. Streamlit Interface
- **Location**: `app.py`
- **Function**: Web-based user interface with calendar integration
- **Pages**: Chat, Analytics, Appointments, Admin Panel, Calendar View

## 📊 Database Schema

### Patients Table
```sql
- patient_id (VARCHAR, PRIMARY KEY)
- first_name, last_name (VARCHAR)
- date_of_birth (DATE)
- phone, email (VARCHAR)
- insurance_company, member_id (VARCHAR)
- is_new_patient (BOOLEAN)
- allergies (TEXT)
```

### Appointments Table
```sql
- appointment_id (INTEGER, PRIMARY KEY)
- patient_id, doctor_id (VARCHAR, FOREIGN KEY)
- appointment_date, appointment_time (DATE, TIME)
- duration (INTEGER) -- 30 or 60 minutes
- status (VARCHAR) -- scheduled, completed, cancelled
- forms_sent, forms_completed (BOOLEAN)
```

## 🎯 Business Logic

### Appointment Duration
- **New Patients**: 60 minutes (comprehensive evaluation)
- **Returning Patients**: 30 minutes (follow-up visit)

### 🆕 Calendar Scheduling Rules
- **Slot Intervals**: 15-minute increments for optimal scheduling flexibility
- **Buffer Time**: Automatic 15-minute buffers between appointments
- **Working Hours**: 8:00 AM - 6:00 PM, Monday through Saturday
- **Conflict Detection**: Real-time validation preventing double-booking
- **Multi-Doctor Support**: Simultaneous scheduling across 28 doctors in 11 specialties
- **Availability Window**: 14-day rolling availability for patient selection

### Reminder System
1. **First Reminder**: 24 hours before appointment (email + SMS)
2. **Second Reminder**: 4 hours before (with form completion check)
3. **Final Reminder**: 1 hour before (with confirmation request)

### Form Management
- Intake forms sent immediately after booking confirmation
- Pre-visit medication instructions included
- 24-hour submission deadline before appointment
- Automated follow-up for incomplete forms

### 🆕 Export and Documentation
- **Calendar Exports**: Professional Excel files with appointment details
- **Technical Documentation**: Automated PDF generation with project overview
- **Administrative Reports**: Patient data exports with analytics
- **Appointment Confirmations**: Individual Excel files per booking

## 📈 Analytics & Reporting

### Available Metrics
- Total patients (new vs. returning)
- Daily/weekly appointment counts
- Doctor utilization rates
- Form completion rates
- No-show tracking
- Insurance carrier distribution

### Export Capabilities
- Excel reports with patient details
- Appointment summaries
- Administrative overviews
- Reminder status tracking

## 🔒 Security & Privacy

### Data Protection
- Local SQLite database storage
- Environment variable protection for API keys
- No sensitive data in code repository

### Compliance Considerations
- HIPAA-compliant architecture ready
- Audit trail capabilities
- Secure communication channels

## 🚧 Future Enhancements

### Recently Completed ✅
- ✅ **Calendly-Style Calendar Integration** - Visual scheduling with real-time availability
- ✅ **Professional Excel Export** - Formatted calendar and appointment exports  
- ✅ **Technical Documentation** - Automated PDF generation with comprehensive details
- ✅ **Multi-Doctor Coordination** - 28 doctors across 11 specialties
- ✅ **Advanced Conflict Detection** - Real-time slot validation and buffer management

### Planned Features
- [ ] **External Calendar Integration** (Google Calendar, Outlook, iCal sync)
- [ ] **Patient Portal Access** with self-service capabilities
- [ ] **Advanced AI Conversation** with medical history analysis
- [ ] **Multi-language Support** for diverse patient populations
- [ ] **Mobile App Companion** for iOS and Android
- [ ] **Insurance Verification API** with real-time eligibility checks
- [ ] **Telehealth Integration** for virtual appointments
- [ ] **Waiting List Management** with automatic rebooking
- [ ] **Provider Dashboard** with analytics and insights

### Technical Improvements
- [ ] **PostgreSQL Migration** for production scalability
- [ ] **Redis Caching Layer** for performance optimization
- [ ] **RESTful API** with FastAPI and comprehensive documentation
- [ ] **Containerization** with Docker and Docker Compose
- [ ] **CI/CD Pipeline** with automated testing and deployment
- [ ] **Load Balancing** for high-availability architecture
- [ ] **Real-time Notifications** with WebSocket integration

## 🐛 Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure virtual environment is activated
.\.venv\Scripts\activate
pip install -r requirements.txt
```

**Database Connection Issues**
```bash
# Regenerate database
python database_manager.py
```

**Streamlit Port Conflicts**
```bash
# Use different port
streamlit run app.py --server.port 8502
```

**API Key Issues**
- Verify `.env` file configuration
- Check Google Cloud Console for Gemini API access
- Confirm Twilio credentials if using SMS

## � Calendar Integration Features

### Calendly-Style Functionality
The system now includes comprehensive calendar integration that rivals commercial scheduling platforms:

#### **Visual Slot Generation**
- **15-minute intervals** with intelligent buffer time management
- **Real-time availability** checking across all doctors and specialties
- **Conflict detection** preventing double-booking and scheduling conflicts
- **Multi-doctor coordination** supporting 28 doctors across 11 medical specialties

#### **Professional Export Capabilities**
- **Excel calendar exports** with professional formatting and styling
- **Individual appointment confirmations** with detailed patient and appointment information
- **Administrative reports** for clinic management and planning
- **Automated file naming** with timestamps for organization

#### **Technical Architecture**
- **Custom CalendarIntegration class** with optimized algorithms
- **Database integration** with ACID-compliant transactions
- **Thread-safe operations** supporting concurrent user access
- **Error handling** with comprehensive validation and rollback mechanisms

### Usage Examples

#### **Generate Calendar Export**
```python
from calendar_integration import CalendarIntegration

calendar = CalendarIntegration()
filename = calendar.export_calendar_to_excel()
print(f"Calendar exported to: {filename}")
```

#### **Check Available Slots**
```python
available_slots = calendar.get_available_slots(
    doctor_id="DOC001",
    start_date="2025-09-06",
    end_date="2025-09-20"
)
```

## �📝 Development Notes

### Code Quality
- Type hints throughout codebase
- Comprehensive error handling
- Modular architecture
- Documentation strings

### Testing Strategy
- Unit tests for core functions
- Integration tests for database operations
- UI tests for Streamlit components
- End-to-end workflow validation

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch
3. Implement changes with tests
4. Update documentation
5. Submit pull request

### Code Standards
- Follow PEP 8 style guidelines
- Use type hints
- Write descriptive commit messages
- Include unit tests for new features

## 📞 Support

### Technical Support
- **Email**: support@medicare-scheduling.com
- **Documentation**: See `/docs` folder
- **Issues**: GitHub Issues tracker

### Business Contact
- **Clinic**: MediCare Allergy & Wellness Center
- **Phone**: (555) 123-4567
- **Address**: 456 Healthcare Boulevard, Suite 300

## 📄 License

This project is proprietary software developed for MediCare Allergy & Wellness Center.

---

**Built with ❤️ for MediCare Allergy & Wellness Center**

*Reducing no-shows, improving patient experience, and streamlining healthcare operations through AI-powered scheduling.*

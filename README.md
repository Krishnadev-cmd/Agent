# MediCare AI Scheduling Agent

## Project Overview

A comprehensive AI-powered medical appointment scheduling system for MediCare Allergy & Wellness Center that automates patient booking, reduces no-shows, and streamlines clinic operations.

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
```

### 4. Access the System
- **Main App**: http://localhost:8502
- **Patient Forms**: http://localhost:8501?patient_id=<PATIENT_ID>

## 🏥 Features

### Core Features (MVP-1)
- ✅ **Patient Greeting & Data Collection** - Collect name, DOB, doctor preferences, and location
- ✅ **Patient Lookup System** - Search EMR database for existing vs. new patients
- ✅ **Smart Scheduling Logic** - 60min slots for new patients, 30min for returning patients
- ✅ **Calendar Integration** - Show available appointment slots
- ✅ **Insurance Collection** - Capture carrier, member ID, and group information
- ✅ **Appointment Confirmation** - Export to Excel and send confirmations
- ✅ **Form Distribution** - Email patient intake forms after confirmation
- ✅ **Automated Reminder System** - 3 automated reminders via email and SMS

### Technical Implementation
- **Framework**: LangChain + Google Gemini AI
- **Frontend**: Streamlit web application
- **Database**: SQLite with synthetic patient data (50+ patients)
- **Communication**: Email (SMTP) + SMS (Twilio)
- **Export**: Excel reports for admin review

## 📁 Project Structure

```
agent/
├── app.py                      # Main Streamlit application
├── medical_agent_simple.py     # Core AI scheduling agent
├── database_manager.py         # Database operations
├── communication.py            # Email & SMS functionality
├── reports.py                  # Report generation utilities
├── generate_data.py            # Synthetic data generator
├── .env                       # Environment variables
├── requirements.txt           # Python dependencies
├── data/
│   ├── medical_scheduler.db   # SQLite database
│   ├── patients.csv          # Patient data
│   └── doctor_schedules.xlsx # Doctor availability
├── forms/
│   └── patient_intake_form.html # Patient intake form
├── reports/                   # Generated reports
└── exports/                   # Excel exports
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

### 2. Database Manager
- **Location**: `database_manager.py`
- **Function**: SQLite database operations
- **Tables**: Patients, Doctors, Schedules, Appointments, Reminders

### 3. Communication System
- **Location**: `communication.py`
- **Function**: Email and SMS notifications
- **Features**: Confirmations, reminders, form distribution

### 4. Streamlit Interface
- **Location**: `app.py`
- **Function**: Web-based user interface
- **Pages**: Chat, Analytics, Appointments, Admin Panel

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

### Reminder System
1. **First Reminder**: 24 hours before appointment
2. **Second Reminder**: 4 hours before (with form completion check)
3. **Final Reminder**: 1 hour before (with confirmation request)

### Form Management
- Intake forms sent immediately after booking confirmation
- Pre-visit medication instructions included
- 24-hour submission deadline before appointment

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

### Planned Features
- [ ] Calendar integration (Google Calendar, Outlook)
- [ ] Patient portal access
- [ ] Advanced AI conversation capabilities
- [ ] Multi-language support
- [ ] Mobile app companion
- [ ] Insurance verification API
- [ ] Telehealth integration

### Technical Improvements
- [ ] PostgreSQL migration for production
- [ ] Redis caching layer
- [ ] API documentation with FastAPI
- [ ] Containerization with Docker
- [ ] CI/CD pipeline setup

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

## 📝 Development Notes

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

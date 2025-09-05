# 🔗 Patient Intake Form - Quick Reference

## ✅ **FIXED ISSUES:**

1. **URL Path Error**: Removed `/patient_intake_form` from URLs
2. **Port Conflict**: Moved form app to port 8503
3. **Date Format Error**: Added support for MM/DD/YYYY format
4. **Query Parameters**: Updated to use `st.query_params` (modern Streamlit)

## 🌐 **CORRECT URLs:**

### **Main Medical App:**
- URL: http://localhost:8502
- Purpose: Book appointments, manage patients

### **Patient Intake Forms:**
- URL: http://localhost:8503?patient_id=<PATIENT_ID>
- Purpose: Patient form completion

## 🧪 **Test URLs (Ready to Use):**

Based on your current database, here are working test URLs:

```
Jane Brown: http://localhost:8503?patient_id=fb9e265c
Lisa Hernandez: http://localhost:8503?patient_id=4d885dc9  
Dorothy Gonzalez: http://localhost:8503?patient_id=c0445c60
```

## 🚀 **How to Run Both Apps:**

### Terminal 1 - Main App:
```bash
streamlit run app.py
# Runs on http://localhost:8502
```

### Terminal 2 - Form App:
```bash
streamlit run patient_intake_form.py --server.port 8503
# Runs on http://localhost:8503
```

## 📧 **Email Integration:**

When patients book appointments, they receive emails with personalized form URLs like:
```
http://localhost:8503?patient_id=fb9e265c
```

## ✅ **Status:**
- ✅ Main app running on port 8502
- ✅ Form app running on port 8503  
- ✅ Patient forms working with database integration
- ✅ Reminders set for immediate testing (5-15-25 seconds)

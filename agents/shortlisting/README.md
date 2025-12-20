# Test Management System

A comprehensive test management system for HR teams to create and manage technical assessments using Codeforces problems.

## Features

### HR Component
- **Question Selection**: Browse and select problems from Codeforces API
- **Test Creation**: Create tests with custom names, descriptions, and selected problems
- **Candidate Management**: Send test invitations to selected candidates via email
- **Results Tracking**: Fetch and view candidate results from Codeforces
- **Filtering**: Filter problems by difficulty, tags, and other criteria

### Candidate Component
- **Test Registration**: Register with email and Codeforces username
- **Problem Access**: View assigned problems with direct links to Codeforces
- **Progress Tracking**: Automatic tracking of solved problems

## System Architecture

### Backend (Flask API)
- **Database Management**: SQLite databases for tests, candidates, and results
- **Codeforces Integration**: API integration for problem fetching and result checking
- **Email Service**: Automated email notifications for test invitations
- **RESTful APIs**: Complete API endpoints for all operations

### Frontend (React)
- **HR Dashboard**: Complete test management interface
- **Candidate Interface**: Clean, professional test-taking interface
- **Responsive Design**: Works on desktop and mobile devices

## Database Schema

### selected_candidates.db
- `selected_candidates`: Existing candidate data
- `tests`: Test information and configuration
- `test_notifications`: Email notification tracking

### userids.db
- `userids`: Candidate Codeforces username registration
- `test_results`: Detailed test results and submissions

## Installation & Setup

### Backend Setup
```bash
cd agents/shortlisting
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd front
npm install
```

### Environment Variables
Create a `.env` file in the project root:
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
```

## Usage

### Starting the System

1. **Start Backend API**:
```bash
cd agents/shortlisting
python start_server.py
```

2. **Start Frontend**:
```bash
cd front
npm run dev
```

### HR Workflow

1. **Access HR Interface**: Navigate to `http://localhost:3000/hr-tests`
2. **Create Test**: 
   - Set difficulty range and tags
   - Fetch problems from Codeforces
   - Select desired problems
   - Create test with name and description
3. **Send Invitations**: Click "Send Invites" to notify all candidates
4. **View Results**: Use "View Results" to fetch and display candidate performance

### Candidate Workflow

1. **Receive Email**: Candidates get test invitation with link
2. **Access Test**: Click link to go to `http://localhost:3000/test/{test_id}`
3. **Register**: Enter email and Codeforces username
4. **Take Test**: Solve problems on Codeforces platform
5. **Automatic Tracking**: Results are automatically tracked

## API Endpoints

### Test Management
- `GET /api/tests/problems` - Fetch available problems
- `POST /api/tests/create` - Create new test
- `GET /api/tests` - Get all tests
- `POST /api/tests/{id}/send-invitations` - Send test invitations

### Candidate Management
- `POST /api/tests/{id}/register` - Register candidate
- `POST /api/tests/{id}/fetch-results` - Fetch results from Codeforces
- `GET /api/tests/{id}/results` - Get test results

## Codeforces Integration

The system integrates with Codeforces API to:
- Fetch available problems with filtering
- Verify candidate usernames
- Check problem solving status
- Retrieve submission details

## Email Notifications

Automated email system sends:
- Test invitation emails to candidates
- Professional email templates
- Direct links to test interface

## Security Features

- Input validation on all forms
- SQL injection protection
- Email verification for usernames
- Secure API endpoints

## Professional Features

- Clean, modern UI design
- Responsive layout
- Real-time status updates
- Comprehensive error handling
- Professional email templates
- Detailed result analytics

## Troubleshooting

### Common Issues

1. **Email not sending**: Check SMTP credentials in `.env` file
2. **Codeforces API errors**: Verify internet connection and API availability
3. **Database errors**: Ensure proper file permissions for SQLite databases
4. **Frontend not loading**: Check if backend API is running on port 5001

### Support

For technical support or feature requests, please contact the development team.

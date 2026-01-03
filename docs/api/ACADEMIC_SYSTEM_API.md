# 📚 Academic System API Documentation

> **For Frontend Developers** - React/Next.js/Vue.js Integration Guide

---

## 🔐 Authentication

All endpoints require JWT authentication.

**Headers Required:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Branch Context:**
JWT tokens contain `branch_id` and `branch_role` claims. All API calls are automatically scoped to the user's current branch.

---

## 📋 Schedule Management API

### Timetable Templates

#### GET `/api/v1/school/timetables/`
List all timetable templates.

**Query Params:**
- `academic_year` (UUID) - Filter by academic year
- `is_active` (boolean) - Filter active templates

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Fall 2025",
    "branch": "uuid",
    "academic_year": "uuid",
    "is_active": true,
    "effective_from": "2025-09-01",
    "slots_count": 45,
    "created_at": "2025-01-01T00:00:00Z"
  }
]
```

**Permissions:** Teacher, Admin

---

#### POST `/api/v1/school/timetables/`
Create new timetable template.

**Request Body:**
```json
{
  "name": "Fall 2025",
  "academic_year": "uuid",
  "effective_from": "2025-09-01",
  "is_active": true,
  "notes": "Optional notes"
}
```

**Response:** Same as GET (single object)

**Permissions:** Admin only

---

#### POST `/api/v1/school/timetables/{id}/activate/`
Activate a timetable template.

**Response:**
```json
{
  "id": "uuid",
  "is_active": true,
  "message": "Template activated successfully"
}
```

**Side Effects:** Deactivates other templates for same academic year

**Permissions:** Admin only

---

### Timetable Slots

#### GET `/api/v1/school/timetable-slots/`
List slots for a timetable.

**Query Params:**
- `timetable` (UUID, **required**) - Filter by timetable
- `class_subject` (UUID) - Filter by class subject
- `day_of_week` (0-6) - Filter by day (0=Monday, 6=Sunday)

**Response:**
```json
[
  {
    "id": "uuid",
    "timetable": "uuid",
    "class_subject": "uuid",
    "day_of_week": 0,
    "lesson_number": 1,
    "start_time": "08:00:00",
    "end_time": "08:45:00",
    "room": "uuid"
  }
]
```

**Permissions:** Teacher, Admin

---

#### POST `/api/v1/school/timetable-slots/`
Create new slot.

**Request Body:**
```json
{
  "timetable": "uuid",
  "class_subject": "uuid",
  "day_of_week": 0,
  "lesson_number": 1,
  "start_time": "08:00:00",
  "end_time": "08:45:00",
  "room": "uuid"
}
```

**Validation:**
- Checks teacher conflicts (same teacher, same time)
- Checks room conflicts (same room, same time)
- Returns 400 with conflict details if found

**Error Response (409 Conflict):**
```json
{
  "conflicts": [
    "Teacher already has a lesson at this time",
    "Room is already booked"
  ]
}
```

**Permissions:** Admin only

---

### Lesson Instances

#### GET `/api/v1/school/lessons/`
List generated lessons.

**Query Params:**
- `class_subject` (UUID) - Filter by class subject
- `date` (YYYY-MM-DD) - Filter by specific date
- `date_from` (YYYY-MM-DD) - Filter from date
- `date_to` (YYYY-MM-DD) - Filter to date
- `status` (planned|completed|canceled)

**Response:**
```json
[
  {
    "id": "uuid",
    "class_subject": "uuid",
    "date": "2026-01-06",
    "lesson_number": 1,
    "start_time": "08:00:00",
    "end_time": "08:45:00",
    "topic": {
      "id": "uuid",
      "title": "Introduction to Algebra"
    },
    "room": "uuid",
    "status": "planned",
    "is_auto_generated": true
  }
]
```

**Permissions:** Teacher, Student (filtered), Admin

---

#### POST `/api/v1/school/lessons/generate/`
Generate lessons from timetable.

**Request Body:**
```json
{
  "timetable_id": "uuid",
  "start_date": "2026-01-06",
  "end_date": "2026-01-12",
  "skip_existing": true
}
```

**Response:**
```json
{
  "generated": 35,
  "skipped": 5,
  "message": "Generated 35 lessons successfully"
}
```

**Notes:**
- Respects working_days from BranchSettings
- Skips holidays
- Idempotent if `skip_existing=true`

**Permissions:** Admin only

---

#### POST `/api/v1/school/lessons/{id}/complete/`
Mark lesson as completed.

**Response:** Updated lesson object

**Permissions:** Teacher (own lessons), Admin

---

### Lesson Topics

#### GET `/api/v1/school/lesson-topics/`
List curriculum topics.

**Query Params:**
- `subject` (UUID, **required**)
- `quarter` (UUID)

**Response:**
```json
[
  {
    "id": "uuid",
    "subject": "uuid",
    "quarter": "uuid",
    "title": "Introduction",
    "description": "Basic concepts",
    "position": 1
  }
]
```

**Note:** Ordered by `position` field (manual teacher ordering)

**Permissions:** Teacher, Admin

---

#### POST `/api/v1/school/lesson-topics/`
Create new topic.

**Request Body:**
```json
{
  "subject": "uuid",
  "quarter": "uuid",
  "title": "Introduction",
  "description": "Basic concepts",
  "position": 1
}
```

**Permissions:** Teacher, Admin

---

#### POST `/api/v1/school/lesson-topics/{id}/reorder/`
Change topic position.

**Request Body:**
```json
{
  "new_position": 5
}
```

**Permissions:** Teacher, Admin

---

## ✅ Attendance API

### Lesson Attendance

#### GET `/api/v1/school/attendance/`
List attendance sheets.

**Query Params:**
- `class_subject` (UUID)
- `date` (YYYY-MM-DD)
- `is_locked` (boolean)

**Response:**
```json
[
  {
    "id": "uuid",
    "class_subject": "uuid",
    "lesson": "uuid",
    "date": "2026-01-06",
    "lesson_number": 1,
    "is_locked": false,
    "locked_at": null,
    "records_count": 25,
    "present_count": 23
  }
]
```

**Permissions:** Teacher, Admin

---

#### POST `/api/v1/school/attendance/`
Create attendance sheet.

**Request Body:**
```json
{
  "class_subject": "uuid",
  "lesson": "uuid",  // optional
  "date": "2026-01-06",
  "lesson_number": 1
}
```

**Permissions:** Teacher, Admin

---

#### POST `/api/v1/school/attendance/bulk-mark/`
Mark attendance for multiple students.

**Request Body:**
```json
{
  "attendance_id": "uuid",
  "records": [
    {
      "student_id": "uuid",
      "status": "present"
    },
    {
      "student_id": "uuid",
      "status": "absent",
      "notes": "Sick"
    }
  ]
}
```

**Status Options:** `present`, `absent`, `late`, `excused`, `sick`

**Response:**
```json
{
  "created": 23,
  "updated": 2,
  "errors": []
}
```

**Validation:**
- Fails if attendance is locked
- Returns 400 with error message

**Permissions:** Teacher (own classes), Admin

---

#### POST `/api/v1/school/attendance/{id}/lock/`
Lock attendance (prevent further edits).

**Response:** Updated attendance object with `is_locked: true`

**Note:** Used for N-day locking policy. Once locked, only admin can unlock.

**Permissions:** Admin only

---

#### POST `/api/v1/school/attendance/{id}/unlock/`
Unlock attendance (admin override).

**Response:** Updated attendance object with `is_locked: false`

**Permissions:** Admin only

---

### Attendance Statistics

#### GET `/api/v1/school/attendance/statistics/student/`
Get student attendance statistics.

**Query Params:**
- `student_id` (UUID, **required**)
- `quarter_id` (UUID) - Optional filter

**Response:**
```json
{
  "total_homework": 20,
  "submitted": 18,
  "not_submitted": 2,
  "late": 3,
  "graded": 15,
  "average_score": 85.5,
  "completion_rate": 90.0
}
```

**Permissions:** Teacher, Student (own stats), Admin

---

#### GET `/api/v1/school/attendance/statistics/class/`
Get class attendance statistics.

**Query Params:**
- `class_id` (UUID, **required**)
- `quarter_id` (UUID) - Optional filter

**Response:**
```json
{
  "total_students": 25,
  "average_attendance_rate": 92.5,
  "absent_count": 3,
  "late_count": 5
}
```

**Permissions:** Teacher, Admin

---

## 📊 Grades API

### Assessment Types

#### GET `/api/v1/school/assessment-types/`
List assessment types for branch.

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Quiz",
    "code": "quiz",
    "default_max_score": "10.00",
    "default_weight": "0.20",
    "color": "#3498db",
    "is_active": true
  }
]
```

**Note:** Pre-configured by admin per branch

**Permissions:** Teacher, Admin

---

### Assessments

#### GET `/api/v1/school/assessments/`
List assessments.

**Query Params:**
- `class_subject` (UUID)
- `quarter` (UUID)
- `date_from` (YYYY-MM-DD)
- `date_to` (YYYY-MM-DD)
- `is_locked` (boolean)

**Response:**
```json
[
  {
    "id": "uuid",
    "class_subject": "uuid",
    "assessment_type": "uuid",
    "quarter": "uuid",
    "title": "Midterm Exam",
    "date": "2026-01-15",
    "max_score": "100.00",
    "weight": "0.40",
    "is_locked": false,
    "grades_count": 25,
    "average_score": "78.50"
  }
]
```

**Permissions:** Teacher, Admin

---

#### POST `/api/v1/school/assessments/`
Create assessment.

**Request Body:**
```json
{
  "class_subject": "uuid",
  "assessment_type": "uuid",
  "quarter": "uuid",
  "title": "Midterm Exam",
  "description": "Chapters 1-5",
  "date": "2026-01-15",
  "max_score": "100.00",
  "weight": "0.40",
  "lesson": "uuid"  // optional
}
```

**Permissions:** Teacher, Admin

---

#### POST `/api/v1/school/assessments/{id}/lock/`
Lock assessment (prevent grade changes).

**Response:** Updated assessment with `is_locked: true`

**Note:** Typically done after releasing grades to students

**Permissions:** Admin only

---

### Grades

#### GET `/api/v1/school/grades/`
List grades.

**Query Params:**
- `assessment` (UUID)
- `student` (UUID)
- `class_subject` (UUID)

**Response:**
```json
[
  {
    "id": "uuid",
    "assessment": "uuid",
    "student": "uuid",
    "student_name": "John Doe",
    "score": "85.00",
    "calculated_score": "4.25",
    "final_score": "4.50",
    "override_reason": "Extra credit for project",
    "graded_at": "2026-01-16T10:00:00Z"
  }
]
```

**Note:**
- `calculated_score` = auto-calculated percentage
- `final_score` = manual override (if provided)

**Permissions:** Teacher, Student (own grades), Admin

---

#### POST `/api/v1/school/grades/bulk-create/`
Grade multiple students at once.

**Request Body:**
```json
{
  "assessment_id": "uuid",
  "grades": [
    {
      "student_id": "uuid",
      "score": "85.00"
    },
    {
      "student_id": "uuid",
      "score": "92.00"
    }
  ]
}
```

**Response:**
```json
{
  "created": 25,
  "updated": 0,
  "errors": []
}
```

**Validation:**
- Fails if assessment is locked
- Returns errors for invalid scores (> max_score)

**Permissions:** Teacher, Admin

---

#### PUT `/api/v1/school/grades/{id}/`
Update grade (manual override).

**Request Body:**
```json
{
  "final_score": "4.50",
  "override_reason": "Extra credit for project"
}
```

**Validation:**
- `override_reason` is **required** when setting `final_score`
- Fails if assessment is locked

**Permissions:** Teacher, Admin

---

### Quarter Grades

#### GET `/api/v1/school/quarter-grades/`
List aggregated quarter grades.

**Query Params:**
- `student` (UUID)
- `class_subject` (UUID)
- `quarter` (UUID)

**Response:**
```json
[
  {
    "id": "uuid",
    "student": "uuid",
    "class_subject": "uuid",
    "quarter": "uuid",
    "calculated_grade": "4.30",
    "final_grade": "4.30",
    "is_locked": false,
    "last_calculated": "2026-01-16T12:00:00Z"
  }
]
```

**Note:**
- `calculated_grade` = weighted average from all assessments
- Auto-updates when underlying grades change

**Permissions:** Teacher, Student (own), Admin

---

#### POST `/api/v1/school/quarter-grades/calculate/`
Recalculate quarter grades.

**Request Body:**
```json
{
  "quarter_id": "uuid",
  "class_subject_id": "uuid"  // optional
}
```

**Response:**
```json
{
  "calculated": 125,
  "message": "Recalculated 125 quarter grades"
}
```

**Permissions:** Admin only

---

### Grade Statistics

#### GET `/api/v1/school/grades/statistics/student/`
Get student grade statistics.

**Query Params:**
- `student_id` (UUID, **required**)
- `quarter_id` (UUID)

**Response:**
```json
{
  "total_assessments": 15,
  "graded": 15,
  "average_score": "4.25",
  "by_type": {
    "quiz": {"count": 5, "average": "4.10"},
    "exam": {"count": 3, "average": "4.50"}
  }
}
```

**Permissions:** Teacher, Student (own), Admin

---

## 📝 Homework API

### Homework

#### GET `/api/v1/school/homework/`
List homework assignments.

**Query Params:**
- `class_subject` (UUID)
- `status` (active|closed|archived)
- `due_date_from` (YYYY-MM-DD)
- `due_date_to` (YYYY-MM-DD)

**Response:**
```json
[
  {
    "id": "uuid",
    "class_subject": "uuid",
    "title": "Chapter 1 Exercises",
    "assigned_date": "2026-01-06",
    "due_date": "2026-01-13",
    "status": "active",
    "allow_late_submission": true,
    "max_score": "100.00",
    "submissions_count": 18,
    "completion_rate": 72.0,
    "is_overdue": false
  }
]
```

**Permissions:** Teacher, Student (own classes), Admin

---

#### POST `/api/v1/school/homework/`
Create homework.

**Request Body:**
```json
{
  "class_subject": "uuid",
  "title": "Chapter 1 Exercises",
  "description": "Complete exercises 1-10 on page 25",
  "assigned_date": "2026-01-06",
  "due_date": "2026-01-13",
  "allow_late_submission": true,
  "max_score": "100.00",
  "attachments": [
    {
      "name": "worksheet.pdf",
      "url": "/media/homework/...",
      "size": 1024000,
      "type": "application/pdf"
    }
  ],
  "lesson": "uuid",  // optional
  "assessment": "uuid"  // optional, links to grading
}
```

**Note:** `attachments` is JSON array of file metadata

**Permissions:** Teacher, Admin

---

#### POST `/api/v1/school/homework/{id}/close/`
Close homework (no more submissions).

**Response:** Updated homework with `status: "closed"`

**Permissions:** Teacher, Admin

---

#### GET `/api/v1/school/homework/{id}/submissions/`
Get all submissions for homework.

**Response:** Array of submission objects (see below)

**Permissions:** Teacher, Admin

---

#### GET `/api/v1/school/homework/{id}/statistics/`
Get homework statistics.

**Response:**
```json
{
  "total_students": 25,
  "submitted": 18,
  "not_submitted": 7,
  "graded": 15,
  "late": 3,
  "average_score": "82.50",
  "completion_rate": 72.0
}
```

**Permissions:** Teacher, Admin

---

### Homework Submissions

#### GET `/api/v1/school/submissions/`
List submissions.

**Query Params:**
- `homework` (UUID)
- `student` (UUID)
- `status` (not_submitted|submitted|late|graded|returned)

**Response:**
```json
[
  {
    "id": "uuid",
    "homework": "uuid",
    "student": "uuid",
    "student_name": "John Doe",
    "submission_text": "My answer...",
    "submitted_at": "2026-01-12T18:30:00Z",
    "status": "submitted",
    "is_late": false,
    "score": null,
    "teacher_feedback": null,
    "graded_at": null,
    "attachments": [
      {
        "name": "answer.pdf",
        "url": "/media/submissions/...",
        "size": 512000,
        "type": "application/pdf"
      }
    ]
  }
]
```

**Permissions:** Teacher, Student (own), Admin

---

#### POST `/api/v1/school/submissions/`
Submit homework.

**Request Body:**
```json
{
  "homework": "uuid",
  "submission_text": "My answer...",
  "attachments": [
    {
      "name": "answer.pdf",
      "url": "/media/submissions/...",
      "size": 512000,
      "type": "application/pdf"
    }
  ]
}
```

**Response:** Created submission object

**Validation:**
- Fails if homework status is not "active"
- Auto-detects late submission
- Fails if late submission not allowed

**Permissions:** Student only

---

#### POST `/api/v1/school/submissions/{id}/grade/`
Grade a submission.

**Request Body:**
```json
{
  "score": "85.00",
  "teacher_feedback": "Good work! Pay attention to..."
}
```

**Response:** Updated submission with `status: "graded"`

**Permissions:** Teacher, Admin

---

#### POST `/api/v1/school/submissions/{id}/return-for-revision/`
Return submission for revision.

**Request Body:**
```json
{
  "teacher_feedback": "Please revise section 2..."
}
```

**Response:** Updated submission with `status: "returned"`

**Note:** Student can resubmit after revision

**Permissions:** Teacher, Admin

---

#### POST `/api/v1/school/submissions/bulk-grade/`
Grade multiple submissions.

**Request Body:**
```json
{
  "grades": [
    {
      "submission_id": "uuid",
      "score": "85.00",
      "teacher_feedback": "Good work"
    },
    {
      "submission_id": "uuid",
      "score": "92.00",
      "teacher_feedback": "Excellent"
    }
  ]
}
```

**Response:**
```json
{
  "results": [
    {"submission_id": "uuid", "status": "success", "score": "85.00"},
    {"submission_id": "uuid", "status": "success", "score": "92.00"}
  ],
  "errors": []
}
```

**Permissions:** Teacher, Admin

---

### Homework Statistics

#### GET `/api/v1/school/statistics/student/`
Get student homework statistics.

**Query Params:**
- `student_id` (UUID, **required**)
- `quarter_id` (UUID)

**Response:**
```json
{
  "total_homework": 20,
  "submitted": 18,
  "not_submitted": 2,
  "late": 3,
  "graded": 15,
  "average_score": "85.50",
  "completion_rate": 90.0
}
```

**Permissions:** Teacher, Student (own), Admin

---

#### GET `/api/v1/school/statistics/class/`
Get class homework statistics.

**Query Params:**
- `class_id` (UUID, **required**)
- `quarter_id` (UUID)

**Response:**
```json
{
  "total_homework": 15,
  "active_homework": 5,
  "closed_homework": 10,
  "total_submissions": 375,
  "graded_submissions": 300,
  "average_completion_rate": 85.5,
  "average_score": "82.30"
}
```

**Permissions:** Teacher, Admin

---

## 🔒 Permission Matrix

| Endpoint | Student | Teacher | Admin |
|----------|---------|---------|-------|
| View schedule | Own classes | Own classes | All |
| Create timetable | ❌ | ❌ | ✅ |
| Generate lessons | ❌ | ❌ | ✅ |
| Mark attendance | ❌ | Own classes | All |
| Lock attendance | ❌ | ❌ | ✅ |
| View grades | Own | Own classes | All |
| Create assessment | ❌ | ✅ | ✅ |
| Grade students | ❌ | ✅ | ✅ |
| Override grades | ❌ | ✅ | ✅ |
| Create homework | ❌ | ✅ | ✅ |
| Submit homework | ✅ | ❌ | ❌ |
| Grade homework | ❌ | ✅ | ✅ |

---

## ⚠️ Important Notes

### File Uploads
Attachments are stored as JSON metadata:
```json
{
  "name": "file.pdf",
  "url": "/media/path/to/file.pdf",
  "size": 1024000,
  "type": "application/pdf"
}
```

Handle file upload separately, then include metadata in API calls.

### Locking Behavior
- **Attendance:** Locked after N days (configurable). Only admin can unlock.
- **Assessments:** Locked manually by teacher/admin. Prevents grade changes.
- **Quarter Grades:** Can be locked after quarter ends.

### Automatic Calculations
- **Grade calculated_score:** Auto-calculated as (score/max_score) * 5
- **Quarter grades:** Auto-recalculated when underlying grades change
- **Attendance statistics:** Updated periodically by background tasks

### Date Formats
- All dates: `YYYY-MM-DD`
- All timestamps: ISO 8601 format `YYYY-MM-DDTHH:MM:SSZ`

### Error Responses
Standard format:
```json
{
  "error": "Error message",
  "details": {
    "field": ["Validation error"]
  }
}
```

HTTP Status Codes:
- `200` - Success
- `201` - Created
- `400` - Validation error
- `401` - Unauthorized
- `403` - Forbidden (wrong role)
- `404` - Not found
- `409` - Conflict (e.g., schedule conflict)
- `500` - Server error

---

## 🚀 Quick Start Example

```javascript
// Login and get token
const login = async () => {
  const response = await fetch('/api/v1/auth/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      phone_number: '+998901234567',
      password: 'password123',
      branch_id: 'branch-uuid'
    })
  });
  const data = await response.json();
  return data.access; // JWT token
};

// List homework for a class
const getHomework = async (token, classSubjectId) => {
  const response = await fetch(
    `/api/v1/school/homework/?class_subject=${classSubjectId}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  return response.json();
};

// Submit homework as student
const submitHomework = async (token, homeworkId, text) => {
  const response = await fetch('/api/v1/school/submissions/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      homework: homeworkId,
      submission_text: text,
      attachments: []
    })
  });
  return response.json();
};
```

---

## 📞 Support

For implementation questions:
1. Check model constraints in backend code
2. Test with Swagger UI: `/api/docs/`
3. Review validation errors in API responses

**Base URL:** `http://localhost:8000` (development)

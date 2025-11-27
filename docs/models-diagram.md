# Modellar Diagrammasi

## Asosiy Modellar va Ularning Munosabatlari

```mermaid
erDiagram
    USER ||--o| PROFILE : "has (OneToOne)"
    USER ||--o{ BRANCH_MEMBERSHIP : "has (ManyToMany)"
    
    BRANCH ||--o{ BRANCH_MEMBERSHIP : "has"
    BRANCH ||--o{ CLASS : "has"
    BRANCH ||--o{ SUBJECT : "has"
    BRANCH ||--o{ BUILDING : "has"
    
    BRANCH_MEMBERSHIP ||--o| STUDENT_PROFILE : "has (OneToOne)"
    BRANCH_MEMBERSHIP ||--o| TEACHER_PROFILE : "has (OneToOne)"
    BRANCH_MEMBERSHIP ||--o| PARENT_PROFILE : "has (OneToOne)"
    BRANCH_MEMBERSHIP ||--o| ADMIN_PROFILE : "has (OneToOne)"
    BRANCH_MEMBERSHIP ||--o| USER_BRANCH_PROFILE : "has (OneToOne)"
    
    STUDENT_PROFILE ||--o{ STUDENT_RELATIVE : "has"
    
    ACADEMIC_YEAR ||--o{ QUARTER : "has"
    ACADEMIC_YEAR ||--o{ CLASS : "has"
    
    CLASS ||--o{ CLASS_STUDENT : "has"
    CLASS ||--o{ CLASS_SUBJECT : "has"
    CLASS }o--o| BRANCH_MEMBERSHIP : "class_teacher"
    CLASS }o--o| ROOM : "room"
    
    CLASS_STUDENT }o--|| BRANCH_MEMBERSHIP : "membership"
    
    SUBJECT ||--o{ CLASS_SUBJECT : "has"
    CLASS_SUBJECT }o--o| BRANCH_MEMBERSHIP : "teacher"
    CLASS_SUBJECT }o--|| QUARTER : "quarter"
    
    BUILDING ||--o{ ROOM : "has"
    
    ROLE ||--o{ BRANCH_MEMBERSHIP : "role_ref"

    USER {
        uuid id PK
        string phone_number UK
        string first_name
        string last_name
        string email
        bool phone_verified
        bool is_active
        datetime created_at
    }
    
    PROFILE {
        uuid id PK
        uuid user_id FK
        string avatar
        date date_of_birth
        string gender
        string language
        string timezone
        text bio
        string address
        json socials
    }
    
    BRANCH {
        uuid id PK
        string name
        string slug UK
        string type
        string status
        text address
        string phone_number
        string email
    }
    
    BRANCH_MEMBERSHIP {
        uuid id PK
        uuid user_id FK
        uuid branch_id FK
        string role
        uuid role_ref_id FK
        string title
        decimal balance
    }
    
    STUDENT_PROFILE {
        uuid id PK
        uuid user_branch_id FK UK
        string personal_number UK
        string middle_name
        string gender
        date date_of_birth
        text address
        file birth_certificate
        json additional_fields
    }
    
    STUDENT_RELATIVE {
        uuid id PK
        uuid student_profile_id FK
        string relationship_type
        string first_name
        string middle_name
        string last_name
        string phone_number
        string email
        string gender
        date date_of_birth
        text address
        string workplace
        string position
        string passport_number
        file photo
        bool is_primary_contact
        bool is_guardian
        json additional_info
        text notes
    }
    
    TEACHER_PROFILE {
        uuid id PK
        uuid user_branch_id FK UK
        string subject
        int experience_years
        text bio
    }
    
    PARENT_PROFILE {
        uuid id PK
        uuid user_branch_id FK UK
        text notes
    }
    
    ADMIN_PROFILE {
        uuid id PK
        uuid user_branch_id FK UK
        bool is_super_admin
        string title
        text notes
    }
    
    ACADEMIC_YEAR {
        uuid id PK
        uuid branch_id FK
        string name
        date start_date
        date end_date
        bool is_current
    }
    
    QUARTER {
        uuid id PK
        uuid academic_year_id FK
        string name
        date start_date
        date end_date
        bool is_current
    }
    
    CLASS {
        uuid id PK
        uuid branch_id FK
        uuid academic_year_id FK
        uuid class_teacher_id FK
        uuid room_id FK
        string name
        int grade_level
        string section
        int max_students
        bool is_active
    }
    
    CLASS_STUDENT {
        uuid id PK
        uuid class_obj_id FK
        uuid membership_id FK
        date enrollment_date
        bool is_active
        text notes
    }
    
    SUBJECT {
        uuid id PK
        uuid branch_id FK
        string name
        string code
        text description
        bool is_active
    }
    
    CLASS_SUBJECT {
        uuid id PK
        uuid class_obj_id FK
        uuid subject_id FK
        uuid teacher_id FK
        uuid quarter_id FK
        int hours_per_week
        bool is_active
    }
    
    BUILDING {
        uuid id PK
        uuid branch_id FK
        string name
        text address
        text description
    }
    
    ROOM {
        uuid id PK
        uuid building_id FK
        string name
        int capacity
        string room_type
        text description
    }
    
    ROLE {
        uuid id PK
        uuid branch_id FK
        string name
        json permissions
        text description
        bool is_active
    }
```

## Modellar O'rtasidagi Bog'liqlik Darajalari

### 1. **User → BranchMembership → Role Profiles**
```
User (1) → BranchMembership (N) → StudentProfile (1)
                              → TeacherProfile (1)
                              → ParentProfile (1)
                              → AdminProfile (1)
```

### 2. **Branch → School Entities**
```
Branch (1) → Class (N) → ClassStudent (N)
                      → ClassSubject (N)
         → Subject (N)
         → Building (N) → Room (N)
         → AcademicYear (N) → Quarter (N)
```

### 3. **Class Structure**
```
Class (1) → ClassStudent (N) → BranchMembership (1) → User (1)
          → ClassSubject (N) → Subject (1)
                           → BranchMembership (teacher) (1)
                           → Quarter (1)
          → BranchMembership (class_teacher) (1)
          → Room (1)
```

## Field Types va Constraints

### Unique Constraints
- `User.phone_number` - unique
- `Branch.slug` - unique
- `StudentProfile.personal_number` - unique
- `StudentProfile.user_branch` - unique (OneToOne)
- `TeacherProfile.user_branch` - unique (OneToOne)
- `Class.name + branch + academic_year` - unique_together

### Indexes
- `User.phone_number` - db_index
- `StudentProfile.personal_number` - db_index
- `Branch.status`, `Branch.type` - indexes
- `Class.grade_level`, `Class.is_active` - indexes

### Foreign Keys
- Barcha ForeignKey lar `on_delete=models.CASCADE` yoki `SET_NULL`
- `class_teacher` va `room` - `SET_NULL` (ixtiyoriy)
- `membership` - `CASCADE` (majburiy)


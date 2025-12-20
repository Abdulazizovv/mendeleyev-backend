# Staff API URL Fixes and Filtering

**Date:** 2024-12-13  
**Status:** ✅ Completed

## Problem Summary

1. **404 Errors**: Documentation showed incorrect URL `/api/branch/staff/` 
2. **Versioning Confusion**: Actual endpoint is `/api/v1/branches/staff/` (versioned)
3. **Wrong Users Returned**: Staff API returned all users including students and parents

## Root Causes

### 1. URL Structure Mismatch
- **Documented URL**: `/api/branch/staff/` (missing `/v1/` version prefix)
- **Actual URL**: `/api/v1/branches/staff/` (correct versioned path)
- **Source**: 
  - `core/urls.py`: `path('api/v1/branches/', include('apps.branch.urls'))`
  - `apps/branch/urls.py`: `router.register(r'staff', StaffViewSet)`

### 2. Missing Role Filtering
- `StaffViewSet.get_queryset()` returned ALL `BranchMembership` objects
- No filtering to exclude `STUDENT` and `PARENT` roles
- Staff API should only return staff members (admins, teachers, etc.)

## Solutions Applied

### 1. Added Role Filtering (`apps/branch/views.py`)

```python
def get_queryset(self):
    """Filter staff by branch access and active status.
    
    Only returns staff members (excludes students and parents).
    """
    qs = super().get_queryset()
    
    # IMPORTANT: Exclude students and parents - only staff
    qs = qs.exclude(role__in=[BranchRole.STUDENT, BranchRole.PARENT])
    
    # Filter by branch if specified
    branch_id = self.request.query_params.get('branch')
    if branch_id:
        qs = qs.filter(branch_id=branch_id)
    
    # Filter by employment status
    status = self.request.query_params.get('status')
    if status == 'active':
        qs = qs.filter(termination_date__isnull=True)
    elif status == 'terminated':
        qs = qs.filter(termination_date__isnull=False)
    
    return qs.filter(deleted_at__isnull=True)
```

**Key Changes:**
- Added `.exclude(role__in=[BranchRole.STUDENT, BranchRole.PARENT])`
- Only staff roles returned: `SUPER_ADMIN`, `BRANCH_ADMIN`, `TEACHER`, `OTHER`
- Students and parents excluded from all staff API responses

### 2. Updated Documentation URLs

Updated all staff API documentation files:

#### `docs/api/README-staff.md`
- ✅ Base URL: `/api/v1/branches/staff/`
- ✅ All endpoint examples updated
- ✅ TypeScript fetch examples corrected

#### `docs/api/hr.md`
- ✅ Base URL: `/api/v1/branches/staff/`
- ✅ All 8 endpoint sections updated
- ✅ cURL examples corrected
- ✅ Response examples with pagination links updated

#### `docs/api/hr-frontend-integration.md`
- ✅ Base URL: `/api/v1/branches/staff/`
- ✅ All React Query examples updated
- ✅ TypeScript fetch calls corrected
- ✅ All 8 endpoint integrations fixed

#### `docs/staff-refactoring-summary.md`
- ✅ API endpoints list updated

#### `docs/staff-api-bugfixes.md`
- ✅ Testing examples updated

## API Endpoint Reference

All staff endpoints now properly versioned:

```
GET    /api/v1/branches/staff/                    - List staff (no students/parents)
POST   /api/v1/branches/staff/                    - Create staff member
GET    /api/v1/branches/staff/{id}/               - Get staff details
PATCH  /api/v1/branches/staff/{id}/               - Update staff
DELETE /api/v1/branches/staff/{id}/               - Delete staff (soft)
GET    /api/v1/branches/staff/stats/              - Staff statistics
POST   /api/v1/branches/staff/{id}/add_balance/   - Add balance transaction
POST   /api/v1/branches/staff/{id}/pay_salary/    - Record salary payment
```

## Testing

### Test Role Filtering
```bash
# Should return only staff (no students/parents)
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/branches/staff/

# Should return only active teachers
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/branches/staff/?role=teacher-uuid&status=active"
```

### Verify Exclusion
```bash
# Create a student membership
# Then verify it does NOT appear in /api/v1/branches/staff/

# Create a parent membership  
# Then verify it does NOT appear in /api/v1/branches/staff/

# Create a teacher membership
# Then verify it DOES appear in /api/v1/branches/staff/
```

## Impact Analysis

### ✅ Benefits
1. **Correct URLs**: All documentation matches actual API structure
2. **API Versioning**: Proper `/api/v1/` prefix throughout
3. **Data Integrity**: Staff API only returns staff members
4. **Clear Separation**: Students/parents have separate endpoints
5. **No Breaking Changes**: Existing correct API calls still work

### ⚠️ Potential Issues
1. **Frontend Updates Required**: Any frontend using old URL must update
2. **Bookmarks/Scripts**: Any saved URLs or scripts need updating
3. **Third-party Integrations**: External systems must use correct URLs

## Related Files Changed

- `apps/branch/views.py` - Added role filtering
- `docs/api/README-staff.md` - URL corrections
- `docs/api/hr.md` - URL corrections
- `docs/api/hr-frontend-integration.md` - URL corrections
- `docs/staff-refactoring-summary.md` - URL corrections
- `docs/staff-api-bugfixes.md` - URL corrections

## Verification Checklist

- [x] Role filtering added to `StaffViewSet`
- [x] Students excluded from staff API
- [x] Parents excluded from staff API
- [x] All documentation URLs updated to `/api/v1/branches/staff/`
- [x] cURL examples corrected
- [x] TypeScript examples corrected
- [x] React Query hooks updated
- [x] Django check passes
- [ ] Manual API testing completed
- [ ] Frontend team notified of URL changes

## Notes for Frontend Developers

**IMPORTANT:** If you were using `/api/branch/staff/`, update to `/api/v1/branches/staff/`

### Quick Migration
```typescript
// OLD (incorrect)
const res = await fetch('/api/branch/staff/');

// NEW (correct)
const res = await fetch('/api/v1/branches/staff/');
```

### What Changed
1. Base URL now includes `/v1/` for API versioning
2. Staff endpoint only returns staff (teachers, admins, etc.)
3. Students and parents are NOT included in staff responses
4. Use student/parent specific endpoints for those user types

## References

- URL Structure: `core/urls.py` line 8
- Router Registration: `apps/branch/urls.py` line 8
- Staff ViewSet: `apps/branch/views.py` line 546
- Role Enum: `apps/branch/models.py` - `BranchRole` choices

# Changelog

## Phase 4 (RBAC Admin Profiles)

- Added AdminProfile model for admin-class memberships (branch_admin, super_admin).
- Auto-provision AdminProfile via signals on membership save (both legacy UserBranch and canonical BranchMembership).
- Integrated AdminProfile into BranchMembershipSerializer.role_data for admin roles.
- Registered AdminProfile in Django admin and as inline on BranchMembership admin.
- Frontend docs updated with AdminProfile examples and UI guidance (managed_branches selector).
- Backward compatible: no schema changes required; relations continue to target the shared membership table via legacy concrete model.

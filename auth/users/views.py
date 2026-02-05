from __future__ import annotations

import logging
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.utils import extend_schema

from apps.common.otp import OTPService, OTPError
from .serializers import (
    UserSerializer,
    RegisterRequestOTPSerializer,
    RegisterConfirmSerializer,
    LoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    PasswordChangeSerializer,
    PhoneCheckSerializer,
    PhoneVerificationRequestSerializer,
    PhoneVerificationConfirmSerializer,
    PasswordSetSerializer,
    BranchMembershipSerializer,
    SwitchBranchSerializer,
)

logger = logging.getLogger("apps.auth")
User = get_user_model()


# Legacy RequestOTPView and VerifyOTPView removed - use phone/verification/request and phone/verification/confirm instead

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: "MeResponse"},
        summary="Get current authenticated user with profile, branch context, memberships, and role profiles",
        description="""Returns a comprehensive snapshot for the authenticated user including:
        - user: core user fields
        - profile: global profile fields (nullable if not yet created)
        - current_branch: branch context derived from JWT 'br' claim (if scoped) with role & role_data
        - memberships: list of all active branch memberships with role profiles
        - auth_state: high-level auth state (READY, NOT_VERIFIED, NEEDS_PASSWORD, etc.)
        Optimized with select_related to avoid N+1 queries for branch + role-specific profiles.
        """
    )
    def get(self, request):
        from apps.branch.models import BranchMembership, BranchStatuses
        from auth.profiles.serializers import ProfileSerializer
        from .serializers import UserSerializer, BranchMembershipSerializer, MeResponseSerializer

        user = request.user

        # Global profile (may not exist yet)
        profile_obj = getattr(user, "profile", None)
        profile_data = ProfileSerializer(profile_obj).data if profile_obj else None

        # Collect all active memberships with branch & role profiles in one query
        memberships_qs = (
            BranchMembership.objects.select_related(
                "branch",
                "teacher_profile",
                "student_profile",
                "parent_profile",
                "admin_profile",
            )
            .filter(user_id=user.id, branch__status=BranchStatuses.ACTIVE)
        )
        memberships_data = [BranchMembershipSerializer.from_membership(m) for m in memberships_qs]

        # Determine current branch context from JWT claims (request.auth may be a dict from SimpleJWT)
        # Extract branch claims from authenticated token. SimpleJWT usually provides
        # a token object (UntypedToken/AccessToken), not a raw dict, so we support
        # multiple shapes: dict-like, token with .payload, or fallback indexing.
        current_branch_id = None
        current_role = None
        token_auth = getattr(request, "auth", None)
        if token_auth:
            try:
                # Direct dict case (e.g., force_authenticate in tests)
                if isinstance(token_auth, dict):
                    current_branch_id = token_auth.get("br") or token_auth.get("branch_id")
                    current_role = token_auth.get("br_role")
                else:
                    # Token object: prefer .payload if present
                    payload = getattr(token_auth, "payload", None)
                    if isinstance(payload, dict):
                        current_branch_id = payload.get("br") or payload.get("branch_id")
                        current_role = payload.get("br_role")
                    # Fallback: attempt mapping access
                    if not current_branch_id:
                        if hasattr(token_auth, "get"):
                            current_branch_id = token_auth.get("br") or token_auth.get("branch_id")
                            current_role = current_role or token_auth.get("br_role")
                        else:
                            # Last resort indexing
                            try:
                                current_branch_id = token_auth["br"]
                            except Exception:
                                pass
                            try:
                                current_role = token_auth["br_role"]
                            except Exception:
                                pass
            except Exception:
                current_branch_id = None

        current_branch_data = None
        if current_branch_id:
            # Find corresponding membership (already loaded if in memberships_qs) without extra DB hit when possible
            chosen = next((m for m in memberships_qs if str(m.branch_id) == str(current_branch_id)), None)
            if chosen:
                if current_role and current_role != chosen.role:
                    current_role = chosen.role  # reflect updated DB role
                data = BranchMembershipSerializer.from_membership(chosen)
                data["role"] = current_role or chosen.role
                current_branch_data = data
            else:
                # Fallback: token has branch claim but membership not active (role change, inactive branch, or superuser global token)
                try:
                    from apps.branch.models import Branch
                    b = Branch.objects.only("id", "name", "type", "status").get(id=current_branch_id)
                    current_branch_data = {
                        "branch_id": b.id,
                        "branch_name": getattr(b, "name", ""),
                        "branch_type": getattr(b, "type", ""),
                        "branch_status": getattr(b, "status", ""),
                        "role": current_role or "unknown",
                        "title": "",
                        "role_data": None,
                    }
                except Exception:
                    # Silent: keep null if branch not found
                    pass
        elif len(memberships_data) == 1:
            # Auto-select single branch if no branch scope in token
            current_branch_data = memberships_data[0]

        response_payload = {
            "user": UserSerializer(user).data,
            "profile": profile_data,
            "current_branch": current_branch_data,
            "memberships": memberships_data,
            "auth_state": user.auth_state,
        }

        # Serializer used only for schema validation / consistency (does not alter data)
        ser = MeResponseSerializer(response_payload)
        return Response(ser.data)


class RefreshTokenView(TokenRefreshView):
    """Secure refresh that mirrors login branch validation logic.

    Rules:
    - If 'br' claim present and user is NOT superuser/staff:
        * Branch must exist and be ACTIVE.
        * User must have membership (branch-scoped) in that branch.
    - Superuser / staff bypass branch & membership checks.
    - All error responses include machine-friendly 'code'.
    - Preserves original branch claims (br, br_role) in new access token.
    Performance:
    - Single membership query with select_related('branch') used for both checks.
    - Avoids duplicate user fetch failures by narrowing fields.
    """
    permission_classes = [AllowAny]

    @extend_schema(summary="Refresh JWT token with full branch validation")
    def post(self, request, *args, **kwargs):
        from rest_framework_simplejwt.serializers import TokenRefreshSerializer
        refresh_str = request.data.get("refresh")
        if not refresh_str:
            return Response({"detail": "Missing refresh token", "code": "refresh_missing"}, status=status.HTTP_400_BAD_REQUEST)
        # Validate refresh structure via serializer (will also rotate if configured)
        serializer = TokenRefreshSerializer(data={"refresh": refresh_str})
        serializer.is_valid(raise_exception=True)
        try:
            incoming_refresh = RefreshToken(refresh_str)
        except Exception:
            return Response({"detail": "Invalid refresh token", "code": "refresh_invalid"}, status=status.HTTP_401_UNAUTHORIZED)

        payload = incoming_refresh.payload
        user_id = payload.get("user_id") or payload.get("user")
        if not user_id:
            return Response({"detail": "Malformed token (user_id missing)", "code": "user_id_missing"}, status=status.HTTP_401_UNAUTHORIZED)

        # Narrow user query for speed
        try:
            user = User.objects.only("id", "is_staff", "is_superuser").get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found", "code": "user_not_found"}, status=status.HTTP_401_UNAUTHORIZED)

        br = payload.get("br")  # branch scope claim (string UUID) if present
        br_role = payload.get("br_role")

        # Validate branch + membership for non-admin scoped tokens
        membership = None
        if br and not (user.is_superuser or user.is_staff):
            from apps.branch.models import BranchMembership, BranchStatuses
            membership = (
                BranchMembership.objects.select_related("branch")
                .only("id", "role", "branch__id", "branch__status", "user_id")
                .filter(user_id=user.id, branch_id=br)
                .first()
            )
            if not membership:
                return Response({"detail": "Membership not found", "code": "membership_not_found"}, status=status.HTTP_401_UNAUTHORIZED)
            if membership.branch.status != BranchStatuses.ACTIVE:
                return Response({"detail": "Branch not active", "code": "branch_inactive", "branch_status": membership.branch.status}, status=status.HTTP_403_FORBIDDEN)

        # Build new access token from validated serializer output (preserves refresh rotation config)
        new_refresh_str = serializer.validated_data.get("refresh", refresh_str)
        try:
            refresh_obj = RefreshToken(new_refresh_str)
        except Exception:
            # Fallback to original
            refresh_obj = incoming_refresh
        access = refresh_obj.access_token

        if br:
            access["br"] = br
            # Decide br_role: prefer existing claim, else derive from membership if loaded
            if br_role:
                access["br_role"] = br_role
            elif membership:
                access["br_role"] = membership.role

        # Response matches original format; include new refresh if rotated
        response_payload = {"access": str(access), "refresh": str(refresh_obj)}
        return Response(response_payload, status=status.HTTP_200_OK)


class RegisterRequestOTPView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterRequestOTPSerializer

    @extend_schema(
        request=RegisterRequestOTPSerializer,
        responses={200: dict},
        summary="Request registration OTP",
        description="Sends an OTP code (purpose=register) to the provided phone if cooldown allows."
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone_number"]
        try:
            OTPService.request_code(phone, purpose="register")
        except OTPError as e:
            return Response({"detail": str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        return Response({"detail": "OTP sent (register)"}, status=status.HTTP_200_OK)


class RegisterConfirmView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterConfirmSerializer

    @extend_schema(
        request=RegisterConfirmSerializer,
        responses={201: dict, 200: dict},
        summary="Confirm registration OTP and set password",
        description="Verifies OTP (purpose=register). Creates user if not exists, sets password, marks phone_verified, and returns JWT tokens."
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone_number"]
        code = serializer.validated_data["code"]
        password = serializer.validated_data["password"]
        if not OTPService.verify_code(phone, code, purpose="register"):
            return Response({"detail": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)
        user, created = User.objects.get_or_create(phone_number=phone)
        user.set_password(password)
        user.phone_verified = True
        user.is_active = True
        user.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
            "created": created,
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class LoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    @extend_schema(
        request=LoginSerializer,
        responses={200: dict},
        summary="Login with phone + password",
        description="Requires phone_verified=True. Returns JWT tokens on success."
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone_number"]
        password = serializer.validated_data["password"]
        branch_id = serializer.validated_data.get("branch_id")
        try:
            user = User.objects.get(phone_number=phone)
        except User.DoesNotExist:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        if not user.phone_verified:
            return Response({"state": "NOT_VERIFIED"}, status=status.HTTP_200_OK)
        if not user.has_usable_password():
            return Response({"state": "NEEDS_PASSWORD"}, status=status.HTTP_200_OK)
        if not user.check_password(password):
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Collect all active memberships for this user
        from apps.branch.models import BranchMembership
        qs = BranchMembership.objects.select_related("branch").filter(user_id=user.id, branch__status="active")
        memberships = list(qs)
        
        # Super/admin: can use global token or scoped token
        if user.is_superuser or user.is_staff:
            if branch_id:
                # Explicit branch requested
                from apps.branch.models import Branch
                try:
                    b = Branch.objects.get(id=branch_id, status="active")
                except Branch.DoesNotExist:
                    return Response({"detail": "Branch not active or not found"}, status=status.HTTP_400_BAD_REQUEST)
                # Check if user has membership to get role
                mem = next((m for m in memberships if str(m.branch_id) == str(branch_id)), None)
                refresh = RefreshToken.for_user(user)
                access = refresh.access_token
                refresh["br"] = str(b.id)
                access["br"] = str(b.id)
                if mem:
                    refresh["br_role"] = mem.role
                    access["br_role"] = mem.role
                return Response({
                    "access": str(access),
                    "refresh": str(refresh),
                    "user": UserSerializer(user).data,
                    "br": str(b.id),
                    "br_role": mem.role if mem else None,
                })
            elif len(memberships) == 1:
                # Auto-select single branch for staff users
                chosen = memberships[0]
                refresh = RefreshToken.for_user(user)
                access = refresh.access_token
                refresh["br"] = str(chosen.branch_id)
                refresh["br_role"] = chosen.role
                access["br"] = str(chosen.branch_id)
                access["br_role"] = chosen.role
                return Response({
                    "access": str(access),
                    "refresh": str(refresh),
                    "user": UserSerializer(user).data,
                    "br": str(chosen.branch_id),
                    "br_role": chosen.role,
                })
            else:
                # Multiple or no branches - return global token
                refresh = RefreshToken.for_user(user)
                return Response({
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": UserSerializer(user).data,
                })

        # Non-admin: require active branch membership
        if len(memberships) == 0:
            return Response({"state": "NO_BRANCH"}, status=status.HTTP_200_OK)
        chosen = None
        if branch_id:
            chosen = next((m for m in memberships if str(m.branch_id) == str(branch_id)), None)
            if not chosen:
                return Response({"detail": "Branch not found or inactive for this user"}, status=status.HTTP_400_BAD_REQUEST)
        elif len(memberships) == 1:
            chosen = memberships[0]
        else:
            from .serializers import BranchMembershipSerializer
            data = [BranchMembershipSerializer.from_membership(m) for m in memberships]
            return Response({"state": "MULTI_BRANCH", "branches": data}, status=status.HTTP_200_OK)

        # Issue branch-scoped tokens (with role)
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        refresh["br"] = str(chosen.branch_id)
        refresh["br_role"] = chosen.role
        access["br"] = str(chosen.branch_id)
        access["br_role"] = chosen.role
        return Response({
            "access": str(access),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
            "br": str(chosen.branch_id),
            "br_role": chosen.role,
        })


class PasswordResetRequestView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    @extend_schema(
        request=PasswordResetRequestSerializer,
        responses={200: dict},
        summary="Request password reset OTP",
        description="If a verified user exists for the phone, sends an OTP (purpose=reset). Always returns 200 to prevent enumeration."
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone_number"]
        if User.objects.filter(phone_number=phone, phone_verified=True).exists():
            try:
                OTPService.request_code(phone, purpose="reset")
            except OTPError as e:
                return Response({"detail": str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        return Response({"detail": "If account exists, OTP sent (reset)"}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    @extend_schema(
        request=PasswordResetConfirmSerializer,
        responses={200: dict},
        summary="Confirm password reset OTP and set new password",
        description="Verifies OTP (purpose=reset) and sets a new password. Returns fresh JWT tokens."
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone_number"]
        code = serializer.validated_data["code"]
        new_password = serializer.validated_data["new_password"]
        try:
            user = User.objects.get(phone_number=phone, phone_verified=True)
        except User.DoesNotExist:
            return Response({"detail": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)
        if not OTPService.verify_code(phone, code, purpose="reset"):
            return Response({"detail": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        })


class PasswordChangeView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    @extend_schema(
        request=PasswordChangeSerializer,
        responses={200: dict},
        summary="Change password (authenticated)",
        description="Authenticated user supplies old password and a new one passing validators; on success updates credentials."
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user: User = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response({"detail": "Old password incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        new_password = serializer.validated_data["new_password"]
        user.set_password(new_password)
        user.save()
        return Response({"detail": "Password changed"}, status=status.HTTP_200_OK)


class PhoneCheckView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PhoneCheckSerializer

    @extend_schema(request=PhoneCheckSerializer, responses={200: dict}, summary="Check phone auth state")
    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        phone = ser.validated_data["phone_number"]
        from django.utils import timezone
        try:
            user = User.objects.get(phone_number=phone)
        except User.DoesNotExist:
            try:
                from apps.common.tasks_alerts import send_unknown_phone_attempt_task
                send_unknown_phone_attempt_task.delay(phone)
            except Exception:
                logger.exception("Unknown phone notify enqueue failed")
            return Response({"state": "NOT_FOUND"}, status=status.HTTP_200_OK)
        return Response({"state": user.auth_state}, status=status.HTTP_200_OK)


class PhoneVerificationRequestView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PhoneVerificationRequestSerializer

    @extend_schema(request=PhoneVerificationRequestSerializer, responses={200: dict}, summary="Request phone verification OTP")
    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        phone = ser.validated_data["phone_number"]
        try:
            user = User.objects.get(phone_number=phone)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if user.phone_verified:
            return Response({"detail": "Already verified", "state": user.auth_state}, status=status.HTTP_200_OK)
        try:
            OTPService.request_code(phone, purpose="verify")
        except OTPError as e:
            return Response({"detail": str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        return Response({"detail": "OTP sent", "state": user.auth_state}, status=status.HTTP_200_OK)


class PhoneVerificationConfirmView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PhoneVerificationConfirmSerializer

    @extend_schema(request=PhoneVerificationConfirmSerializer, responses={200: dict}, summary="Confirm phone verification OTP")
    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        phone = ser.validated_data["phone_number"]
        code = ser.validated_data["code"]
        try:
            user = User.objects.get(phone_number=phone)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if user.phone_verified:
            return Response({"detail": "Already verified", "state": user.auth_state}, status=status.HTTP_200_OK)
        if not OTPService.verify_code(phone, code, purpose="verify"):
            return Response({"detail": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)
        user.phone_verified = True
        user.save(update_fields=["phone_verified", "updated_at"])
        # If password already set, issue tokens now for convenience
        if user.has_usable_password():
            refresh = RefreshToken.for_user(user)
            return Response({
                "state": user.auth_state,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }, status=status.HTTP_200_OK)
        return Response({"state": user.auth_state}, status=status.HTTP_200_OK)


class PasswordSetView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordSetSerializer

    @extend_schema(request=PasswordSetSerializer, responses={200: dict}, summary="Set initial password after verification")
    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        phone = ser.validated_data["phone_number"]
        password = ser.validated_data["password"]
        try:
            user = User.objects.get(phone_number=phone)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if not user.phone_verified:
            return Response({"state": "NOT_VERIFIED", "detail": "Phone not verified"}, status=status.HTTP_400_BAD_REQUEST)
        if user.has_usable_password():
            return Response({"state": user.auth_state, "detail": "Password already set"}, status=status.HTTP_200_OK)
        user.set_password(password)
        user.save(update_fields=["password", "updated_at"])
        refresh = RefreshToken.for_user(user)
        return Response({
            "state": user.auth_state,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_200_OK)


class MyBranchesView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: dict}, summary="List current user's branch memberships")
    def get(self, request, *args, **kwargs):
        from apps.branch.models import BranchMembership
        qs = (
            BranchMembership.objects
            .select_related("branch")
            .filter(user_id=request.user.id)
            .order_by("branch__name")
        )
        data = [BranchMembershipSerializer.from_membership(m) for m in qs]
        return Response({"results": data, "count": len(data)})


class SwitchBranchView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = SwitchBranchSerializer

    @extend_schema(request=SwitchBranchSerializer, responses={200: dict}, summary="Switch branch by issuing new scoped tokens")
    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        refresh_str = ser.validated_data["refresh"]
        branch_id = str(ser.validated_data["branch_id"])
        try:
            token = RefreshToken(refresh_str)
        except Exception:
            return Response({"detail": "Invalid refresh"}, status=status.HTTP_401_UNAUTHORIZED)
        # resolve user
        try:
            user = User.objects.get(id=token["user_id"])  # type: ignore
        except Exception:
            return Response({"detail": "Invalid user"}, status=status.HTTP_401_UNAUTHORIZED)
        # super/admin: allow scoping to any active branch
        from apps.branch.models import Branch
        if user.is_superuser or user.is_staff:
            try:
                b = Branch.objects.get(id=branch_id, status="active")
            except Branch.DoesNotExist:
                return Response({"detail": "Branch not active or not found"}, status=status.HTTP_400_BAD_REQUEST)
            new_refresh = RefreshToken.for_user(user)
            new_access = new_refresh.access_token
            new_refresh["br"] = branch_id
            new_access["br"] = branch_id
            return Response({"access": str(new_access), "refresh": str(new_refresh), "br": branch_id})
        # regular user: must have active membership
        from apps.branch.models import BranchMembership
        if not Branch.objects.filter(id=branch_id, status="active").exists():
            return Response({"detail": "Branch inactive or removed"}, status=status.HTTP_400_BAD_REQUEST)
        mem = BranchMembership.objects.filter(user_id=user.id, branch_id=branch_id).first()
        if not mem:
            return Response({"detail": "Membership not found"}, status=status.HTTP_403_FORBIDDEN)
        new_refresh = RefreshToken.for_user(user)
        new_access = new_refresh.access_token
        new_refresh["br"] = branch_id
        new_refresh["br_role"] = mem.role
        new_access["br"] = branch_id
        new_access["br_role"] = mem.role
        return Response({
            "access": str(new_access),
            "refresh": str(new_refresh),
            "br": branch_id,
            "br_role": mem.role,
        })

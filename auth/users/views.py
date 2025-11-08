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
    RequestOTPSerializer,
    VerifyOTPSerializer,
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


class RequestOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=RequestOTPSerializer, responses={200: dict}, summary="(Legacy) Request OTP code")
    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone_number"]
        try:
            result = OTPService.request_code(phone)
            return Response({"detail": "OTP sent", **result}, status=status.HTTP_200_OK)
        except OTPError as e:
            return Response({"detail": str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except Exception:
            logger.exception("OTP request failure")
            return Response({"detail": "Failed to process OTP request"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=VerifyOTPSerializer, responses={200: dict}, summary="(Legacy) Verify OTP and get JWT")
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone_number"]
        code = serializer.validated_data["code"]

        try:
            ok = OTPService.verify_code(phone, code)
            if not ok:
                return Response({"detail": "Invalid or expired code"}, status=status.HTTP_400_BAD_REQUEST)

            user, _ = User.objects.get_or_create(phone_number=phone, defaults={"is_active": True})
            if not user.is_active:
                return Response({"detail": "User is inactive"}, status=status.HTTP_403_FORBIDDEN)

            refresh = RefreshToken.for_user(user)
            data = {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception:
            logger.exception("OTP verify failure")
            return Response({"detail": "Failed to verify code"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserSerializer, summary="Get current user")
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class RefreshTokenView(TokenRefreshView):
    permission_classes = [AllowAny]
    @extend_schema(summary="Refresh JWT token (preserves branch scope if present)")
    def post(self, request, *args, **kwargs):
        from rest_framework_simplejwt.serializers import TokenRefreshSerializer
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_str = serializer.validated_data.get("refresh") or request.data.get("refresh")
        try:
            token = RefreshToken(refresh_str)
        except Exception:
            return Response({"detail": "Invalid refresh"}, status=status.HTTP_401_UNAUTHORIZED)
        br = token.get("br")
        br_role = token.get("br_role")
        if br:
            try:
                user = User.objects.get(id=token["user_id"])  # type: ignore
            except Exception:
                return Response({"detail": "Invalid user"}, status=status.HTTP_401_UNAUTHORIZED)
            if not (user.is_superuser or user.is_staff):
                from apps.branch.models import Branch
                from auth.users.models import UserBranch
                if not Branch.objects.filter(id=br, status="active").exists():
                    return Response({"detail": "Branch inactive or removed"}, status=status.HTTP_401_UNAUTHORIZED)
                if not UserBranch.objects.filter(user_id=user.id, branch_id=br).exists():
                    return Response({"detail": "Membership revoked"}, status=status.HTTP_401_UNAUTHORIZED)
        access = token.access_token
        if br:
            access["br"] = br
            if br_role:
                access["br_role"] = br_role
        return Response({"access": str(access), "refresh": str(token)})


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
        # Super/admin global by default; can request scoped if branch_id provided
        if user.is_superuser or user.is_staff:
            if branch_id:
                from apps.branch.models import Branch
                try:
                    b = Branch.objects.get(id=branch_id, status="active")
                except Branch.DoesNotExist:
                    return Response({"detail": "Branch not active or not found"}, status=status.HTTP_400_BAD_REQUEST)
                refresh = RefreshToken.for_user(user)
                access = refresh.access_token
                refresh["br"] = str(b.id)
                access["br"] = str(b.id)
                return Response({
                    "access": str(access),
                    "refresh": str(refresh),
                    "user": UserSerializer(user).data,
                    "br": str(b.id),
                })
            refresh = RefreshToken.for_user(user)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            })

        # Non-admin: require active branch membership
        from auth.users.models import UserBranch
        qs = UserBranch.objects.select_related("branch").filter(user_id=user.id, branch__status="active")
        memberships = list(qs)
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
            data = [BranchMembershipSerializer.from_userbranch(m) for m in memberships]
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
        from auth.users.models import UserBranch
        qs = (
            UserBranch.objects
            .select_related("branch")
            .filter(user_id=request.user.id)
            .order_by("branch__name")
        )
        data = [BranchMembershipSerializer.from_userbranch(m) for m in qs]
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
        from auth.users.models import UserBranch
        if not Branch.objects.filter(id=branch_id, status="active").exists():
            return Response({"detail": "Branch inactive or removed"}, status=status.HTTP_400_BAD_REQUEST)
        mem = UserBranch.objects.filter(user_id=user.id, branch_id=branch_id).first()
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

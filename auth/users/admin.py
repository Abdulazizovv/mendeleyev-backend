from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django import forms
from django.core.exceptions import ValidationError
from .models import User, UserBranch
from auth.profiles.models import Profile


class UserCreateForm(forms.ModelForm):
	password1 = forms.CharField(label="Parol", widget=forms.PasswordInput, required=False, help_text="Agar hozir parol bermasangiz foydalanuvchi 'NEEDS_PASSWORD' holatida qoladi.")
	password2 = forms.CharField(label="Parol tasdiqlash", widget=forms.PasswordInput, required=False)

	class Meta:
		model = User
		fields = ["phone_number", "first_name", "last_name", "email", "is_active", "is_staff", "is_superuser"]

	def clean(self):
		cleaned = super().clean()
		p1 = cleaned.get("password1")
		p2 = cleaned.get("password2")
		if p1 or p2:
			if p1 != p2:
				raise ValidationError("Parollar mos emas")
		return cleaned

	def save(self, commit=True):
		user: User = super().save(commit=False)
		p1 = self.cleaned_data.get("password1")
		if p1:
			user.set_password(p1)
			user.phone_verified = True  # Agar admin parol qo'ysa, telefonni tasdiqlangan deb belgilashi mumkin.
		else:
			user.set_unusable_password()
			user.phone_verified = False
		if commit:
			user.save()
		return user


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
	model = User
	ordering = ("-date_joined",)
	list_display = ("phone_number", "first_name", "last_name", "is_staff", "is_active", "phone_verified", "date_joined")
	list_filter = ("is_staff", "is_superuser", "is_active")
	search_fields = ("phone_number", "first_name", "last_name", "email")
	readonly_fields = ("last_login", "date_joined", "created_at", "updated_at")

	fieldsets = (
		(None, {"fields": ("phone_number", "password")}),
		("Personal info", {"fields": ("first_name", "last_name", "email")} ),
		("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "phone_verified", "groups", "user_permissions")} ),
	("Important dates", {"fields": ("last_login", "date_joined", "created_at", "updated_at")} ),
	)

	add_fieldsets = (
		(
			None,
			{
				"classes": ("wide",),
				"fields": ("phone_number", "first_name", "last_name", "email", "password1", "password2", "is_active", "is_staff", "is_superuser"),
			},
		),
	)

	add_form = UserCreateForm

	def get_fieldsets(self, request, obj=None):
		if not obj:
			return self.add_fieldsets
		return super().get_fieldsets(request, obj)

	def save_model(self, request, obj, form, change):  # ensure auth state integrity
		if change:
			# If password cleared manually (unlikely via admin), keep unusable
			if not obj.has_usable_password():
				obj.phone_verified = False
		obj.save()

	class MembershipInline(admin.TabularInline):
		model = UserBranch
		extra = 0
		autocomplete_fields = ("branch",)
		fields = ("branch", "role", "title", "created_at", "updated_at")
		readonly_fields = ("created_at", "updated_at")

	class ProfileInline(admin.StackedInline):
		model = Profile
		can_delete = False
		extra = 0
		fields = ("avatar", "date_of_birth", "gender", "language", "timezone", "bio", "address", "socials")

	inlines = [ProfileInline, MembershipInline]

@admin.register(UserBranch)
class UserBranchAdmin(admin.ModelAdmin):
	list_display = ("user", "branch", "role", "title", "created_at")
	list_filter = ("role",)
	search_fields = ("user__phone_number", "branch__name", "title")
	autocomplete_fields = ("user", "branch")


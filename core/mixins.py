"""EduTrack Enterprise Base View Mixins and Optimization Protocols."""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied

class EduTrackQueryOptimizationMixin:
    """Automatically applies select_related and prefetch_related hints."""
    select_related_fields = []
    prefetch_related_fields = []

    def get_queryset(self):
        qs = super().get_queryset()
        if self.select_related_fields:
            qs = qs.select_related(*self.select_related_fields)
        if self.prefetch_related_fields:
            qs = qs.prefetch_related(*self.prefetch_related_fields)
        return qs

class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Enforces granular institutional role authorizations."""
    allowed_roles = []

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        if self.request.user.is_superuser:
            return True
        user_roles = getattr(self.request.user, "roles", [])
        return any(role in self.allowed_roles for role in user_roles)

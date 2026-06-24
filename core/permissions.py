from rest_framework import permissions


def get_farmer_profile(user):
    if not user or not user.is_authenticated:
        return None
    try:
        return user.farmerprofile
    except Exception:
        return None


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_staff


class IsFarmerOwnerOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and (
            request.user.is_staff or get_farmer_profile(request.user) is not None
        )

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_staff:
            return True
        farmer = get_farmer_profile(request.user)
        if farmer is None:
            return False
        owner = getattr(obj, "farmer", None)
        if owner is None and hasattr(obj, "product"):
            owner = getattr(obj.product, "farmer", None)
        return owner == farmer


class IsOrderParticipantOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        if obj.buyer_id == request.user.id:
            return True
        farmer = get_farmer_profile(request.user)
        if farmer is None:
            return False
        return obj.items.filter(product_batch__product__farmer=farmer).exists()


class IsSubsidyOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        farmer = get_farmer_profile(request.user)
        return farmer is not None and obj.farmer_id == farmer.id

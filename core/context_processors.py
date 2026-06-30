"""Inject role-based template context so a single template works for all roles."""


def role_context(request):
    """Determine the appropriate base template based on user role."""
    ctx = {'base_template': 'base.html'}
    if not request.user.is_authenticated:
        return ctx

    if request.user.is_staff:
        ctx['base_template'] = 'admin/panel_base.html'
        ctx['is_admin'] = True
    elif hasattr(request.user, 'farmerprofile'):
        ctx['base_template'] = 'farmer/base.html'
        ctx['is_farmer'] = True

    return ctx

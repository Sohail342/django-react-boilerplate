from django.urls import path

from apps.admin_panel.api.admin_views import dashboard
from apps.admin_panel.api.auth_views import (
    legacy_login_redirect,
    login_view,
    logout_view,
)
from apps.admin_panel.api.group_views import (
    group_create,
    group_delete,
    group_edit,
    group_list,
)
from apps.admin_panel.api.user_views import (
    user_create,
    user_delete,
    user_edit,
    user_list,
)

urlpatterns = [
    path("", login_view, name="login"),
    path("admin/login/", legacy_login_redirect),
    path("logout/", logout_view, name="logout"),
    path("admin/", dashboard, name="admin_dashboard"),
    path("admin/users/", user_list, name="admin_users"),
    path("admin/users/create/", user_create, name="admin_user_create"),
    path("admin/users/<int:user_id>/edit/", user_edit, name="admin_user_edit"),
    path("admin/users/<int:user_id>/delete/", user_delete, name="admin_user_delete"),
    path("admin/groups/", group_list, name="admin_groups"),
    path("admin/groups/create/", group_create, name="admin_group_create"),
    path("admin/groups/<int:group_id>/edit/", group_edit, name="admin_group_edit"),
    path(
        "admin/groups/<int:group_id>/delete/", group_delete, name="admin_group_delete"
    ),
]

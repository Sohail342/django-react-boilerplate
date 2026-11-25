from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from apps.admin_panel.tests.factories import make_user
from apps.budget.domain import policies
from apps.budget.models import BudgetRequest
from apps.users.models import User


class RoleHomeTests(TestCase):
    def test_each_role_has_its_own_home(self):
        client = make_user("client", role=User.Roles.CLIENT)
        manager = make_user("manager", role=User.Roles.MANAGER)
        admin = make_user("admin", role=User.Roles.ADMIN)

        self.assertEqual(policies.role_home(client)["route"], "budget_requests")
        self.assertEqual(policies.role_home(manager)["route"], "budget_reviews")
        self.assertEqual(policies.role_home(admin)["route"], "budget_admin")
        self.assertEqual(policies.role_home_url(client), "/requests/")
        self.assertEqual(policies.role_home_url(manager), "/reviews/")
        self.assertEqual(policies.role_home_url(admin), "/budget/")


class BudgetPolicyTests(TestCase):
    def setUp(self):
        self.client_user = make_user("client", role=User.Roles.CLIENT)
        self.other = make_user("other", role=User.Roles.CLIENT)
        self.manager = make_user("manager", role=User.Roles.MANAGER)
        self.admin = make_user("admin", role=User.Roles.ADMIN)
        self.pending = BudgetRequest(
            requester_id=self.client_user.pk, status=BudgetRequest.Status.PENDING
        )
        self.approved = BudgetRequest(
            requester_id=self.client_user.pk, status=BudgetRequest.Status.APPROVED
        )

    def test_only_the_client_who_owns_a_pending_request_can_change_it(self):
        self.assertTrue(policies.can_create(self.client_user))
        self.assertFalse(policies.can_create(self.manager))
        self.assertFalse(policies.can_create(self.admin))
        self.assertTrue(policies.can_view(self.client_user, self.pending))
        self.assertFalse(policies.can_view(self.other, self.pending))
        self.assertTrue(policies.can_update(self.client_user, self.pending))
        self.assertTrue(policies.can_withdraw(self.client_user, self.pending))
        self.assertFalse(policies.can_update(self.client_user, self.approved))
        self.assertFalse(policies.can_withdraw(self.client_user, self.approved))
        self.assertFalse(policies.can_update(self.manager, self.pending))

    def test_managers_and_admins_decide_only_while_pending(self):
        self.assertTrue(policies.can_decide(self.manager, self.pending))
        self.assertTrue(policies.can_decide(self.admin, self.pending))
        self.assertFalse(policies.can_decide(self.manager, self.approved))
        self.assertFalse(policies.can_decide(self.client_user, self.pending))
        self.assertTrue(policies.can_review(self.manager))
        self.assertTrue(policies.can_view(self.manager, self.pending))
        self.assertTrue(policies.can_view(self.admin, self.approved))

    def test_only_admins_can_delete(self):
        self.assertTrue(policies.can_delete(self.admin))
        self.assertFalse(policies.can_delete(self.manager))
        self.assertFalse(policies.can_delete(self.client_user))
        self.assertFalse(policies.can_view_admin(self.manager))
        self.assertFalse(policies.can_list_own(AnonymousUser()))

    def test_only_admins_can_read_audit_logs(self):
        self.assertTrue(policies.can_read_audit(self.admin))
        self.assertFalse(policies.can_read_audit(self.manager))
        self.assertFalse(policies.can_read_audit(self.client_user))
        self.assertFalse(policies.can_read_audit(AnonymousUser()))

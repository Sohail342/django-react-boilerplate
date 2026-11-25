import uuid
from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import TestCase

from apps.admin_panel.tests.factories import make_user
from apps.budget.dto.requests import DecisionInputDTO, RequestFormInputDTO
from apps.budget.models import AuditLog, BudgetRequest
from apps.budget.services import pages as page_services
from apps.budget.services import requests as request_services
from apps.users.models import User


def form(**overrides) -> RequestFormInputDTO:
    values = {
        "title": "New laptops",
        "amount": "1500.50",
        "justification": "The team needs replacements.",
    }
    values.update(overrides)
    return RequestFormInputDTO(**values)


def decision(status, note="") -> DecisionInputDTO:
    return DecisionInputDTO(status=status, reviewer_feedback=note)


class BudgetServiceTests(TestCase):
    def setUp(self):
        self.client_user = make_user("client", role=User.Roles.CLIENT)
        self.other = make_user("other", role=User.Roles.CLIENT)
        self.manager = make_user("manager", role=User.Roles.MANAGER)
        self.admin = make_user("admin", role=User.Roles.ADMIN)

    def test_client_sees_only_their_requests(self):
        own = request_services.create_request(actor=self.client_user, data=form())
        request_services.create_request(
            actor=self.other, data=form(title="Other request")
        )
        page = page_services.get_my_requests_page(actor=self.client_user, page=1)
        self.assertEqual([row["id"] for row in page["requests"]], [own.request_id])
        with self.assertRaises(PermissionDenied):
            page_services.get_my_requests_page(actor=self.manager, page=1)

    def test_client_can_edit_and_withdraw_only_while_pending(self):
        created = request_services.create_request(actor=self.client_user, data=form())
        updated = request_services.update_request(
            actor=self.client_user,
            request_id=created.request_id,
            data=form(title="Updated laptops", amount="20"),
        )
        self.assertTrue(updated.success)
        stored = BudgetRequest.objects.get(pk=created.request_id)
        self.assertEqual(stored.title, "Updated laptops")
        self.assertEqual(stored.amount, Decimal("20.00"))
        self.assertEqual(stored.currency, "USD")
        self.assertEqual(stored.status, BudgetRequest.Status.PENDING)

        request_services.decide_request(
            actor=self.manager,
            request_id=created.request_id,
            data=decision(BudgetRequest.Status.APPROVED, "Looks good"),
        )
        with self.assertRaises(PermissionDenied):
            request_services.update_request(
                actor=self.client_user,
                request_id=created.request_id,
                data=form(),
            )
        with self.assertRaises(PermissionDenied):
            request_services.withdraw_request(
                actor=self.client_user, request_id=created.request_id
            )

    def test_invalid_amount_is_rejected(self):
        result = request_services.create_request(
            actor=self.client_user, data=form(amount="0")
        )
        self.assertFalse(result.success)
        self.assertIn("amount", result.errors)
        self.assertEqual(BudgetRequest.objects.count(), 0)

    def test_reject_requires_a_note_and_a_decision_is_final(self):
        created = request_services.create_request(actor=self.client_user, data=form())
        rejected = request_services.decide_request(
            actor=self.manager,
            request_id=created.request_id,
            data=decision(BudgetRequest.Status.REJECTED, "   "),
        )
        self.assertFalse(rejected.success)
        self.assertEqual(
            BudgetRequest.objects.get(pk=created.request_id).status,
            BudgetRequest.Status.PENDING,
        )

        request_services.decide_request(
            actor=self.manager,
            request_id=created.request_id,
            data=decision(BudgetRequest.Status.REJECTED, "Over budget"),
        )
        stored = BudgetRequest.objects.get(pk=created.request_id)
        self.assertEqual(stored.status, BudgetRequest.Status.REJECTED)
        self.assertEqual(stored.reviewer, self.manager)
        self.assertEqual(stored.reviewer_feedback, "Over budget")
        self.assertIsNotNone(stored.reviewed_at)

        with self.assertRaises(PermissionDenied):
            request_services.decide_request(
                actor=self.admin,
                request_id=created.request_id,
                data=decision(BudgetRequest.Status.APPROVED, "Changed my mind"),
            )

    def test_manager_cannot_delete_and_admin_totals_include_both_statuses(self):
        first = request_services.create_request(
            actor=self.client_user, data=form(amount="100.00")
        )
        second = request_services.create_request(
            actor=self.other, data=form(title="Travel", amount="40.25")
        )
        request_services.decide_request(
            actor=self.admin,
            request_id=first.request_id,
            data=decision(BudgetRequest.Status.APPROVED),
        )

        with self.assertRaises(PermissionDenied):
            request_services.delete_request(
                actor=self.manager, request_id=second.request_id
            )

        page = page_services.get_admin_page(actor=self.admin, page=1, activity_page=1)
        self.assertEqual(page["totals"]["pending"], "40.25")
        self.assertEqual(page["totals"]["approved"], "100.00")
        self.assertEqual(len(page["requests"]), 2)

        request_services.delete_request(actor=self.admin, request_id=second.request_id)
        self.assertFalse(BudgetRequest.objects.filter(pk=second.request_id).exists())

    def test_hidden_request_is_a_404(self):
        created = request_services.create_request(actor=self.client_user, data=form())
        with self.assertRaises(Http404):
            page_services.get_edit_page(actor=self.other, request_id=created.request_id)


class AuditTrailTests(TestCase):
    def setUp(self):
        self.client_user = make_user("client", role=User.Roles.CLIENT)
        self.manager = make_user("manager", role=User.Roles.MANAGER)
        self.admin = make_user("admin", role=User.Roles.ADMIN)

    def test_successful_changes_are_recorded_and_only_admins_see_them(self):
        created = request_services.create_request(actor=self.client_user, data=form())
        created_log = AuditLog.objects.get(action="created")
        self.assertEqual(created_log.actor, self.client_user)
        self.assertIsNone(created_log.old_values)
        self.assertEqual(created_log.new_values["title"], "New laptops")
        self.assertEqual(created_log.new_values["requester_id"], self.client_user.pk)
        self.assertEqual(created_log.entity_id, uuid.UUID(created.request_id))

        request_services.update_request(
            actor=self.client_user,
            request_id=created.request_id,
            data=form(title="Updated laptops", amount="20"),
        )
        updated_log = AuditLog.objects.get(action="updated")
        self.assertEqual(updated_log.old_values["title"], "New laptops")
        self.assertEqual(updated_log.new_values["title"], "Updated laptops")
        self.assertEqual(updated_log.new_values["amount"], "20.00")

        request_services.decide_request(
            actor=self.manager,
            request_id=created.request_id,
            data=decision(BudgetRequest.Status.APPROVED, "Looks good"),
        )
        approved_log = AuditLog.objects.get(action="approved")
        self.assertEqual(approved_log.actor, self.manager)
        self.assertEqual(approved_log.old_values, {"status": "pending"})
        self.assertEqual(approved_log.new_values["reviewer_id"], self.manager.pk)
        self.assertEqual(approved_log.new_values["reviewer_feedback"], "Looks good")

        page = page_services.get_admin_page(actor=self.admin, page=1, activity_page=1)
        self.assertEqual(
            [row["action"] for row in page["activity"]],
            ["approved", "updated", "created"],
        )
        self.assertEqual(page["activity"][0]["actor"]["username"], "manager")
        updated = next(row for row in page["activity"] if row["action"] == "updated")
        updated_changes = {change["label"]: change for change in updated["changes"]}
        self.assertEqual(updated_changes["Title"]["before"], "New laptops")
        self.assertEqual(updated_changes["Title"]["after"], "Updated laptops")
        self.assertEqual(updated_changes["Amount"]["before"], "USD 1500.50")
        self.assertEqual(updated_changes["Amount"]["after"], "USD 20.00")
        self.assertFalse(updated_changes["Justification"]["changed"])
        approved_changes = {
            change["label"]: change for change in page["activity"][0]["changes"]
        }
        self.assertEqual(approved_changes["Status"]["before"], "Pending")
        self.assertEqual(approved_changes["Status"]["after"], "Approved")
        self.assertEqual(approved_changes["Reviewer"]["after"], "manager")
        self.assertEqual(approved_changes["Reviewer note"]["after"], "Looks good")
        reviews = page_services.get_reviews_page(
            actor=self.manager, page=1, history_page=1
        )
        self.assertNotIn("activity", reviews)
        with self.assertRaises(PermissionDenied):
            page_services.get_admin_page(actor=self.manager, page=1, activity_page=1)

    def test_failed_checks_and_removals(self):
        request_services.create_request(actor=self.client_user, data=form(amount="0"))
        self.assertEqual(AuditLog.objects.count(), 0)

        created = request_services.create_request(actor=self.client_user, data=form())
        rejected = request_services.decide_request(
            actor=self.manager,
            request_id=created.request_id,
            data=decision(BudgetRequest.Status.REJECTED, " "),
        )
        self.assertFalse(rejected.success)
        self.assertFalse(AuditLog.objects.filter(action="rejected").exists())

        request_services.withdraw_request(
            actor=self.client_user, request_id=created.request_id
        )
        withdrawn = AuditLog.objects.get(action="withdrawn")
        self.assertEqual(withdrawn.actor, self.client_user)
        self.assertEqual(withdrawn.old_values["title"], "New laptops")
        self.assertIsNone(withdrawn.new_values)
        self.assertFalse(BudgetRequest.objects.filter(pk=created.request_id).exists())

        other = request_services.create_request(
            actor=self.client_user, data=form(title="Travel")
        )
        request_services.delete_request(actor=self.admin, request_id=other.request_id)
        deleted = AuditLog.objects.get(action="deleted")
        self.assertEqual(deleted.actor, self.admin)
        self.assertEqual(deleted.old_values["title"], "Travel")
        self.assertIsNone(deleted.new_values)
        self.assertTrue(AuditLog.objects.filter(entity_id=other.request_id).exists())

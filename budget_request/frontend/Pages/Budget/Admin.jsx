import * as React from "react"
import { Head, router } from "@inertiajs/react"
import { Button } from "@/Components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/Components/ui/card"
import { DataTablePagination } from "@/Components/admin/DataTablePagination"
import { DeleteConfirmDialog } from "@/Components/admin/DeleteConfirmDialog"
import { PageHeader } from "@/Components/admin/PageHeader"
import { ActivityTable } from "@/Components/budget/ActivityTable"
import { DecisionDialog } from "@/Components/budget/DecisionDialog"
import { RequestTable } from "@/Components/budget/RequestTable"
import { useRoute } from "@/composables/useRoute"
import { AdminLayout } from "@/Layouts/AdminLayout"
import { formatMoney } from "@/lib/money"

export default function BudgetAdmin({ totals, requests, pagination, activity, activity_pagination }) {
  const route = useRoute()
  const [decision, setDecision] = React.useState(null)
  const [deciding, setDeciding] = React.useState(false)
  const [deleteTarget, setDeleteTarget] = React.useState(null)
  const [deleting, setDeleting] = React.useState(false)

  const confirmDecision = (note) => {
    router.post(
      route("budget_request_decide", { request_id: decision.id }),
      { status: decision.status, reviewer_feedback: note },
      {
        preserveScroll: true,
        onStart: () => setDeciding(true),
        onFinish: () => {
          setDeciding(false)
          setDecision(null)
        },
      }
    )
  }

  const confirmDelete = () => {
    router.post(route("budget_request_delete", { request_id: deleteTarget.id }), {}, {
      preserveScroll: true,
      onStart: () => setDeleting(true),
      onFinish: () => {
        setDeleting(false)
        setDeleteTarget(null)
      },
    })
  }

  return (
    <>
      <Head title="Budget summary" />
      <PageHeader
        title="Budget summary"
        description="Organization-wide funding totals and every request on record."
      />

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Pending funding</CardDescription>
            <CardTitle className="text-3xl font-semibold tabular-nums">
              {formatMoney(totals.pending, totals.currency)}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">Requests still waiting for a decision.</CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Approved funding</CardDescription>
            <CardTitle className="text-3xl font-semibold tabular-nums">
              {formatMoney(totals.approved, totals.currency)}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">Amount already approved.</CardContent>
        </Card>
      </div>

      <RequestTable
        requests={requests}
        showRequester
        emptyTitle="No requests"
        emptyText="Budget requests from the organization will appear here."
        renderActions={(item) => (
          <div className="flex justify-end gap-2">
            {item.can_decide && (
              <>
                <Button size="sm" onClick={() => setDecision({ ...item, status: "approved" })}>
                  Approve
                </Button>
                <Button size="sm" variant="outline" onClick={() => setDecision({ ...item, status: "rejected" })}>
                  Reject
                </Button>
              </>
            )}
            {item.can_delete && (
              <Button size="sm" variant="outline" onClick={() => setDeleteTarget(item)}>
                Delete
              </Button>
            )}
          </div>
        )}
      />
      <DataTablePagination
        pagination={pagination}
        itemLabel="requests"
        buildUrl={(page) =>
          route("budget_admin", {}, { page, activity_page: activity_pagination.page })
        }
      />

      <section className="grid gap-3">
        <h2 className="text-sm font-medium">Activity</h2>
        <ActivityTable activity={activity} />
        <DataTablePagination
          pagination={activity_pagination}
          itemLabel="events"
          buildUrl={(page) =>
            route("budget_admin", {}, { page: pagination.page, activity_page: page })
          }
        />
      </section>

      <DecisionDialog
        open={Boolean(decision)}
        mode={decision?.status}
        title={decision?.title ?? ""}
        processing={deciding}
        onOpenChange={(open) => {
          if (!open) setDecision(null)
        }}
        onConfirm={confirmDecision}
      />
      <DeleteConfirmDialog
        open={Boolean(deleteTarget)}
        onOpenChange={(open) => {
          if (!open) setDeleteTarget(null)
        }}
        onConfirm={confirmDelete}
        processing={deleting}
        title="Delete request"
        description={
          deleteTarget ? `Permanently delete "${deleteTarget.title}"? This cannot be undone.` : ""
        }
      />
    </>
  )
}

BudgetAdmin.layout = (page) => <AdminLayout>{page}</AdminLayout>

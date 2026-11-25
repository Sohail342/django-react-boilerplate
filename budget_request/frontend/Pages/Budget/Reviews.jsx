import * as React from "react"
import { Head, router } from "@inertiajs/react"
import { Button } from "@/Components/ui/button"
import { DataTablePagination } from "@/Components/admin/DataTablePagination"
import { PageHeader } from "@/Components/admin/PageHeader"
import { DecisionDialog } from "@/Components/budget/DecisionDialog"
import { RequestTable } from "@/Components/budget/RequestTable"
import { useRoute } from "@/composables/useRoute"
import { AdminLayout } from "@/Layouts/AdminLayout"

export default function Reviews({ pending, pending_pagination, history, history_pagination }) {
  const route = useRoute()
  const [decision, setDecision] = React.useState(null)
  const [deciding, setDeciding] = React.useState(false)

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

  const reviewActions = (item) =>
    item.can_decide ? (
      <div className="flex justify-end gap-2">
        <Button size="sm" onClick={() => setDecision({ ...item, status: "approved" })}>
          Approve
        </Button>
        <Button size="sm" variant="outline" onClick={() => setDecision({ ...item, status: "rejected" })}>
          Reject
        </Button>
      </div>
    ) : null

  return (
    <>
      <Head title="Reviews" />
      <PageHeader
        title="Reviews"
        description="Approve or reject requests that are waiting, and look back at earlier decisions."
      />

      <section className="grid gap-3">
        <h2 className="text-sm font-medium">Awaiting decision</h2>
        <RequestTable
          requests={pending}
          showRequester
          emptyTitle="Nothing waiting"
          emptyText="Pending requests will show up here."
          renderActions={reviewActions}
        />
        <DataTablePagination
          pagination={pending_pagination}
          itemLabel="pending requests"
          buildUrl={(page) =>
            route("budget_reviews", {}, { page, history_page: history_pagination.page })
          }
        />
      </section>

      <section className="grid gap-3">
        <h2 className="text-sm font-medium">History</h2>
        <RequestTable
          requests={history}
          showRequester
          emptyTitle="No decisions yet"
          emptyText="Approved and rejected requests will be listed here."
        />
        <DataTablePagination
          pagination={history_pagination}
          itemLabel="decisions"
          buildUrl={(page) =>
            route("budget_reviews", {}, { page: pending_pagination.page, history_page: page })
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
    </>
  )
}

Reviews.layout = (page) => <AdminLayout>{page}</AdminLayout>

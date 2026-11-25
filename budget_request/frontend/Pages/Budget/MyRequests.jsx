import * as React from "react"
import { Head, Link, router } from "@inertiajs/react"
import { Plus } from "lucide-react"
import { Button } from "@/Components/ui/button"
import { DataTablePagination } from "@/Components/admin/DataTablePagination"
import { DeleteConfirmDialog } from "@/Components/admin/DeleteConfirmDialog"
import { PageHeader } from "@/Components/admin/PageHeader"
import { RequestTable } from "@/Components/budget/RequestTable"
import { useRoute } from "@/composables/useRoute"
import { AdminLayout } from "@/Layouts/AdminLayout"

export default function MyRequests({ requests, pagination, can }) {
  const route = useRoute()
  const [withdrawTarget, setWithdrawTarget] = React.useState(null)
  const [withdrawing, setWithdrawing] = React.useState(false)

  const confirmWithdraw = () => {
    router.post(route("budget_request_withdraw", { request_id: withdrawTarget.id }), {}, {
      preserveScroll: true,
      onStart: () => setWithdrawing(true),
      onFinish: () => {
        setWithdrawing(false)
        setWithdrawTarget(null)
      },
    })
  }

  return (
    <>
      <Head title="My requests" />
      <PageHeader title="My requests" description="Track the requests you have submitted.">
        {can.create && (
          <Button asChild>
            <Link href={route("budget_request_create")}>
              <Plus />
              New request
            </Link>
          </Button>
        )}
      </PageHeader>

      <RequestTable
        requests={requests}
        emptyTitle="No requests yet"
        emptyText="Submit a request when you need funding or resources."
        renderActions={(item) =>
          item.can_update ? (
            <div className="flex justify-end gap-2">
              <Button variant="outline" size="sm" asChild>
                <Link href={route("budget_request_edit", { request_id: item.id })}>Edit</Link>
              </Button>
              <Button variant="outline" size="sm" onClick={() => setWithdrawTarget(item)}>
                Withdraw
              </Button>
            </div>
          ) : null
        }
      />
      <DataTablePagination
        pagination={pagination}
        itemLabel="requests"
        buildUrl={(page) => route("budget_requests", {}, { page })}
      />

      <DeleteConfirmDialog
        open={Boolean(withdrawTarget)}
        onOpenChange={(open) => {
          if (!open) setWithdrawTarget(null)
        }}
        onConfirm={confirmWithdraw}
        processing={withdrawing}
        title="Withdraw request"
        description={
          withdrawTarget
            ? `Withdraw "${withdrawTarget.title}"? This permanently removes the pending request.`
            : ""
        }
      />
    </>
  )
}

MyRequests.layout = (page) => <AdminLayout>{page}</AdminLayout>

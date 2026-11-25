import { Head, useForm } from "@inertiajs/react"
import { ErrorSummary } from "@/Components/admin/ErrorSummary"
import { PageHeader } from "@/Components/admin/PageHeader"
import { RequestForm } from "@/Components/budget/RequestForm"
import { useRoute } from "@/composables/useRoute"
import { AdminLayout } from "@/Layouts/AdminLayout"

export default function BudgetForm({ request, form: initialForm, errors = {} }) {
  const route = useRoute()
  const form = useForm(initialForm)
  const isEdit = Boolean(request)

  return (
    <>
      <Head title={isEdit ? "Edit request" : "New request"} />
      <PageHeader
        title={isEdit ? "Edit request" : "New request"}
        description={isEdit ? "Update this request while it is still pending." : "Submit a funding request for review."}
      />
      <ErrorSummary errors={errors} className="max-w-3xl" />
      <RequestForm
        data={form.data}
        setData={form.setData}
        errors={errors}
        processing={form.processing}
        onSubmit={() =>
          isEdit
            ? form.post(route("budget_request_edit", { request_id: request.id }))
            : form.post(route("budget_request_create"))
        }
        cancelHref={route("budget_requests")}
        isEdit={isEdit}
      />
    </>
  )
}

BudgetForm.layout = (page) => (
  <AdminLayout breadcrumbs={[{ label: page.props.request ? "Edit request" : "New request" }]}>
    {page}
  </AdminLayout>
)

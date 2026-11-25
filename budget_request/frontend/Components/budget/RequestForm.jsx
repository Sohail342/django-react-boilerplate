import { Link } from "@inertiajs/react"
import { Loader2 } from "lucide-react"
import { Button } from "@/Components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/Components/ui/card"
import { Input } from "@/Components/ui/input"
import { Textarea } from "@/Components/ui/textarea"
import { FormField } from "@/Components/admin/FormField"
import { cn } from "@/lib/utils"

export function RequestForm({ data, setData, errors = {}, processing, onSubmit, cancelHref, isEdit }) {
  const invalid = (name) => (errors[name]?.length ? true : undefined)

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault()
        onSubmit()
      }}
      className="grid max-w-3xl gap-6"
    >
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Request details</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-5">
          <FormField label="Title" htmlFor="title" error={errors.title?.[0]} required>
            <Input
              id="title"
              value={data.title}
              onChange={(event) => setData("title", event.target.value)}
              aria-invalid={invalid("title")}
              className={cn(errors.title?.length && "border-destructive focus-visible:ring-destructive")}
            />
          </FormField>
          <FormField label="Amount" htmlFor="amount" error={errors.amount?.[0]} required description="USD">
            <Input
              id="amount"
              inputMode="decimal"
              value={data.amount}
              onChange={(event) => setData("amount", event.target.value)}
              aria-invalid={invalid("amount")}
              className={cn(errors.amount?.length && "border-destructive focus-visible:ring-destructive")}
            />
          </FormField>
          <FormField
            label="Business justification"
            htmlFor="justification"
            error={errors.justification?.[0]}
            required
          >
            <Textarea
              id="justification"
              value={data.justification}
              onChange={(event) => setData("justification", event.target.value)}
              aria-invalid={invalid("justification")}
              className={cn(errors.justification?.length && "border-destructive focus-visible:ring-destructive")}
            />
          </FormField>
        </CardContent>
        <CardFooter className="justify-end gap-2 border-t px-6 py-4">
          <Button variant="outline" asChild>
            <Link href={cancelHref}>Cancel</Link>
          </Button>
          <Button type="submit" disabled={processing}>
            {processing && <Loader2 className="animate-spin" />}
            {isEdit ? "Save changes" : "Submit request"}
          </Button>
        </CardFooter>
      </Card>
    </form>
  )
}

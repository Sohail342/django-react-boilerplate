import { Head, Link, usePage } from "@inertiajs/react"
import { Button } from "@/Components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/Components/ui/card"
import { AdminLayout } from "@/Layouts/AdminLayout"

function ForbiddenBody({ message, home_url, home_label }) {
  return (
    <div className="mx-auto flex w-full max-w-lg flex-1 items-center py-12">
      <Card className="w-full">
        <CardHeader>
          <CardTitle>You do not have access</CardTitle>
          <CardDescription>{message}</CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          This page is limited to another role. Use your own home to continue.
        </CardContent>
        <CardFooter>
          <Button asChild>
            <Link href={home_url}>{home_label}</Link>
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}

export default function Forbidden(props) {
  const { auth } = usePage().props
  return (
    <>
      <Head title="Access denied" />
      {auth?.user ? (
        <ForbiddenBody {...props} />
      ) : (
        <div className="flex min-h-screen items-center justify-center bg-background p-6">
          <ForbiddenBody {...props} />
        </div>
      )}
    </>
  )
}

Forbidden.layout = (page) => (page.props.auth?.user ? <AdminLayout>{page}</AdminLayout> : page)

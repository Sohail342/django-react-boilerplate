import { Badge } from "@/Components/ui/badge"
import { cn } from "@/lib/utils"

const STYLES = {
  pending: "border-amber-200 bg-amber-50 text-amber-900 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-100",
  approved:
    "border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-100",
  rejected: "border-red-200 bg-red-50 text-red-900 dark:border-red-900 dark:bg-red-950 dark:text-red-100",
}

const LABELS = {
  pending: "Pending",
  approved: "Approved",
  rejected: "Rejected",
}

export function StatusBadge({ status }) {
  return (
    <Badge variant="outline" className={cn("capitalize", STYLES[status])}>
      {LABELS[status] ?? status}
    </Badge>
  )
}

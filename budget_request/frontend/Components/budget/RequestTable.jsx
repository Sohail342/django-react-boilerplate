import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/Components/ui/table"
import { StatusBadge } from "@/Components/budget/StatusBadge"
import { formatRelativeTime } from "@/lib/date"
import { formatMoney } from "@/lib/money"

export function RequestTable({
  requests,
  showRequester = false,
  emptyTitle,
  emptyText,
  renderActions,
}) {
  const colSpan = 5 + (showRequester ? 1 : 0) + (renderActions ? 1 : 0)

  return (
    <div className="overflow-hidden rounded-lg border">
      <Table>
        <TableHeader className="bg-muted/50">
          <TableRow className="hover:bg-transparent">
            <TableHead>Request</TableHead>
            <TableHead>Amount</TableHead>
            <TableHead>Status</TableHead>
            {showRequester && <TableHead>Requester</TableHead>}
            <TableHead>Reviewer note</TableHead>
            <TableHead>Submitted</TableHead>
            {renderActions && (
              <TableHead className="w-40">
                <span className="sr-only">Actions</span>
              </TableHead>
            )}
          </TableRow>
        </TableHeader>
        <TableBody>
          {!requests.length && (
            <TableRow className="hover:bg-transparent">
              <TableCell colSpan={colSpan} className="h-32 text-center">
                <p className="font-medium">{emptyTitle}</p>
                {emptyText && <p className="mt-1 text-sm text-muted-foreground">{emptyText}</p>}
              </TableCell>
            </TableRow>
          )}
          {requests.map((item) => (
            <TableRow key={item.id}>
              <TableCell className="whitespace-normal">
                <p className="font-medium">{item.title}</p>
                <p className="max-w-sm truncate text-xs text-muted-foreground">{item.justification}</p>
              </TableCell>
              <TableCell>{formatMoney(item.amount, item.currency)}</TableCell>
              <TableCell>
                <StatusBadge status={item.status} />
              </TableCell>
              {showRequester && <TableCell>{item.requester?.name}</TableCell>}
              <TableCell className="max-w-xs whitespace-normal text-sm text-muted-foreground">
                {item.reviewer_feedback || "—"}
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {formatRelativeTime(item.created_at)}
              </TableCell>
              {renderActions && <TableCell>{renderActions(item)}</TableCell>}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

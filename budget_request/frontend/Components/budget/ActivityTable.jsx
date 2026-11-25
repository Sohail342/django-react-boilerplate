import * as React from "react"
import { Button } from "@/Components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/Components/ui/dialog"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/Components/ui/table"
import { formatRelativeTime } from "@/lib/date"

const ACTION_LABELS = {
  created: "Created",
  updated: "Updated",
  approved: "Approved",
  rejected: "Rejected",
  withdrawn: "Withdrawn",
  deleted: "Deleted",
}

function displayValue(value) {
  return value || "—"
}

export function ActivityTable({ activity }) {
  const [selected, setSelected] = React.useState(null)

  return (
    <>
      <div className="overflow-hidden rounded-lg border">
        <Table>
          <TableHeader className="bg-muted/50">
            <TableRow className="hover:bg-transparent">
              <TableHead>When</TableHead>
              <TableHead>Who</TableHead>
              <TableHead>Action</TableHead>
              <TableHead>Request</TableHead>
              <TableHead className="w-28">
                <span className="sr-only">Details</span>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {!activity.length && (
              <TableRow className="hover:bg-transparent">
                <TableCell colSpan={5} className="h-24 text-center">
                  <p className="font-medium">No activity yet</p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Submissions, edits, decisions, and deletions will be listed here.
                  </p>
                </TableCell>
              </TableRow>
            )}
            {activity.map((item) => (
              <TableRow key={item.id}>
                <TableCell className="text-sm text-muted-foreground">
                  {formatRelativeTime(item.created_at)}
                </TableCell>
                <TableCell>{item.actor?.name}</TableCell>
                <TableCell>{ACTION_LABELS[item.action] ?? item.action}</TableCell>
                <TableCell className="font-medium">{item.title || "—"}</TableCell>
                <TableCell>
                  <Button size="sm" variant="outline" onClick={() => setSelected(item)}>
                    Details
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      <ActivityDetailDialog
        item={selected}
        onOpenChange={(open) => {
          if (!open) setSelected(null)
        }}
      />
    </>
  )
}

function ActivityDetailDialog({ item, onOpenChange }) {
  const changes = item?.changes ?? []
  const action = ACTION_LABELS[item?.action] ?? "Activity"

  return (
    <Dialog open={Boolean(item)} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>
            {action}
            {item?.title ? ` · ${item.title}` : ""}
          </DialogTitle>
          <DialogDescription>
            {item?.actor?.name}
            {item?.created_at ? ` · ${formatRelativeTime(item.created_at)}` : ""}
          </DialogDescription>
        </DialogHeader>
        {!changes.length ? (
          <p className="text-sm text-muted-foreground">No field values were stored for this event.</p>
        ) : (
          <div className="max-h-[60vh] overflow-auto rounded-lg border">
            <Table>
              <TableHeader className="bg-muted/50">
                <TableRow className="hover:bg-transparent">
                  <TableHead className="w-36">Field</TableHead>
                  <TableHead>Before</TableHead>
                  <TableHead>After</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {changes.map((change) => (
                  <TableRow key={change.label} className={change.changed ? "bg-muted/40" : undefined}>
                    <TableCell className="align-top font-medium">{change.label}</TableCell>
                    <TableCell className="align-top whitespace-pre-wrap text-muted-foreground">
                      {displayValue(change.before)}
                    </TableCell>
                    <TableCell className="align-top whitespace-pre-wrap">{displayValue(change.after)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}

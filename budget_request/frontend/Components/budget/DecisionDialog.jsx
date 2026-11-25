import * as React from "react"
import { Button } from "@/Components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/Components/ui/dialog"
import { Textarea } from "@/Components/ui/textarea"
import { FormField } from "@/Components/admin/FormField"

export function DecisionDialog({ open, mode, title, processing, onOpenChange, onConfirm }) {
  const [note, setNote] = React.useState("")
  const rejecting = mode === "rejected"

  React.useEffect(() => {
    if (open) setNote("")
  }, [open, mode])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{rejecting ? "Reject request" : "Approve request"}</DialogTitle>
          <DialogDescription>
            {rejecting
              ? `A note is required to reject "${title}".`
              : `Add an optional note when approving "${title}".`}
          </DialogDescription>
        </DialogHeader>
        <FormField label="Reviewer note" htmlFor="reviewer_feedback" required={rejecting}>
          <Textarea
            id="reviewer_feedback"
            value={note}
            onChange={(event) => setNote(event.target.value)}
          />
        </FormField>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            variant={rejecting ? "destructive" : "default"}
            disabled={processing || (rejecting && !note.trim())}
            onClick={() => onConfirm(note.trim())}
          >
            {rejecting ? "Reject" : "Approve"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function formatMoney(amount, currency = "USD") {
  const value = Number(amount)
  if (!Number.isFinite(value)) return amount ?? ""
  try {
    return new Intl.NumberFormat(undefined, { style: "currency", currency }).format(value)
  } catch {
    return `${amount} ${currency}`
  }
}

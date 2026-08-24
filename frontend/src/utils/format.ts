export function formatQuantity(value: unknown): string {
  const quantity = Number(value ?? 0)
  return Number.isFinite(quantity) ? Math.trunc(quantity).toLocaleString('zh-CN') : '0'
}

export function formatSignedQuantity(value: unknown): string {
  const quantity = Number(value)
  return `${quantity > 0 ? '+' : ''}${formatQuantity(quantity)}`
}

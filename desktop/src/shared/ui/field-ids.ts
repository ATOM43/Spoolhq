/** The id of a `Field`'s hint or error, for the control's `aria-describedby`. */
export function describedBy(id: string): string {
  return `${id}-message`;
}

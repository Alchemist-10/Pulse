// All number and date formatting goes through `Intl`. We do not hand-write
// separators or date order (.claude/rules/frontend.md): `en-IN` gives lakh/crore
// grouping and day-first dates, and the platform's output beats ours.
//
// NOTE: this is for interface values only — counts, the patient's date of birth,
// a phone number. Clinical values (lab results, dosages) are never reformatted;
// they render exactly as recorded.

const DATE_LOCALE = "en-IN";
const NUMBER_LOCALE = "en-IN";

/** Day-first date, e.g. "12 Apr 1990". Accepts an ISO date string or Date. */
export function formatDate(value: string | Date): string {
  const date = typeof value === "string" ? new Date(value) : value;
  if (Number.isNaN(date.getTime())) return typeof value === "string" ? value : "";
  return new Intl.DateTimeFormat(DATE_LOCALE, {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(date);
}

/** Integer with Indian grouping, e.g. 1234567 -> "12,34,567". */
export function formatNumber(value: number): string {
  return new Intl.NumberFormat(NUMBER_LOCALE).format(value);
}

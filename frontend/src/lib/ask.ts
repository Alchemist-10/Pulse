import type { AskIntent, AskResponse } from "./generated/api";

export type { AskIntent, AskResponse } from "./generated/api";
export type AskBlock = AskResponse["blocks"][number];

/** Intents a patient can ask about, in display order. UNMATCHED is not one. */
export const ASK_INTENTS: AskIntent[] = [
  "LATEST_LAB",
  "LAB_TREND",
  "WHO_ACCESSED",
  "WHAT_CHANGED",
  "MEDICATIONS",
  "ALLERGIES",
  "CONDITIONS",
  "EMERGENCY_PREVIEW",
];

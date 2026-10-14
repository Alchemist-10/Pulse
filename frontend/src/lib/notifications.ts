import { api } from "./api";
import type { NotificationType } from "./generated/api";
export const NOTIFICATIONS_CHANGED_EVENT = "pulse:notifications-changed";
export {
  NotificationTypeValues as NOTIFICATION_TYPES,
  NotificationChannelValues as NOTIFICATION_CHANNELS,
} from "./generated/api";
export type {
  NotificationType,
  NotificationChannel,
  Notification,
  NotificationPreference,
} from "./generated/api";

/**
 * Mandatory types — never subject to a preference check, never shown in the
 * preferences list, absent rather than locked
 * (`backend/app/modules/notifications/service.py` `MANDATORY_TYPES`, issue
 * #43; .claude/rules/clinical-safety.md). A break-glass access and a
 * consent revocation must always reach the Patient; consent-granted,
 * record-uploaded and the daily digest are all opt-outable.
 */
export const MANDATORY_NOTIFICATION_TYPES: ReadonlySet<NotificationType> =
  new Set(["BREAK_GLASS_ACCESS", "CONSENT_REVOKED", "EMERGENCY_CARD_VIEWED"]);

/** Marks every unread notification read; tells the bell and list to refresh. */
export async function markAllNotificationsRead(): Promise<void> {
  await api.post<{ updated: number }>("/notifications/read-all");
  window.dispatchEvent(new Event(NOTIFICATIONS_CHANGED_EVENT));
}

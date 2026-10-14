export type {
  EmergencyCard,
  EmergencyCardUpdate,
  EmergencyCardView,
} from "./generated/api";

const TOKEN = /^[A-Za-z0-9_-]{16,64}$/;

/** Link a QR carries: this site's emergency page for one token. */
export function emergencyLink(origin: string, locale: string, token: string) {
  return `${origin}/${locale}/emergency/${token}`;
}

/** Token from a scanned/pasted value: a Pulse emergency link or a bare token. */
export function tokenFromScan(text: string): string | null {
  const value = text.trim();
  if (TOKEN.test(value)) return value;
  const match = value.match(/\/emergency\/([A-Za-z0-9_-]{16,64})(?:[/?#]|$)/);
  return match ? match[1] : null;
}

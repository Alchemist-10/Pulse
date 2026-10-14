"use client";

import { use } from "react";
import { EmergencyCardLoader } from "@/components/EmergencyCardLoader";

export default function EmergencyByTokenPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = use(params);
  return (
    <EmergencyCardLoader
      path={`/emergency-card/by-token/${encodeURIComponent(token)}`}
      fallback="/"
    />
  );
}

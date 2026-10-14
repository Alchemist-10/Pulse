"use client";

import { use } from "react";
import { EmergencyCardLoader } from "@/components/EmergencyCardLoader";

export default function PatientEmergencyPage({
  params,
}: {
  params: Promise<{ patientId: string }>;
}) {
  const { patientId } = use(params);
  return (
    <EmergencyCardLoader
      path={`/patients/${encodeURIComponent(patientId)}/emergency-card`}
      fallback="/clinician"
      recordsPatientId={patientId}
    />
  );
}

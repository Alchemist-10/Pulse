"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Callout } from "@/components/ui/Callout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { useRouter } from "@/i18n/navigation";
import type { DuplicateReviewCandidate, MergeRecord, MergeResult } from "@/lib/admin";
import { api, ApiError } from "@/lib/api";
import type { Me } from "@/lib/auth";
import { useApiErrorMessage } from "@/lib/errors";
import { formatDate } from "@/lib/format";

// Duplicate review UI (issue #55). Renders `AdminPatientIdentity` fields
// only — `id`, `fullName`, `dateOfBirth`, `phone`, `claimed`, `entryCount` —
// never an entry's clinical content. That guarantee is structural, not a
// rendering choice: `DuplicateReviewCandidate`/`AdminPatientIdentity`
// (`lib/admin.ts`, mirroring `backend/app/modules/admin/schemas.py`) have no
// field capable of holding clinical content, and this screen fetches nothing
// else about either patient.
//
// Reversal reads `GET /admin/merges` (every unreversed merge, by any
// admin, in any session), so a merge stays reversible after a reload.
// Names only — identity, never clinical content.
type GateState = { status: "loading" } | { status: "denied" } | { status: "error"; message: string } | { status: "ready" };

type QueueState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; items: DuplicateReviewCandidate[] };

type RowBusy = "merge" | "notDuplicate" | null;

export default function DuplicateReviewPage() {
  const t = useTranslations("admin");
  const errorMessage = useApiErrorMessage();
  const router = useRouter();

  const [gate, setGate] = useState<GateState>({ status: "loading" });
  const [queue, setQueue] = useState<QueueState>({ status: "loading" });
  const [busyId, setBusyId] = useState<string | null>(null);
  const [busyKind, setBusyKind] = useState<RowBusy>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [merges, setMerges] = useState<MergeRecord[]>([]);
  const [reversingId, setReversingId] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    api
      .get<Me>("/auth/me")
      .then((me) => {
        if (!active) return;
        if (me.role !== "ADMINISTRATOR") {
          setGate({ status: "denied" });
          return;
        }
        setGate({ status: "ready" });
      })
      .catch((err) => {
        if (!active) return;
        if (err instanceof ApiError && (err.status === 401 || err.code === "SESSION_EXPIRED")) {
          router.replace("/login");
          return;
        }
        setGate({ status: "error", message: t("gate.error") });
      });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const [retryToken] = useState(0);

  useEffect(() => {
    if (gate.status !== "ready") return;
    let active = true;
    Promise.resolve().then(() => {
      if (active) setQueue({ status: "loading" });
    });
    api
      .get<DuplicateReviewCandidate[]>("/admin/duplicate-review")
      .then((items) => {
        if (active) setQueue({ status: "ready", items });
      })
      .catch((err) => {
        if (active) setQueue({ status: "error", message: errorMessage(err) });
      });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gate.status, retryToken]);

  function loadMerges() {
    api
      .get<MergeRecord[]>("/admin/merges")
      .then(setMerges)
      .catch((err) => setActionError(errorMessage(err)));
  }

  useEffect(() => {
    if (gate.status === "ready") loadMerges();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gate.status]);

  function markNotDuplicate(candidate: DuplicateReviewCandidate) {
    setBusyId(candidate.id);
    setBusyKind("notDuplicate");
    setActionError(null);
    api
      .post("/admin/duplicate-review/not-duplicate", {
        patientIdA: candidate.patientA.id,
        patientIdB: candidate.patientB.id,
      })
      .then(() => {
        setQueue((prev) =>
          prev.status === "ready"
            ? { ...prev, items: prev.items.filter((c) => c.id !== candidate.id) }
            : prev,
        );
      })
      .catch((err) => setActionError(errorMessage(err)))
      .finally(() => {
        setBusyId(null);
        setBusyKind(null);
      });
  }

  function merge(candidate: DuplicateReviewCandidate) {
    // The candidate with more entries wins by default — a reasonable default
    // absent any ticket guidance on which side should be the winner; the
    // admin can still tell the two apart before confirming since both
    // identities are shown in full.
    const winner =
      candidate.patientA.entryCount >= candidate.patientB.entryCount
        ? candidate.patientA
        : candidate.patientB;
    const loser = winner === candidate.patientA ? candidate.patientB : candidate.patientA;

    setBusyId(candidate.id);
    setBusyKind("merge");
    setActionError(null);
    api
      .post<MergeResult>("/admin/duplicate-review/merge", {
        winnerPatientId: winner.id,
        loserPatientId: loser.id,
      })
      .then(() => {
        loadMerges();
        setQueue((prev) =>
          prev.status === "ready"
            ? { ...prev, items: prev.items.filter((c) => c.id !== candidate.id) }
            : prev,
        );
      })
      .catch((err) => setActionError(errorMessage(err)))
      .finally(() => {
        setBusyId(null);
        setBusyKind(null);
      });
  }

  function reverseMerge(mergeId: string) {
    setReversingId(mergeId);
    setActionError(null);
    api
      .post<MergeResult>(`/admin/merges/${mergeId}/reverse`)
      .then((result) => {
        setMerges((prev) =>
          prev.map((m) => (m.id === result.id ? { ...m, reversedAt: result.reversedAt } : m)),
        );
      })
      .catch((err) => setActionError(errorMessage(err)))
      .finally(() => setReversingId(null));
  }

  if (gate.status === "loading") return <p className="text-sm text-muted">{t("loading")}</p>;
  if (gate.status === "denied") {
    return (
      <Callout tone="error" iconLabel={t("gate.title")}>
        {t("gate.denied")}
      </Callout>
    );
  }
  if (gate.status === "error") {
    return (
      <Callout tone="error" iconLabel={t("gate.title")}>
        {gate.message}
      </Callout>
    );
  }

  return (
    <section className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-foreground">{t("duplicateReview.title")}</h1>
        <p className="text-sm text-muted">{t("duplicateReview.description")}</p>
      </div>

      {actionError && (
        <Callout tone="error" iconLabel={t("duplicateReview.actionErrorTitle")}>
          {actionError}
        </Callout>
      )}

      {queue.status === "loading" && <p className="text-sm text-muted">{t("loading")}</p>}

      {queue.status === "error" && (
        <Callout tone="error" iconLabel={t("duplicateReview.actionErrorTitle")}>
          {queue.message}
        </Callout>
      )}

      {queue.status === "ready" && queue.items.length === 0 && (
        <Callout tone="info" iconLabel={t("duplicateReview.emptyTitle")}>
          {t("duplicateReview.empty")}
        </Callout>
      )}

      {queue.status === "ready" &&
        queue.items.map((candidate) => (
          <Card key={candidate.id}>
            <CardHeader className="flex flex-row items-center justify-between gap-2">
              <CardTitle className="text-base">
                {t("duplicateReview.candidateTitle")}
              </CardTitle>
              <Badge variant="outline">
                {t("duplicateReview.score", { score: candidate.score.toFixed(2) })}
              </Badge>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {[candidate.patientA, candidate.patientB].map((p, idx) => (
                  <div key={p.id} className="space-y-1 rounded-lg border border-border p-3 text-sm">
                    <p className="text-xs font-semibold tracking-wide text-muted uppercase">
                      {t("duplicateReview.candidateLabel", { n: idx + 1 })}
                    </p>
                    <p className="font-medium text-foreground">{p.fullName}</p>
                    <p className="text-muted">
                      {t("duplicateReview.fields.dateOfBirth")}: {formatDate(p.dateOfBirth) || "—"}
                    </p>
                    <p className="text-muted">
                      {t("duplicateReview.fields.phone")}: {p.phone ?? "—"}
                    </p>
                    <p className="text-muted">
                      {t("duplicateReview.fields.claimed")}:{" "}
                      {p.claimed ? t("duplicateReview.claimedTrue") : t("duplicateReview.claimedFalse")}
                    </p>
                    <p className="text-muted">
                      {t("duplicateReview.fields.entryCount")}: {p.entryCount}
                    </p>
                  </div>
                ))}
              </div>

              <div className="flex flex-wrap gap-3">
                <Button
                  variant="primary"
                  loading={busyId === candidate.id && busyKind === "merge"}
                  disabled={busyId !== null}
                  onClick={() => merge(candidate)}
                >
                  {t("duplicateReview.mergeCta")}
                </Button>
                <Button
                  variant="secondary"
                  loading={busyId === candidate.id && busyKind === "notDuplicate"}
                  disabled={busyId !== null}
                  onClick={() => markNotDuplicate(candidate)}
                >
                  {t("duplicateReview.notDuplicateCta")}
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}

      {merges.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("duplicateReview.recentMerges.title")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-xs text-muted">{t("duplicateReview.recentMerges.hint")}</p>
            <ul className="divide-y divide-border">
              {merges.map((m) => (
                <li key={m.id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
                  <span className="text-foreground">
                    {t("duplicateReview.recentMerges.pair", { winner: m.winnerName, loser: m.loserName })}
                    <span className="ml-2 text-muted">{formatDate(m.occurredAt)}</span>
                    {m.reversedAt && (
                      <Badge variant="outline" className="ml-2">
                        {t("duplicateReview.recentMerges.reversed")}
                      </Badge>
                    )}
                  </span>
                  {!m.reversedAt && (
                    <Button
                      variant="secondary"
                      loading={reversingId === m.id}
                      disabled={reversingId !== null}
                      onClick={() => reverseMerge(m.id)}
                    >
                      {t("duplicateReview.recentMerges.reverseCta")}
                    </Button>
                  )}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </section>
  );
}

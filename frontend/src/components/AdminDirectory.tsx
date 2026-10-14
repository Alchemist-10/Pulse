"use client";

import { useCallback, useEffect, useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import { SearchIcon } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Link, useRouter } from "@/i18n/navigation";
import { api } from "@/lib/api";
import { useApiErrorMessage } from "@/lib/errors";
import { formatDate } from "@/lib/format";
import type {
  AdminPatientRow,
  AdminSummary,
  AdminUserRow,
} from "@/lib/generated/api";
import type { Page } from "@/lib/records";

// Identity and counts only (ADR-0007): no clinical value is on any wire here.
type Tab = "patients" | "users";

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <CardContent className="space-y-1 pt-6">
        <p className="text-3xl font-semibold tabular-nums">{value}</p>
        <p className="text-sm text-muted-foreground">{label}</p>
      </CardContent>
    </Card>
  );
}

function useCursorTable<T>(path: string, q: string, role?: string) {
  const errorMessage = useApiErrorMessage();
  const [items, setItems] = useState<T[]>([]);
  const [next, setNext] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (cursor: string | null, replace: boolean) => {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams({ limit: "25" });
      if (q.trim()) params.set("q", q.trim());
      if (role) params.set("role", role);
      if (cursor) params.set("cursor", cursor);
      try {
        const page = await api.get<Page<T>>(`${path}?${params}`);
        setItems((prev) => (replace ? page.items : [...prev, ...page.items]));
        setNext(page.nextCursor);
      } catch (e) {
        setError(errorMessage(e));
      } finally {
        setLoading(false);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [path, q, role],
  );

  useEffect(() => {
    const timer = setTimeout(() => void load(null, true), 250);
    return () => clearTimeout(timer);
  }, [load]);

  return { items, next, loading, error, more: () => void load(next, false) };
}

export function AdminDirectory() {
  const t = useTranslations("admin.directory");
  const locale = useLocale();
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("patients");
  const [q, setQ] = useState("");
  const [role, setRole] = useState("");
  const [summary, setSummary] = useState<AdminSummary | null>(null);

  useEffect(() => {
    let active = true;
    api
      .get<AdminSummary>("/admin/summary")
      .then((s) => active && setSummary(s))
      .catch(() => active && setSummary(null));
    return () => {
      active = false;
    };
  }, []);

  const patients = useCursorTable<AdminPatientRow>(
    tab === "patients" ? "/admin/patients" : "/admin/__idle",
    tab === "patients" ? q : "",
  );
  const users = useCursorTable<AdminUserRow>(
    tab === "users" ? "/admin/users" : "/admin/__idle",
    tab === "users" ? q : "",
    tab === "users" ? role : undefined,
  );

  return (
    <div className="space-y-6">
      {summary && (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Stat label={t("stats.patients")} value={summary.patients} />
          <Stat label={t("stats.claimed")} value={summary.claimedPatients} />
          <Stat label={t("stats.pending")} value={summary.pendingDuplicates} />
          <Stat
            label={t("stats.users")}
            value={
              summary.usersPatient +
              summary.usersClinician +
              summary.usersProviderStaff +
              summary.usersAdministrator
            }
          />
          <Stat label={t("stats.clinicians")} value={summary.usersClinician} />
          <Stat label={t("stats.staff")} value={summary.usersProviderStaff} />
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2">
        {(["patients", "users"] as const).map((key) => (
          <Button
            key={key}
            variant={tab === key ? "default" : "outline"}
            size="sm"
            aria-pressed={tab === key}
            onClick={() => {
              setTab(key);
              setQ("");
              setRole("");
            }}
          >
            {t(`tabs.${key}`)}
          </Button>
        ))}
        <div className="relative ml-auto w-full sm:w-72">
          <SearchIcon
            aria-hidden="true"
            className="absolute top-2.5 left-3 size-4 text-muted-foreground"
          />
          <Input
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={t(`search.${tab}`)}
            aria-label={t(`search.${tab}`)}
            className="pl-9"
          />
        </div>
        {tab === "users" && (
          <select
            value={role}
            onChange={(e) => setRole(e.target.value)}
            aria-label={t("roleFilter")}
            className="h-9 rounded-md border bg-background px-2 text-sm"
          >
            <option value="">{t("allRoles")}</option>
            {["PATIENT", "CLINICIAN", "PROVIDER_STAFF", "ADMINISTRATOR"].map(
              (r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ),
            )}
          </select>
        )}
      </div>

      {tab === "patients" && (
        <>
          {patients.error && (
            <Alert variant="destructive">
              <AlertDescription>{patients.error}</AlertDescription>
            </Alert>
          )}
          <div className="overflow-x-auto rounded-xl border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("cols.name")}</TableHead>
                  <TableHead>{t("cols.dob")}</TableHead>
                  <TableHead>{t("cols.phone")}</TableHead>
                  <TableHead>{t("cols.location")}</TableHead>
                  <TableHead>{t("cols.account")}</TableHead>
                  <TableHead className="text-right">
                    {t("cols.records")}
                  </TableHead>
                  <TableHead>{t("cols.registered")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {patients.items.map((p) => (
                  <TableRow
                    key={p.id}
                    tabIndex={0}
                    role="link"
                    className="cursor-pointer"
                    onClick={() => router.push(`/admin/patients/${p.id}`)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter")
                        router.push(`/admin/patients/${p.id}`);
                    }}
                  >
                    <TableCell className="font-medium">
                      <Link
                        href={`/admin/patients/${p.id}`}
                        onClick={(e) => e.stopPropagation()}
                      >
                        {p.fullName}
                      </Link>
                    </TableCell>
                    <TableCell className="tabular-nums">
                      {p.dateOfBirth ? formatDate(p.dateOfBirth) : "—"}
                    </TableCell>
                    <TableCell>{p.phone ?? "—"}</TableCell>
                    <TableCell>
                      {[p.city, p.state].filter(Boolean).join(", ") || "—"}
                    </TableCell>
                    <TableCell>
                      {p.claimed ? t("claimed") : t("unclaimed")}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {p.entryCount}
                    </TableCell>
                    <TableCell className="tabular-nums">
                      {new Date(p.createdAt).toLocaleDateString(`${locale}-IN`)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          {!patients.loading && patients.items.length === 0 && (
            <p className="text-sm text-muted-foreground">{t("empty")}</p>
          )}
          {patients.next && (
            <Button
              variant="outline"
              disabled={patients.loading}
              onClick={patients.more}
            >
              {t("loadMore")}
            </Button>
          )}
        </>
      )}

      {tab === "users" && (
        <>
          {users.error && (
            <Alert variant="destructive">
              <AlertDescription>{users.error}</AlertDescription>
            </Alert>
          )}
          <div className="overflow-x-auto rounded-xl border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("cols.email")}</TableHead>
                  <TableHead>{t("cols.role")}</TableHead>
                  <TableHead>{t("cols.verified")}</TableHead>
                  <TableHead>{t("cols.registered")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.items.map((u) => (
                  <TableRow key={u.id}>
                    <TableCell className="font-medium">{u.email}</TableCell>
                    <TableCell>{u.role}</TableCell>
                    <TableCell>
                      {u.emailVerified ? t("yes") : t("no")}
                    </TableCell>
                    <TableCell className="tabular-nums">
                      {new Date(u.createdAt).toLocaleDateString(`${locale}-IN`)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          {!users.loading && users.items.length === 0 && (
            <p className="text-sm text-muted-foreground">{t("empty")}</p>
          )}
          {users.next && (
            <Button
              variant="outline"
              disabled={users.loading}
              onClick={users.more}
            >
              {t("loadMore")}
            </Button>
          )}
        </>
      )}
    </div>
  );
}

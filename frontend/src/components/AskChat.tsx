"use client";

import { useRef, useState, type FormEvent } from "react";
import { useLocale, useTranslations } from "next-intl";
import {
  CheckCircle2Icon,
  ReceiptTextIcon,
  SendIcon,
  TriangleAlertIcon,
} from "lucide-react";
import { ClinicalText } from "@/components/ClinicalText";
import { EmergencyCardDisplay } from "@/components/EmergencyCardDisplay";
import { LabTrendResults } from "@/components/LabTrendResults";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Link } from "@/i18n/navigation";
import { api } from "@/lib/api";
import { ASK_INTENTS, type AskBlock, type AskIntent, type AskResponse } from "@/lib/ask";
import { useApiErrorMessage } from "@/lib/errors";
import { formatDate, formatDateTime } from "@/lib/format";

// Rule-based chat over the patient's own record. History lives in component
// state only: nothing is persisted client-side or server-side, because a
// stored answer would be a copy of the record outside the consent filter.

type Turn =
  | { id: number; question: string; pending: true }
  | { id: number; question: string; response: AskResponse }
  | { id: number; question: string; error: string };

function Receipt({ response }: { response: AskResponse }) {
  const t = useTranslations("ask.receipt");
  const { receipt } = response;
  const count = receipt.entryIds.length || receipt.entryCount;
  return (
    <details className="rounded-lg border px-3 py-2 text-sm">
      <summary className="flex cursor-pointer items-center gap-2 text-muted-foreground">
        <ReceiptTextIcon aria-hidden="true" className="size-4" />
        {t("summary")}
      </summary>
      <dl className="mt-2 space-y-1">
        <div>
          <dt className="text-xs text-muted-foreground">{t("source")}</dt>
          <dd>{t(`filter.${receipt.filter}`)}</dd>
        </div>
        {receipt.filter !== "none" && <p>{t("entries", { count })}</p>}
        <p className="text-muted-foreground">
          {receipt.auditLogged ? t("logged") : t("notLogged")}
        </p>
      </dl>
    </details>
  );
}

function Block({
  block,
  onAsk,
}: {
  block: AskBlock;
  onAsk: (question: string) => void;
}) {
  const t = useTranslations("ask");
  const tAudit = useTranslations("audit");
  const tRoles = useTranslations("auth.roles");

  switch (block.kind) {
    case "message": {
      const path = `answers.${block.key.replace(/^ask\./, "")}`;
      return <p>{t.has(path) ? t(path, block.params) : t("error")}</p>;
    }
    case "suggestions":
      return (
        <div className="flex flex-wrap gap-2">
          {block.intents.map((intent) => (
            <Button
              key={intent}
              type="button"
              variant="outline"
              size="sm"
              onClick={() => onAsk(t(`examples.${intent}`))}
            >
              {t(`examples.${intent}`)}
            </Button>
          ))}
        </div>
      );
    case "lab_value": {
      const hasRange = block.referenceLow != null && block.referenceHigh != null;
      return (
        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">{t("lab.latest")}</p>
          <p className="text-lg font-semibold">
            <ClinicalText>{block.testName}</ClinicalText>:{" "}
            <ClinicalText>
              {block.valueNumeric ?? block.valueText}
              {block.unit ? ` ${block.unit}` : ""}
            </ClinicalText>
          </p>
          <p className="flex items-center gap-1.5 text-sm">
            {block.isAbnormal ? (
              <>
                <TriangleAlertIcon aria-hidden="true" className="size-4" />
                {t("lab.abnormal")}
              </>
            ) : (
              <>
                <CheckCircle2Icon aria-hidden="true" className="size-4" />
                {t("lab.normal")}
              </>
            )}
          </p>
          {hasRange && (
            <p className="text-sm text-muted-foreground">
              {t("lab.range", { low: block.referenceLow!, high: block.referenceHigh! })}
            </p>
          )}
          <p className="text-sm text-muted-foreground">
            {t("lab.observed", { date: formatDate(block.observedAt) })}
          </p>
        </div>
      );
    }
    case "lab_trend":
      return (
        <div className="space-y-2">
          <p className="font-medium">
            <ClinicalText>{block.testName}</ClinicalText>
          </p>
          <LabTrendResults points={block.points} />
        </div>
      );
    case "entry_list":
      return (
        <div className="space-y-1">
          <p className="font-medium">{t(`lists.${block.listKind}`)}</p>
          <ul className="list-disc space-y-0.5 pl-5">
            {block.items.map((item, i) => (
              <li key={item.entryId ?? i}>
                <ClinicalText>{item.displayName}</ClinicalText>
                {item.detail && (
                  <span className="text-muted-foreground">
                    {" "}
                    · <ClinicalText>{item.detail}</ClinicalText>
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      );
    case "changes": {
      const days = block.windowDays;
      const list = (items: typeof block.added) => (
        <ul className="list-disc space-y-0.5 pl-5">
          {items.map((item, i) => (
            <li key={item.entryId ?? i}>
              <ClinicalText>{item.displayName}</ClinicalText>
              <span className="text-muted-foreground">
                {" "}
                · {formatDate(item.recordedAt)}
              </span>
            </li>
          ))}
        </ul>
      );
      return (
        <div className="space-y-3">
          <div className="space-y-1">
            <p className="font-medium">{t("changes.added", { days })}</p>
            {block.added.length ? list(block.added) : <p>{t("changes.none")}</p>}
          </div>
          {block.superseded.length > 0 && (
            <div className="space-y-1">
              <p className="font-medium">{t("changes.corrected")}</p>
              {list(block.superseded)}
            </div>
          )}
        </div>
      );
    }
    case "access_log":
      return (
        <div className="space-y-2">
          <p className="font-medium">
            {t("access.title", { count: block.total, days: block.windowDays })}
          </p>
          <ul className="space-y-2">
            {block.items.map((e) => (
              <li key={e.id} className="rounded-lg border px-3 py-2 text-sm">
                <p className="font-medium">
                  {e.actorName}
                  <Badge variant="secondary" className="ml-2">
                    {tRoles.has(e.actorRole) ? tRoles(e.actorRole) : e.actorRole}
                  </Badge>
                </p>
                <p className="text-muted-foreground">
                  {tAudit.has(`actions.${e.action}`) ? tAudit(`actions.${e.action}`) : e.action}
                  {" · "}
                  {formatDateTime(e.occurredAt)}
                </p>
                {e.entryType && (
                  <p className="text-muted-foreground">
                    {t("access.entryType", { type: e.entryType })}
                  </p>
                )}
              </li>
            ))}
          </ul>
          {block.truncated && (
            <p className="text-sm text-muted-foreground">
              {t("access.truncated", { count: block.items.length })}
            </p>
          )}
          <Link href="/audit" className="text-sm underline underline-offset-4">
            {t("access.openLog")}
          </Link>
        </div>
      );
    case "emergency_preview":
      return (
        <div className="space-y-2">
          {block.card ? (
            <>
              <p className="font-medium">{t("emergency.title")}</p>
              <EmergencyCardDisplay card={block.card} />
            </>
          ) : (
            <p>{t("emergency.notSetUp")}</p>
          )}
          <Link href="/settings" className="text-sm underline underline-offset-4">
            {t("emergency.edit")}
          </Link>
        </div>
      );
  }
}

export function AskChat() {
  const t = useTranslations("ask");
  const locale = useLocale() as "en" | "hi" | "ta" | "ml";
  const errorMessage = useApiErrorMessage();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [question, setQuestion] = useState("");
  const nextId = useRef(1);

  async function ask(text: string) {
    const q = text.trim();
    if (!q) return;
    const id = nextId.current++;
    setQuestion("");
    setTurns((prev) => [{ id, question: q, pending: true }, ...prev]);
    let turn: Turn;
    try {
      const response = await api.post<AskResponse>("/ask", { question: q, locale });
      turn = { id, question: q, response };
    } catch (err) {
      turn = { id, question: q, error: errorMessage(err) };
    }
    setTurns((prev) => prev.map((x) => (x.id === id ? turn : x)));
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void ask(question);
  }

  const suggestions: AskIntent[] = ASK_INTENTS;

  return (
    <div className="space-y-6">
      <form onSubmit={onSubmit} className="space-y-2">
        <Label htmlFor="ask-input">{t("inputLabel")}</Label>
        <div className="flex gap-2">
          <Input
            id="ask-input"
            value={question}
            maxLength={300}
            placeholder={t("placeholder")}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <Button type="submit" disabled={!question.trim()}>
            <SendIcon aria-hidden="true" className="size-4" />
            {t("send")}
          </Button>
        </div>
      </form>

      {turns.length === 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium">{t("emptyTitle")}</p>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((intent) => (
              <Button
                key={intent}
                type="button"
                variant="outline"
                size="sm"
                onClick={() => void ask(t(`examples.${intent}`))}
              >
                {t(`examples.${intent}`)}
              </Button>
            ))}
          </div>
        </div>
      )}

      <ol className="space-y-4" aria-live="polite">
        {turns.map((turn) => (
          <li key={turn.id} className="space-y-2">
            <p className="text-sm text-muted-foreground">
              {t("you")}: {turn.question}
            </p>
            <Card size="sm">
              <CardContent className="space-y-3">
                {"pending" in turn && (
                  <p className="text-muted-foreground">{t("thinking")}</p>
                )}
                {"error" in turn && <p role="alert">{turn.error}</p>}
                {"response" in turn && (
                  <>
                    {turn.response.blocks.map((block, i) => (
                      <Block key={i} block={block} onAsk={(q) => void ask(q)} />
                    ))}
                    <Receipt response={turn.response} />
                  </>
                )}
              </CardContent>
            </Card>
          </li>
        ))}
      </ol>
    </div>
  );
}

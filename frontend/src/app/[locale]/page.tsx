import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/Button";
import {
  ActivityIcon,
  ClinicalNoteIcon,
  EyeIcon,
  ShieldCheckIcon,
} from "@/components/ui/icons";
import { Link } from "@/i18n/navigation";

// Home = the product's spine in three cards: the lifelong history, consent
// the patient controls, and the audit log that keeps both honest. Everything
// below is interface chrome — clinical data never appears on this page.
export default function HomePage() {
  const t = useTranslations("home");

  const features = [
    { icon: ClinicalNoteIcon, title: t("features.history.title"), body: t("features.history.body") },
    { icon: ShieldCheckIcon, title: t("features.consent.title"), body: t("features.consent.body") },
    { icon: EyeIcon, title: t("features.audit.title"), body: t("features.audit.body") },
  ] as const;

  return (
    <div className="space-y-12">
      <section className="bg-brand-wash -mx-4 rounded-b-3xl px-4 pb-10 pt-6 sm:pt-12">
        <div className="mx-auto max-w-2xl space-y-5 text-center">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface px-3 py-1 text-xs font-medium text-accent-text shadow-sm">
            <ActivityIcon className="size-3.5" />
            {t("badge")}
          </span>
          <h1 className="text-balance text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            {t("title")}
          </h1>
          <p className="text-pretty text-base text-muted sm:text-lg">{t("description")}</p>
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Link href="/register">
              <Button className="min-w-40">{t("registerCta")}</Button>
            </Link>
            <Link href="/login">
              <Button variant="secondary" className="min-w-40">
                {t("loginCta")}
              </Button>
            </Link>
          </div>
        </div>
      </section>

      <section aria-label={t("features.label")} className="grid gap-4 sm:grid-cols-3">
        {features.map(({ icon: Icon, title, body }) => (
          <div
            key={title}
            className="elevated-card rounded-xl border border-border bg-surface p-5"
          >
            <span className="mb-3 flex size-10 items-center justify-center rounded-lg bg-accent-soft text-accent-text">
              <Icon className="size-5" />
            </span>
            <h2 className="text-base font-semibold text-foreground">{title}</h2>
            <p className="mt-1 text-sm leading-relaxed text-muted">{body}</p>
          </div>
        ))}
      </section>
    </div>
  );
}

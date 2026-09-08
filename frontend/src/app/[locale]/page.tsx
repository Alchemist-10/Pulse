import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";

export default function HomePage() {
  const t = useTranslations("home");

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold text-foreground">{t("title")}</h1>
        <p className="text-muted">{t("description")}</p>
      </div>
      <div className="flex flex-wrap gap-3">
        <Link
          href="/register"
          className="inline-flex min-h-11 items-center rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-contrast hover:bg-accent-hover"
        >
          {t("registerCta")}
        </Link>
        <Link
          href="/login"
          className="inline-flex min-h-11 items-center rounded-md border border-border-strong bg-surface px-4 py-2 text-sm font-medium text-foreground hover:bg-surface-raised"
        >
          {t("loginCta")}
        </Link>
      </div>
    </div>
  );
}

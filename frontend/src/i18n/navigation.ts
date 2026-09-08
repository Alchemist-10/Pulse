import { createNavigation } from "next-intl/navigation";
import { routing } from "./routing";

// Locale-aware wrappers around Next's navigation APIs. Screens and the
// LocaleSwitcher import from here, never from "next/navigation" directly, so
// the active locale prefix is always preserved.
export const { Link, redirect, usePathname, useRouter, getPathname } =
  createNavigation(routing);

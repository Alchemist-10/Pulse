"""Users wire schemas."""

from typing import Literal

from app.core.schema import PulseSchema

# The four interface locales (frontend `i18n/routing.ts`).
SupportedLocale = Literal["en", "hi", "ta", "ml"]


class LocalePreferenceUpdate(PulseSchema):
    locale: SupportedLocale

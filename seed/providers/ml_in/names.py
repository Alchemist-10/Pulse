"""Hand-compiled Malayalam (Kerala) name word-lists for the ``ml_IN`` gap.

Faker ships no ``ml_IN`` provider (verified against ``joke2k/faker`` on
2026-08-22; see ``docs/seed-data.md`` Gap 1). Personal names are facts and
not independently copyrightable, so this list carries no licence
encumbrance. It is deliberately small -- tens to low hundreds of entries,
not a corpus.

Three Kerala community naming patterns are modelled (seed-data.md asks for
at least two):

* **Hindu** -- given name + family/house name ("Anil Menon", "Lakshmi
  Nair"); the house name is frequently reduced to a leading initial
  ("K. Anil"), which is itself a natural near-duplicate generator.
* **Syrian Christian** -- given name (often Biblical) + house name
  ("Thomas Kadavil", "Mariamma Mulamoottil").
* **Mappila Muslim** -- given name + family marker ("Abdul Rahman
  Haji", "Fathima Koya").

Structural references for Kerala naming conventions (cited as a courtesy,
the same one Faker extends to its own sources):

* L. A. Krishna Iyer, *The Travancore Tribes and Castes* (1937) -- house
  (``tharavadu``) naming.
* Susan Bayly, *Saints, Goddesses and Kings* (1989), ch. on Kerala
  Syrian Christians -- house-name inheritance.
* R. E. Miller, *Mappila Muslims of Kerala* (1976) -- Mappila
  given-name / patronymic patterns.

All strings are Malayalam (ISO 639-1 ``ml``) in Unicode; a romanisation
follows each in a comment for review.
"""

from __future__ import annotations

# --- given names, male -------------------------------------------------------

FIRST_NAMES_MALE_HINDU = (
    "അനിൽ",          # Anil
    "സുനിൽ",         # Sunil
    "രാജീവ്",         # Rajeev
    "ബിജു",          # Biju
    "ഷിബു",          # Shibu
    "ഹരി",           # Hari
    "മുരളി",          # Murali
    "രമേശ്",          # Ramesh
    "സുരേഷ്",         # Suresh
    "ദിനേശ്",         # Dinesh
    "മഹേഷ്",          # Mahesh
    "പ്രദീപ്",         # Pradeep
    "സന്തോഷ്",        # Santhosh
    "അനൂപ്",          # Anoop
    "വിനോദ്",         # Vinod
    "ജയൻ",           # Jayan
    "മോഹനൻ",         # Mohanan
    "ബാലകൃഷ്ണൻ",     # Balakrishnan
    "ഉണ്ണികൃഷ്ണൻ",   # Unnikrishnan
    "ശ്രീകുമാർ",       # Sreekumar
    "വിജയൻ",         # Vijayan
    "പ്രകാശ്",         # Prakash
    "അരവിന്ദ്",       # Aravind
    "ഗിരീഷ്",         # Gireesh
    "സജീവ്",          # Sajeev
)

FIRST_NAMES_MALE_CHRISTIAN = (
    "തോമസ്",          # Thomas
    "മാത്യു",          # Mathew
    "ജോർജ്",          # George
    "വർഗീസ്",         # Varghese
    "ജേക്കബ്",         # Jacob
    "ചാക്കോ",         # Chacko
    "കുര്യൻ",          # Kurian
    "ഈപ്പൻ",          # Eappen
    "ഫിലിപ്പ്",        # Philip
    "സക്കറിയ",        # Zacharia
    "ജോസഫ്",          # Joseph
    "ബിനോയ്",         # Binoy
)

FIRST_NAMES_MALE_MUSLIM = (
    "അബ്ദുൾ റഹ്‌മാൻ",  # Abdul Rahman
    "മുഹമ്മദ്",         # Muhammed
    "ഹംസ",            # Hamza
    "ബഷീർ",           # Basheer
    "സലീം",           # Saleem
    "റഷീദ്",           # Rasheed
    "നൗഷാദ്",          # Naushad
    "അഷ്‌റഫ്",         # Ashraf
    "ഫൈസൽ",           # Faisal
    "സിദ്ദീഖ്",         # Siddique
    "ജമാൽ",           # Jamal
    "ഇർഫാൻ",          # Irfan
)

# --- given names, female ---------------------------------------------------

FIRST_NAMES_FEMALE_HINDU = (
    "ലക്ഷ്മി",         # Lakshmi
    "പാർവതി",         # Parvathy
    "സരസ്വതി",        # Saraswathy
    "രാധിക",          # Radhika
    "ദിവ്യ",           # Divya
    "അഞ്ജലി",         # Anjali
    "രമ്യ",            # Remya
    "സ്വപ്ന",          # Swapna
    "ബിന്ദു",          # Bindu
    "സിന്ധു",          # Sindhu
    "ദീപ",            # Deepa
    "ഗീത",            # Geetha
    "ലത",             # Latha
    "ഉഷ",             # Usha
    "ശ്രീജ",           # Sreeja
    "രേഷ്മ",           # Reshma
    "അമ്പിളി",         # Ambili
    "ഗായത്രി",         # Gayathri
    "മീര",            # Meera
    "അശ്വതി",          # Aswathy
    "കാവ്യ",           # Kavya
    "ആതിര",           # Athira
    "രജനി",           # Rajani
    "സുജാത",          # Sujatha
)

FIRST_NAMES_FEMALE_CHRISTIAN = (
    "മറിയാമ്മ",        # Mariamma
    "അന്ന",           # Anna
    "ഏലിയാമ്മ",        # Eliamma
    "ഗ്രേസി",          # Gracy
    "ജെസ്സി",          # Jessy
    "ലിസി",           # Lissy
    "റോസമ്മ",         # Rosamma
    "ഷേർലി",          # Sherly
    "സൂസൻ",          # Susan
    "ആനി",            # Annie
    "ജിൻസി",          # Jincy
)

FIRST_NAMES_FEMALE_MUSLIM = (
    "ഫാത്തിമ",         # Fathima
    "ആയിഷ",           # Ayesha
    "സുഹറ",           # Suhra
    "റംല",            # Ramla
    "ഷഹീന",           # Shaheena
    "നസീമ",           # Naseema
    "ജസീല",           # Jaseela
    "റസിയ",           # Rasiya
    "ഹസീന",           # Haseena
    "സൈനബ",          # Zainab
    "റുക്‌സാന",        # Ruksana
)

# --- family / house names, grouped by community --------------------------

LAST_NAMES_HINDU = (
    "മേനോൻ",          # Menon
    "നായർ",           # Nair
    "പിള്ള",           # Pillai
    "കുറുപ്പ്",         # Kurup
    "പണിക്കർ",         # Panicker
    "വാരിയർ",          # Warrier
    "നമ്പൂതിരി",       # Namboothiri
    "കൈമൾ",           # Kaimal
    "ഉണ്ണിത്താൻ",     # Unnithan
    "തമ്പി",           # Thampi
    "മാരാർ",           # Marar
    "കിഴക്കേടത്ത്",     # Kizhakkedathu (house)
    "പുത്തൻപുരയിൽ",   # Puthenpurayil (house)
    "വടക്കേവീട്ടിൽ",   # Vadakkeveettil (house)
    "മംഗലത്ത്",        # Mangalathu (house)
    "ചിറ്റിലപ്പിള്ളി",  # Chittilappilly (house)
    "മുണ്ടയ്ക്കൽ",     # Mundakkal (house)
    "പുതുശ്ശേരി",      # Puthussery (house)
)

LAST_NAMES_CHRISTIAN = (
    "കടവിൽ",          # Kadavil
    "മുളമൂട്ടിൽ",       # Mulamoottil
    "പുളിക്കൽ",        # Pulickal
    "ഐക്കര",          # Aikkara
    "കാരിക്കാംപള്ളിൽ",  # Karikkampallil
    "ചെറിയാൻ",        # Cherian
    "കൊച്ചുപറമ്പിൽ",   # Kochuparambil
    "വർക്കി",          # Varkey
    "ഏഴുപുന്ന",        # Ezhupunna
)

LAST_NAMES_MUSLIM = (
    "ഹാജി",           # Haji
    "മുസ്‌ലിയാർ",      # Musliyar
    "തങ്ങൾ",           # Thangal
    "കോയ",            # Koya
    "റാവുത്തർ",        # Rawther
    "മരയ്ക്കാർ",       # Maraikkar
    "ബാവ",            # Bava
)

FIRST_NAMES_MALE = (
    FIRST_NAMES_MALE_HINDU + FIRST_NAMES_MALE_CHRISTIAN + FIRST_NAMES_MALE_MUSLIM
)
FIRST_NAMES_FEMALE = (
    FIRST_NAMES_FEMALE_HINDU
    + FIRST_NAMES_FEMALE_CHRISTIAN
    + FIRST_NAMES_FEMALE_MUSLIM
)
LAST_NAMES = LAST_NAMES_HINDU + LAST_NAMES_CHRISTIAN + LAST_NAMES_MUSLIM

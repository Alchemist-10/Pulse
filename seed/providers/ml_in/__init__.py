"""Project-local ``ml_IN`` Faker person provider (Malayalam / Kerala).

Shaped exactly like Faker's own ``or_IN`` person provider so the overlay
calls it the same way it calls every other Indian locale::

    from faker import Faker
    from seed.providers.ml_in import Provider as MlInPerson

    fake = Faker("en_IN")            # any base locale; we only use the name
    fake.add_provider(MlInPerson)
    fake.name()                      # -> Malayalam name

Word-lists and their sources live in :mod:`seed.providers.ml_in.names`.
"""

from __future__ import annotations

from faker.providers.person import Provider as PersonProvider

from . import names as _n


class Provider(PersonProvider):
    """Malayalam person names across three Kerala community patterns."""

    formats_female = (
        "{{first_name_female}} {{last_name}}",
        "{{first_name_female}} {{last_name}}",
        "{{first_name_female}} {{last_name}}",
        "{{house_initial}} {{first_name_female}}",
    )
    formats_male = (
        "{{first_name_male}} {{last_name}}",
        "{{first_name_male}} {{last_name}}",
        "{{first_name_male}} {{last_name}}",
        "{{house_initial}} {{first_name_male}}",
    )
    formats = formats_female + formats_male

    first_names_male = _n.FIRST_NAMES_MALE
    first_names_female = _n.FIRST_NAMES_FEMALE
    first_names = _n.FIRST_NAMES_MALE + _n.FIRST_NAMES_FEMALE
    last_names = _n.LAST_NAMES

    def house_initial(self) -> str:
        """A house name reduced to its leading grapheme plus a dot -- the
        "K. Anil" form that Kerala Hindu names very commonly take, and a
        natural source of initials-vs-expanded near-duplicates."""
        house = self.random_element(_n.LAST_NAMES_HINDU)
        return f"{house[0]}."

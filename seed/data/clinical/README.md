# seed/data/clinical

Synthea clinical output, patient-id-remapped onto the overlaid Pulse
Patient UUIDs. Coded vocabularies are preserved verbatim: SNOMED-CT
(`conditions`, `procedures`), LOINC (`observations`), RxNorm
(`medications`).

**Not loaded in Phase 1** -- Phase 1 has no clinical tables (`medical_entry`
et al. are Phase 2), so these files were committed ahead of time as a
fixed, reviewed dataset. From P2.4, `seed_loader.py` reads this directory
too and loads a capped, deterministic selection of Medical Entries per
Patient (real `(code_system, code)` pairs throughout; no code invented).

US cost / payer / provider-identity columns are dropped in transform.
Planted duplicate and near-miss Patients carry no clinical rows.

| file | rows |
|---|---|
| `conditions.csv` | 3908 |
| `medications.csv` | 5122 |
| `observations.csv` | 73845 |
| `procedures.csv` | 13226 |
| `encounters.csv` | 6290 |

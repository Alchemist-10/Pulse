# Demo script

A step-by-step script for the live demo, covering the full spine from
issue #56 (signup → upload → timeline → grant → clinician read → patient
audit view → revoke → clinician locked out) plus a pass through Phase 4's
analytics, admin dashboard and duplicate-review screens.

**Rehearsal status:** walked through once, end to end, against `docker
compose up --build` **on this machine's existing clone** (`/mnt/d/Projects/Pulse`,
already checked out at the tip of `main` used for this ticket) — **not** a
fresh `git clone` on a separate machine, and not yet rehearsed by anyone
other than the author. Issue #56 asks for a rehearsal "on a machine that is
not the author's" as a follow-up beyond this ticket's acceptance criteria;
that second rehearsal has not happened and should not be assumed done.
Every screen and button name below was checked against the actually
running app during this rehearsal, not just against the source.

## Setup (before the audience is in the room)

```bash
git clone https://github.com/moneytosms/Pulse.git   # or cd into an existing clone
cd Pulse
docker compose up --build
```

Wait for all six containers healthy (`docker compose ps`). First boot runs
migrations and seeds identity data automatically — no separate seed step.

- App: `http://localhost`
- Mailpit inbox (verification emails): `http://localhost:8025`

**Known gap — no seeded Administrator.** `seed/data/identity/users.csv`
seeds `CLINICIAN`, `PATIENT` and `PROVIDER_STAFF` rows (four of them
marked `demo_login=1` and shown as quick-login buttons on `/en/login`),
but no `ADMINISTRATOR` row, and there is no in-app path to become one —
role assignment at registration only offers Patient/Provider/Clinician,
and there is no role-change endpoint implemented yet (`architecture.md`
mentions step-up verification for "administrator role changes" as a
future requirement, not a built one). To reach `/admin` in the demo, promote
one seeded user by hand, once, right after first boot:

```bash
docker compose exec postgres psql -U pulse -d pulse -c \
  "UPDATE \"user\" SET role = 'ADMINISTRATOR' WHERE email = 'staff000@example.com';"
```

This trades `staff000@example.com`'s Provider-staff demo-login button for
Administrator access — pick a seeded account you are not otherwise using
in Part 1, since it also loses its original role's demo-login button
matching. (`Pulse@demo1` is still its password; log in through the plain
email/password form, not the quick-login button, since the button list is
static and will still say "Provider staff" for it.) Do this once during
setup, not on stage.

## Part 1 — the demo spine (#56)

All of this is one continuous story about **Priya**, a patient, and **Dr.
Fathima Rasheed**, a clinician who initially has no access to her record.

1. **Signup.** Go to `/en/register`. Fill in an email, a password, choose
   "Patient", submit. Land on "Confirm your email address"
   (`/en/verify-pending`). Open `http://localhost:8025`, find the
   verification email, click the link. Say: *every account starts
   unverified — this is the DPDP-shaped consent story starting at account
   creation, not at first clinical read.*

2. **Log in** as the new account (or use the **Patient (EN)** quick-login
   button on `/en/login` — `demo.patient.en@example.com` — to skip ahead
   with a patient who already has history).

3. **Upload.** Go to `/en/timeline/new`. File a Diagnosis entry: pick
   "Diagnosis", set an occurred-at date/time, code system "ICD-10", code
   "E11", display name "Type 2 diabetes mellitus". Submit → "View entry".
   Say: *this is a Provider or the patient themself filing a Medical
   Entry — never editable in place after this point, only superseded.*

4. **Timeline.** Go to `/en/timeline`. The filed entry appears, newest
   first. Point out the entry-type filter and the "Critical" label (never
   colour alone — `frontend.md`).

5. **Grant consent.** Go to `/en/consent/new`. Enter the clinician's user
   ID (use the seeded **Clinician** account's ID — look it up via the
   Clinician quick-login on `/en/login`, or use a known seed ID), purpose
   "Treatment", an expiry date. Submit → "Access granted". Say: *consent
   is granted to one named clinician, never an organisation, and it always
   has a mandatory expiry.*

6. **Clinician reads the record.** Open a second (private/incognito)
   window, log in as **Clinician** (`clinician0@example.com` quick-login).
   Go to `/en/patients/{patientId}/records`. The Diagnosis entry is
   visible. Say: *this read is happening because of the consent grant, not
   because of the clinician's role — a Clinician role alone grants
   nothing.*

7. **Patient's own audit view.** Back in Priya's window, go to `/en/audit`
   — "Who accessed my records". The clinician's read appears, with the
   clinician's name and provider organisation, never any clinical content.
   Say: *this is one row per access, not per entry viewed — a 50-entry
   timeline read is still one `ENTRY_VIEWED` audit event.*

8. **Revoke.** Go to `/en/consent`, find the clinician's grant, click
   "Revoke", confirm. No step-up verification is asked here — say: *this
   is deliberate; withdrawing access must be the frictionless direction.*

9. **Clinician locked out.** Back in the clinician's window, reload
   `/en/patients/{patientId}/records`. It now shows "Record not found" —
   the exact same message a genuinely nonexistent patient ID would
   produce. Say: *this is a 404, not a 403 — a 403 would confirm the
   record exists, which itself is sensitive information. Revocation took
   effect immediately, mid-session, because permission is never cached.*

## Part 2 — Phase 4 screens

Still as the patient from Part 1 (needs a few filed entries with lab
values to show something on the analytics screen — the seeded demo
patients have this already; a freshly-registered account filed in Part 1
will look sparse, so switch to `demo.patient.en@example.com` for this
part if you started from a brand-new signup).

10. **Analytics.** Go to `/en/analytics` — "Your health analytics". Walk
    through visit frequency, active medications, and the data-quality
    flags section (e.g. "No contact phone number is on file for you.").
    Say: *every chart here is computed on read, through the same
    consent-aware query path as the timeline — there is no stored insight
    table to go stale or leak.*

11. **Admin dashboard.** Switch to the Administrator account set up above.
    Go to `/en/admin`. Say: *an Administrator reads no clinical data on
    any screen, ever — this dashboard only ever shows identity fields and
    counts.*

12. **Duplicate review.** Click through to `/en/admin/duplicates`. If the
    queue is empty, say so plainly rather than skipping the screen —
    the seeded planted-duplicate pairs may already have been reviewed in
    an earlier session. If a candidate is present: point out that only
    name/DOB/phone/claim-status/entry-count are shown, walk through
    "Merge" and the resulting entry in "Merges this session", and mention
    that a merge is reversible from that same list — but only within the
    session that performed it (no endpoint lists past merges by ID).

## Fallback notes

- If Mailpit shows no email after signup, check `docker compose logs
  backend` for an SMTP connection error before assuming the account
  didn't register — registration and email delivery are decoupled.
- If `/admin` says "Administrator access required" after logging in as
  the promoted account, the session cookie may predate the SQL update —
  log out and back in.
- Locale switching (`/en` ↔ `/hi` ↔ `/ta` ↔ `/ml`) works on every screen
  above; see `docs/locale-review.md` before demonstrating Tamil or
  Malayalam screens, since neither has had a native-speaker review pass.

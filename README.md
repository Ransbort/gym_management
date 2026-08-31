### Gym Management

A standalone gym management app built on Frappe: members, memberships, attendance,
trainers, group fitness classes, personal training packages, workout plans, body
metric tracking, and locker / gym-floor equipment operations.

No dependency on ERPNext or any other app — it runs on plain Frappe. Billing fields
(`amount`, `payment_status`, `invoice_reference`) are simple, unopinionated fields
you can wire up to whichever invoicing app you use.

#### What's included

- **Members & memberships** — Gym Member, Membership Plan, Membership, Membership
  Renewal. A member's `membership_status` is kept in sync automatically whenever a
  Membership is created, updated or renewed.
- **Attendance** — Gym Attendance (single check-in/check-out record with an
  auto-computed duration).
- **Trainers** — Trainer records, optionally linked to a User login.
- **Group fitness** — Class Type, Class Schedule (weekly recurring slots), Class
  Booking (auto-waitlists once a schedule's capacity is reached).
- **Personal training** — PT Package, PT Package Purchase (tracks sessions
  remaining and expiry), PT Session (marking a session Completed decrements the
  purchase's remaining-session count automatically).
- **Workout plans & body metrics** — Exercise library, Workout Plan (with a sets/
  reps/rest child table), Member Workout Plan assignments, Body Metric Log
  (weight, body fat %, measurements, progress photos).
- **Lockers & equipment** — Locker, Locker Rental (keeps the Locker's status in
  sync), Gym Equipment, Equipment Maintenance Log (updates the equipment's status
  from each maintenance entry).

A daily scheduled job (`gym_management.gym_management.utils.tasks`) expires
Memberships and PT Package Purchases that have passed their end/expiry date, and
keeps the affected Gym Member / PT Package Purchase status fields current.

Three roles are created on install: **Gym Manager**, **Gym Staff**, **Gym
Trainer**.

#### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI.
From your bench directory:

```bash
bench get-app gym_management /path/to/gym_management
bench --site your-site install-app gym_management
```

If you're working inside this repo (it was generated straight into your `apps/`
folder), just run:

```bash
bench --site your-site install-app gym_management
bench --site your-site migrate
```

#### License

mit

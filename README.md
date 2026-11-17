# Giving Circle

A website and admin panel for a community giving group: members give £10–£20 a month,
and the money goes directly to people in need.

Built with Django, the Unfold admin theme, and SQLite (local) / PostgreSQL (live).

## What's inside

| Folder | What it does |
|---|---|
| `donations/` | Donors, monthly plans, donations, totals (`reports.py`) |
| `aid/` | Recipients (people/families helped) and payouts |
| `stories/` | Public updates for the website |
| `website/` | Public website pages, sign-up form, website settings & FAQs |
| `config/` | Settings, URLs, admin dashboard |
| `templates/admin/index.html` | Admin dashboard page |

## Run it on your computer

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then edit .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://localhost:8000/ for the website and http://localhost:8000/admin/ for the admin panel.

Bank details, contact info, page text and FAQs are edited in the admin under **Website**.

Optional made-up demo data (local only):

```bash
python manage.py seed_demo           # or --reset to wipe and recreate
```

## Tests

```bash
python manage.py test
```

## Privacy

Recipient names, phone numbers and notes stay private in the admin panel. Only the
**display name** of recipients who gave consent is used on the public website.
Donors appear as "Anonymous" unless "Show name publicly" is ticked.

## Putting it online

See [DEPLOY.md](DEPLOY.md) for step-by-step instructions for PythonAnywhere's free plan.

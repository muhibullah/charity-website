# Putting the site online (PythonAnywhere, free plan)

This takes about 20 minutes. You only need a web browser — everything happens on
pythonanywhere.com.

Throughout this guide, replace **`USERNAME`** with the PythonAnywhere username you pick.
Your site will live at **`https://USERNAME.eu.pythonanywhere.com`**.

The live site is currently set up at **https://yaawar.eu.pythonanywhere.com** (username `yaawar`).

---

## 1. Create the account

1. Go to **https://eu.pythonanywhere.com** (the EU site keeps donors' data in Europe, which
   suits UK data-protection rules).
2. Click **Pricing & signup → Create a Beginner account** (free).
3. Choose your username carefully — it becomes part of the web address
   (e.g. `givingcircle` → `givingcircle.eu.pythonanywhere.com`).
4. Confirm your email address.

## 2. Copy the code onto the server

1. Open the **Consoles** tab → under "Start a new console" click **Bash**.
2. Paste these lines one at a time (press Enter after each):

```bash
git clone https://github.com/muhibullah/charity-website.git
cd charity-website
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

The last one takes a couple of minutes.

## 3. Create the settings file (`.env`)

Still in the same console, paste this whole block in one go — but first change
`USERNAME` (it appears 2 times) and the group name:

```bash
cat > .env <<EOF
DEBUG=false
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
SITE_NAME=Yaawar
ALLOWED_HOSTS=USERNAME.eu.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://USERNAME.eu.pythonanywhere.com
EOF
```

## 4. Set up the database and admin login

```bash
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python manage.py createsuperuser
```

`createsuperuser` asks for a username, email and password — this is how you'll log in to
`/admin/`. Use a strong password you don't use anywhere else.

The live database starts **empty** (apart from the default FAQs) — none of the demo data from
your laptop is copied.

## 5. Create the web app

1. Open the **Web** tab → **Add a new web app** → **Next**.
2. Choose **Manual configuration** (not "Django") → **Python 3.12** → **Next**.
3. On the page that opens, fill in these sections:

**Code**
- Source code: `/home/USERNAME/charity-website`
- Working directory: `/home/USERNAME/charity-website`

**Virtualenv**
- Enter path: `/home/USERNAME/charity-website/.venv`

**WSGI configuration file** — click the link (e.g. `/var/www/USERNAME_eu_pythonanywhere_com_wsgi.py`),
delete *everything* in it, paste this, change `USERNAME`, then click **Save**:

```python
import os
import sys

path = "/home/USERNAME/charity-website"
if path not in sys.path:
    sys.path.insert(0, path)

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**Static files** — add these three rows (URL → Directory):

| URL | Directory |
|---|---|
| `/static/` | `/home/USERNAME/charity-website/staticfiles` |
| `/media/stories/` | `/home/USERNAME/charity-website/media/stories` |
| `/media/site/` | `/home/USERNAME/charity-website/media/site` |

> Do **not** add a row for `/media/` or `/media/payout-proofs/`. Payout receipts are private and
> the site only shows them to logged-in admins.

**Security**
- Turn **Force HTTPS** on.

4. Scroll to the top and click the big green **Reload** button.

## 6. Check it works

- Open `https://USERNAME.eu.pythonanywhere.com` — you should see the home page.
- Open `https://USERNAME.eu.pythonanywhere.com/admin/` and log in.
- Go to **Website → Website settings** and fill in your headline, intro, contact email,
  WhatsApp link and bank details. Upload a hero photo if you have one.
- Add your existing WhatsApp-group donors under **Money in → Donors**.

If you see "Something went wrong": **Web** tab → **Error log** (link near the bottom) shows why.

---

## Keeping it running

- **Every month** log in, open the **Web** tab and click **"Run until 1 month from today"**.
  PythonAnywhere emails a reminder a week before. If you forget, the site switches off (nothing
  is lost — click the button to switch it back on).
- **Back up the database** regularly: **Files** tab → `charity-website/` → download
  `db.sqlite3`. Keep the copies somewhere private — they contain donors' details.

## Updating the site after changes

When new code has been pushed to GitHub, open a **Bash** console and run:

```bash
cd charity-website
git pull
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput
```

Then click **Reload** on the **Web** tab.

## Free plan limits (worth knowing)

- One website, 512 MB of disk space (photos count towards this).
- Your own domain name (e.g. `givingcircle.org.uk`) needs the paid "Hacker" plan.
- The server can only contact approved websites — this matters later for card payments (Stripe)
  and sending emails.

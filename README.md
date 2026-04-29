# 🧳 JobBoard — Full-Stack Django Job Portal

> A complete, production-grade job portal built with Django. Supports job seekers, employers, and administrators with dedicated dashboards, real-time application tracking, and a professional UI.

---

## ✨ Features

### 👤 Job Seekers
- Browse & search jobs by title, location, type, and category
- Apply with resume upload + cover letter
- Track application status (Pending → Reviewed → Shortlisted / Rejected)
- Complete profile with skills, education, experience, and portfolio link

### 🏢 Employers
- Post and manage job listings
- View all incoming applications per listing
- Update application status with one click
- Separate employer dashboard

### 🔐 Admins / Moderators
- Approve or reject job listings before they go live
- Full Django admin panel with rich UI (search, filters, bulk actions)
- View all users, jobs, and applications with inline editing

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, Django 5.2 |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Frontend | HTML5, CSS3, Bootstrap Icons |
| Fonts | Google Fonts (Inter, Syne) |
| File Serving | WhiteNoise (static), Django media (uploads) |
| Production | Gunicorn WSGI server |

---

## 🚀 Quick Start

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/your-username/jobboard.git
cd jobboard

python -m venv env
source env/bin/activate        # Windows: env\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your SECRET_KEY and other settings
```

### 3. Apply Migrations
```bash
python manage.py migrate
```

### 4. Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

### 5. Seed Sample Data (Optional)
```bash
python manage.py seed_data
# Creates 8 sample jobs, 10 categories, and two demo accounts:
#   employer_demo / demo1234
#   seeker_demo   / demo1234
```

### 6. Run Development Server
```bash
python manage.py runserver
```
Open **http://127.0.0.1:8000/** in your browser.

---

## 📁 Project Structure

```
jobboard/
├── jobboard/                    # Project config
│   ├── settings.py              # All settings (env-aware)
│   ├── urls.py                  # Root URL config
│   ├── wsgi.py / asgi.py
│   └── context_processors.py
│
├── jobs/                        # Main application
│   ├── models.py                # Job, Application, Profile, Category
│   ├── views.py                 # All views (public, employer, admin, profile)
│   ├── forms.py                 # JobForm, RegisterForm, ProfileForm
│   ├── urls.py                  # App URL patterns
│   ├── admin.py                 # Rich Django admin configuration
│   ├── decorators.py            # @employer_required, @job_seeker_required, @admin_required
│   ├── signals.py               # Auto-create Profile on User creation
│   ├── context_processors.py    # is_employer, is_job_seeker, is_admin in all templates
│   ├── migrations/
│   └── management/
│       └── commands/
│           └── seed_data.py     # python manage.py seed_data
│
├── templates/                   # Global templates
│   ├── base.html                # Navbar, alerts, footer, responsive layout
│   └── registration/
│       ├── login.html
│       └── register.html
│
├── jobs/templates/              # App templates
│   ├── jobs/
│   │   ├── home.html            # Landing page with hero, stats, categories
│   │   ├── job_list.html        # Searchable + filterable job listings with pagination
│   │   ├── job_detail.html      # Full job page with sticky apply sidebar
│   │   ├── job_form.html        # Create / edit job listing
│   │   ├── apply.html           # Application form with drag-and-drop upload
│   │   ├── applied_jobs.html    # Job seeker application tracker
│   │   ├── employer_jobs.html   # Employer listing manager
│   │   ├── approve_jobs.html    # Admin moderation panel
│   │   └── unauthorized.html
│   ├── accounts/
│   │   ├── profile.html
│   │   └── edit_profile.html
│   └── employer/
│       └── applications.html    # Employer application manager with status update
│
├── media/                       # User uploads (resumes)
├── staticfiles/                 # Collected static files (production)
├── requirements.txt
├── .env.example
├── .gitignore
└── manage.py
```

---

## 🔗 URL Reference

| URL | Name | Access |
|---|---|---|
| `/` | `home` | Public |
| `/jobs/` | `job_list` | Public |
| `/job/<id>/` | `job_detail` | Public |
| `/register/` | `register` | Guest |
| `/accounts/login/` | `login` | Guest |
| `/accounts/logout/` | `logout` | Auth |
| `/job/<id>/apply/` | `apply_job` | Job Seeker |
| `/my-applications/` | `applied_jobs` | Job Seeker |
| `/profile/<id>/` | `profile` | Auth |
| `/profile/edit/` | `edit_profile` | Auth |
| `/employer/jobs/` | `employer_jobs` | Employer |
| `/employer/jobs/new/` | `job_create` | Employer |
| `/employer/jobs/<id>/edit/` | `job_edit` | Employer |
| `/employer/applications/` | `employer_applications` | Employer |
| `/moderate/jobs/` | `approve_jobs` | Superuser |
| `/moderate/jobs/<id>/approve/` | `approve_job` | Superuser |
| `/moderate/jobs/<id>/reject/` | `reject_job` | Superuser |
| `/admin/` | Django Admin | Superuser |

---

## 👥 User Roles

| Role | How to get it | Capabilities |
|---|---|---|
| **Job Seeker** | Select at registration | Browse, apply, track applications, manage profile |
| **Employer** | Select at registration | Post jobs, manage listings, review applicants |
| **Admin/Superuser** | `createsuperuser` command | All employer permissions + job moderation + Django admin |

---

## 🗄 Data Models

### `Profile` (extends User)
| Field | Type | Description |
|---|---|---|
| role | CharField | `job_seeker` or `employer` |
| resume | FileField | Uploaded CV |
| skills | CharField | Comma-separated skills |
| education | TextField | Education history |
| experience | TextField | Work experience |
| bio | TextField | Professional summary |
| phone | CharField | Contact number |
| location | CharField | City, Country |
| website | URLField | Portfolio link |

### `Job`
| Field | Type | Description |
|---|---|---|
| title | CharField | Job title |
| company_name | CharField | Employer company |
| description | TextField | Full job description |
| location | CharField | Job location |
| salary | DecimalField | Annual salary (optional) |
| job_type | CharField | Full-Time, Part-Time, Remote, etc. |
| experience | IntegerField | Years required |
| category | ForeignKey | Job category |
| is_approved | BooleanField | Admin-controlled visibility |
| posted_by | ForeignKey | Employer user |

### `Application`
| Field | Type | Description |
|---|---|---|
| job | ForeignKey | Related job |
| user | ForeignKey | Applicant |
| resume | FileField | Uploaded resume |
| cover_letter | TextField | Applicant's cover letter |
| status | CharField | pending → reviewed → shortlisted / rejected |

### `Category`
Simple model with `name` field. Jobs are grouped by category.

---

## 🚢 Deployment (Render / Railway / Fly.io)

1. Set environment variables:
   ```
   SECRET_KEY=your-production-secret-key
   DEBUG=False
   ALLOWED_HOSTS=your-domain.com
   ```

2. Add a `Procfile`:
   ```
   web: gunicorn jobboard.wsgi:application
   ```

3. On deploy:
   ```bash
   python manage.py migrate
   python manage.py collectstatic --no-input
   python manage.py createsuperuser
   ```

---

## 🤝 Contributing

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit: `git commit -m "Add: your feature"`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

<div align="center">
  Built with ❤️ using <strong>Django 5.2</strong> · Python · SQLite
</div>

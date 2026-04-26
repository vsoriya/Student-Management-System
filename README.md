# Student Management System

A larger Flask student management system with login/register, roles, students, classes, subjects, scores, attendance, report cards, Excel/PDF export, migrations, and SQLite/MySQL support.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask --app run.py init-db
flask --app run.py create-admin
python run.py
```

Open `http://127.0.0.1:5000` and log in with:

- Email: `admin@example.com`
- Password: `admin123`

## MySQL

Create a database named `student_management`, then set this in `.env`:

```bash
DATABASE_URL=mysql+pymysql://root:password@localhost/student_management
```

Then run:

```bash
flask --app run.py db init
flask --app run.py db migrate -m "initial database"
flask --app run.py db upgrade
flask --app run.py create-admin
```

## Features

- Auth: register, login, logout
- Roles: admin, teacher, student stored on each user
- Student CRUD with search, class filter, and pagination
- Class/grade CRUD
- Subject CRUD
- Scores per subject
- Attendance by date and class
- Report cards
- Export Excel and PDF
- SQLite backup command: `flask --app run.py backup-db`

For MySQL backup, use:

```bash
mysqldump -u root -p student_management > backups/backup.sql
```

## Vercel Deployment

This project includes `api/index.py` and `vercel.json` for Vercel.

Set these environment variables in Vercel:

```bash
SECRET_KEY=your-production-secret
DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:PORT/student_db?charset=utf8mb4
```

Do not use `localhost` for Vercel MySQL. Use a hosted MySQL database such as PlanetScale, Aiven, Railway, Render, AWS RDS, or another public MySQL provider.

# Nutrilog

A Flask web app for tracking nutritional intake. Build recipes from a food database, view per-nutrient breakdowns, and compare against Nordic Nutrition Recommendations (NNR) based on your age, sex, and weight.

## Features

- User registration and login
- Recipe builder with food ingredient search (English and Danish food names)
- Nutrient breakdown per recipe (energy, macros, vitamins, minerals, etc.)
- Daily overview — combine multiple recipes to see your total intake for the day
- NNR comparison — see how your intake stacks up against recommended values
- User profile with age, sex, and weight for personalised recommendations

## Prerequisites

- Python 3.10+
- PostgreSQL

## Setup

**1. Clone the repo**

```bash
git clone https://github.com/greippurt/Nutrilog.git
cd Nutrilog
```

**2. Create and activate a virtual environment**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

```bash
cp .env.example .env
```

Edit `.env` and set your PostgreSQL connection string:

```
DATABASE_URL=postgresql://localhost:5432/myapp
```

**5. Create the database and load food data**

```bash
createdb myapp
psql myapp < myapp_food_groups_2026-06-02_173256.sql
psql myapp < myapp_recipe_ingredients_2026-06-02_173309.sql
```

**6. Create application tables**

```bash
python init_db.py
```

**7. Run the app**

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

## Project Structure

```
Nutrilog/
├── app.py              # Flask routes and application logic
├── db.py               # PostgreSQL connection helpers
├── init_db.py          # One-time table setup script
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── templates/          # Jinja2 HTML templates
└── *.sql               # Food database seed data
```

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | Flask session secret (defaults to a dev key — set this in production) |

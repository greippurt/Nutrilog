# Nutrilog

A Flask web app for tracking nutritional intake. Build recipes from a food database, view per-nutrient breakdowns, and compare against Nordic Nutrition Recommendations (NNR) based on your age, sex, and weight.
Please see https://web-production-38130.up.railway.app/ for deployed application.
Values of nutrients have been pulled from https://fcdb.fooddata.dk/search, a public database of the nutritional value of food.
The daily recommend intake has been pulled from Nordic Nutrition Recommendations 2023 (https://pub.norden.org/nord2023-003/recommendations.html#lnk8a6f4ce4-9a42-4838-ad90-2ce2a2ac9209)

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
DATABASE_URL=postgresql://postgres:password@localhost:5432/postgres
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
├── db.py               # PostgreSQL connection script
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

## How to use the program 

1. Start by creating a user account. During registration, you will be asked to provide your name,     email address, sex, age, and weight. This information is used to personalise nutritional recommendations.
2. After logging in, click "+ New Recipe" to create a new recipe. Enter a name for the recipe and add the desired ingredients using the food search function. For each ingredient, specify the amount in grams.
3. Once all ingredients have been added, save the recipe. The recipe will then be stored in your account and can be viewed or edited later.
4. After saving a recipe, Nutrilog calculates its nutritional content and displays a detailed overview. This includes macronutrients, vitamins, minerals, and other nutritional values based on the selected ingredients and quantities.
5. Multiple recipes can be selected and combined in the daily overview page. This feature shows the total nutritional intake across all selected recipes and compares it with the Nordic Nutrition Recommendations (NNR).

## AI Declaratiom 

We have used generative AI as as a tool for this assignment. It has been used as to provide guidance on how certain features could be implemented, primarily html. It has also assisted us with debugging and fixing errors.

## Openeing the ER/Diagram

To see the ER/Diagram you need to have the file downloaded onto your computer and then open it from your folders. It will the send you to a browser where you can see the diagram.
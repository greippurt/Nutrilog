"""Run once to set up application tables. Users table already exists; we add password_hash to it."""
import db

# Add password_hash to the existing users table if it isn't there yet
db.execute("""
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS password_hash TEXT
""")

db.execute("""
    CREATE TABLE IF NOT EXISTS recipes (
        recipe_id  SERIAL PRIMARY KEY,
        name       TEXT NOT NULL,
        user_id    INTEGER REFERENCES users(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

db.execute("""
    CREATE TABLE IF NOT EXISTS recipe_ingredients (
        recipe_id INTEGER REFERENCES recipes(recipe_id) ON DELETE CASCADE,
        food_id   INTEGER REFERENCES foods(food_id),
        amount_g  NUMERIC NOT NULL,
        PRIMARY KEY (recipe_id, food_id)
    )
""")

print("Done — password_hash column added to users, recipes and recipe_ingredients created (or already exist).")

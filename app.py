from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os
import db
import re 

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── Auth ───────────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        users = db.query("SELECT * FROM users WHERE email = %s", (email,))
        if users and users[0]["password_hash"] and check_password_hash(users[0]["password_hash"], password):
            session["user_id"] = users[0]["id"]
            session["username"] = users[0]["name"] or users[0]["email"]
            return redirect(url_for("index"))
        flash("Invalid email or password.")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        name      = request.form["name"].strip()
        email     = request.form["email"].strip().lower()
        password  = request.form["password"]
        confirm   = request.form["confirm"]
        sex       = request.form["sex"]
        age       = int(request.form["age"])
        weight_kg = float(request.form["weight_kg"])

        lowerCase = re.search("[a-z]", password);
        upperCase = re.search("[A-Z]", password);
        number = re.search("[0-9]", password);
        specialChar = re.search("[@£$€#¤%&/()=´`¨^'*~|]", password)

        if password != confirm:
            flash("Passwords do not match.")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.")
        elif specialChar == None:
            flash("Password must have at least one special character from following list: @£$€#¤%&/()=´`¨^'*~|")
        elif lowerCase == None or upperCase == None:
            flash("Password must have at least one upper and lower case letter")
        elif number == None:
            flash("Password must contain at least one number")    
        else:
            existing = db.query("SELECT id FROM users WHERE email = %s", (email,))
            if existing:
                flash("An account with that email already exists.")
            else:
                db.execute(
                    "INSERT INTO users (name, email, password_hash, sex, age, weight_kg) VALUES (%s, %s, %s, %s, %s, %s)",
                    (name, email, generate_password_hash(password), sex, age, weight_kg),
                )
                user = db.query("SELECT * FROM users WHERE email = %s", (email,))
                session["user_id"] = user[0]["id"]
                session["username"] = user[0]["name"] or user[0]["email"]
                return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── Home: list recipes for the logged-in user ──────────────────────────────────

@app.route("/")
@login_required
def index():
    recipes = db.query(
        "SELECT * FROM recipes WHERE user_id = %s ORDER BY created_at DESC",
        (session["user_id"],),
    )
    return render_template("index.html", recipes=recipes)


# ── Food search API (used by the ingredient search box) ───────────────────────

@app.route("/api/foods")
@login_required
def search_foods():
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify([])
    results = db.query(
        """
        SELECT food_id, name_english, name_danish
        FROM foods
        WHERE name_english ILIKE %s OR name_danish ILIKE %s
        ORDER BY name_english
        LIMIT 20
        """,
        (f"%{q}%", f"%{q}%"),
    )
    return jsonify([dict(r) for r in results])


# ── Create recipe ──────────────────────────────────────────────────────────────

@app.route("/recipes/new")
@login_required
def recipe_new():
    return render_template("recipe_new.html")


@app.route("/recipes", methods=["POST"])
@login_required
def recipe_create():
    name = request.form["name"].strip()
    food_ids = request.form.getlist("food_id")
    amounts = request.form.getlist("amount")

    (recipe_id,) = db.execute_returning(
        "INSERT INTO recipes (name, user_id) VALUES (%s, %s) RETURNING recipe_id",
        (name, session["user_id"]),
    )

    for food_id, amount in zip(food_ids, amounts):
        if food_id and amount:
            db.execute(
                "INSERT INTO recipe_ingredients (recipe_id, food_id, amount_g) VALUES (%s, %s, %s)",
                (recipe_id, int(food_id), float(amount)),
            )

    return redirect(url_for("recipe_view", recipe_id=recipe_id))


# ── View recipe nutrients ──────────────────────────────────────────────────────

@app.route("/recipes/<int:recipe_id>")
@login_required
def recipe_view(recipe_id):
    recipe = db.query(
        "SELECT * FROM recipes WHERE recipe_id = %s AND user_id = %s",
        (recipe_id, session["user_id"]),
    )
    if not recipe:
        return "Recipe not found", 404
    recipe = recipe[0]

    ingredients = db.query(
        """
        SELECT f.name_english, f.name_danish, ri.amount_g
        FROM recipe_ingredients ri
        JOIN foods f ON f.food_id = ri.food_id
        WHERE ri.recipe_id = %s
        ORDER BY f.name_english
        """,
        (recipe_id,),
    )

    nutrients = db.query(
        """
        SELECT
            p.parameter_id,
            p.name_english,
            p.unit,
            p.parameter_group_name_english AS nutrient_group,
            ROUND(SUM(n.res_val * ri.amount_g / 100)::numeric, 2) AS total
        FROM recipe_ingredients ri
        JOIN nutrient_values n ON n.food_id = ri.food_id
        JOIN parameters p      ON p.parameter_id = n.parameter_id
        WHERE ri.recipe_id = %s
          AND n.res_val IS NOT NULL
        GROUP BY p.parameter_id, p.name_english, p.unit, p.parameter_group_name_english, p.sort_key
        ORDER BY p.sort_key
        """,
        (recipe_id,),
    )

    user = db.query(
        "SELECT age, sex, weight_kg FROM users WHERE id = %s",
        (session["user_id"],),
    )[0]

    nnr_map = {}
    if user["age"] and user["sex"]:
        rows = db.query(
            """
            SELECT parameter_id, recommended, unit
            FROM nnr_recommendations
            WHERE sex = %s
              AND age_min <= %s
              AND (age_max IS NULL OR age_max >= %s)
            """,
            (user["sex"], user["age"], user["age"]),
        )
        for r in rows:
            rec = float(r["recommended"])
            if r["unit"] == "g/kg" and user["weight_kg"]:
                rec = rec * float(user["weight_kg"])
            nnr_map[r["parameter_id"]] = rec

    return render_template(
        "recipe_view.html",
        recipe=recipe,
        ingredients=ingredients,
        nutrients=nutrients,
        nnr_map=nnr_map,
    )


# ── Daily overview (multiple recipes combined) ────────────────────────────────

@app.route("/daily")
@login_required
def daily_view():
    ids = request.args.getlist("ids", type=int)
    if not ids:
        return redirect(url_for("index"))

    recipes = db.query(
        "SELECT recipe_id, name FROM recipes WHERE recipe_id = ANY(%s) AND user_id = %s",
        (ids, session["user_id"]),
    )
    if not recipes:
        return "No recipes found", 404

    nutrients = db.query(
        """
        SELECT
            p.parameter_id,
            p.name_english,
            p.unit,
            p.parameter_group_name_english AS nutrient_group,
            ROUND(SUM(n.res_val * ri.amount_g / 100)::numeric, 2) AS total
        FROM recipe_ingredients ri
        JOIN nutrient_values n ON n.food_id = ri.food_id
        JOIN parameters p      ON p.parameter_id = n.parameter_id
        WHERE ri.recipe_id = ANY(%s)
          AND n.res_val IS NOT NULL
        GROUP BY p.parameter_id, p.name_english, p.unit, p.parameter_group_name_english, p.sort_key
        ORDER BY p.sort_key
        """,
        (ids,),
    )

    user = db.query(
        "SELECT age, sex, weight_kg FROM users WHERE id = %s",
        (session["user_id"],),
    )[0]
    nnr_map = {}
    if user["age"] and user["sex"]:
        rows = db.query(
            """
            SELECT parameter_id, recommended, unit
            FROM nnr_recommendations
            WHERE sex = %s
              AND age_min <= %s
              AND (age_max IS NULL OR age_max >= %s)
            """,
            (user["sex"], user["age"], user["age"]),
        )
        for r in rows:
            rec = float(r["recommended"])
            if r["unit"] == "g/kg" and user["weight_kg"]:
                rec = rec * float(user["weight_kg"])
            nnr_map[r["parameter_id"]] = rec

    return render_template(
        "daily_view.html",
        recipes=recipes,
        nutrients=nutrients,
        nnr_map=nnr_map,
    )


# ── User profile ──────────────────────────────────────────────────────────────

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        age       = request.form.get("age", "").strip()
        weight_kg = request.form.get("weight_kg", "").strip()
        if not age or not weight_kg:
            flash("Age and weight are required.")
        else:
            db.execute(
                "UPDATE users SET age = %s, weight_kg = %s WHERE id = %s",
                (int(age), float(weight_kg), session["user_id"]),
            )
            flash("Profile updated.")
        return redirect(url_for("profile"))
    user = db.query(
        "SELECT name, email, age, sex, weight_kg FROM users WHERE id = %s",
        (session["user_id"],),
    )[0]
    return render_template("profile.html", user=user)


# ── Edit recipe ───────────────────────────────────────────────────────────────

@app.route("/recipes/<int:recipe_id>/edit")
@login_required
def recipe_edit(recipe_id):
    recipe = db.query(
        "SELECT * FROM recipes WHERE recipe_id = %s AND user_id = %s",
        (recipe_id, session["user_id"]),
    )
    if not recipe:
        return "Recipe not found", 404
    ingredients = db.query(
        """
        SELECT ri.food_id, f.name_english, ri.amount_g
        FROM recipe_ingredients ri
        JOIN foods f ON f.food_id = ri.food_id
        WHERE ri.recipe_id = %s
        ORDER BY f.name_english
        """,
        (recipe_id,),
    )
    return render_template("recipe_edit.html", recipe=recipe[0], ingredients=ingredients)


@app.route("/recipes/<int:recipe_id>/edit", methods=["POST"])
@login_required
def recipe_update(recipe_id):
    recipe = db.query(
        "SELECT recipe_id FROM recipes WHERE recipe_id = %s AND user_id = %s",
        (recipe_id, session["user_id"]),
    )
    if not recipe:
        return "Recipe not found", 404
    name = request.form["name"].strip()
    food_ids = request.form.getlist("food_id")
    amounts = request.form.getlist("amount")
    db.execute("UPDATE recipes SET name = %s WHERE recipe_id = %s", (name, recipe_id))
    db.execute("DELETE FROM recipe_ingredients WHERE recipe_id = %s", (recipe_id,))
    for food_id, amount in zip(food_ids, amounts):
        if food_id and amount:
            db.execute(
                "INSERT INTO recipe_ingredients (recipe_id, food_id, amount_g) VALUES (%s, %s, %s)",
                (recipe_id, int(food_id), float(amount)),
            )
    return redirect(url_for("recipe_view", recipe_id=recipe_id))


# ── Delete recipe ──────────────────────────────────────────────────────────────

@app.route("/recipes/<int:recipe_id>/delete", methods=["POST"])
@login_required
def recipe_delete(recipe_id):
    db.execute(
        "DELETE FROM recipes WHERE recipe_id = %s AND user_id = %s",
        (recipe_id, session["user_id"]),
    )
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)

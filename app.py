import os
import sqlite3
import random
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)
DB_NAME = 'recipes.db'

# Initialize Database
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            ingredients TEXT,
            instructions TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Templates
BASE_HTML = '''
<!doctype html>
<html lang="en">
<head>
    <title>Recipe Book & Daily Meal Prep</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-light bg-light mb-4">
    <div class="container-fluid">
        <a class="navbar-brand" href="{{ url_for('index') }}">Recipe Book</a>
        <a class="nav-link" href="{{ url_for('add') }}">Add Recipe</a>
        <a class="nav-link" href="{{ url_for('book') }}">All Recipes</a>
        <a class="nav-link" href="{{ url_for('daily_meal') }}">Daily Meal Prep</a>
    </div>
</nav>
<div class="container">
    {% block body %}{% endblock %}
</div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(
        BASE_HTML + '''
        {% block body %}
        <div class="text-center">
            <h1>Welcome to Recipe Book & Daily Meal Prep!</h1>
            <p>Add your recipes, organize them, and get daily meal plans.</p>
        </div>
        {% endblock %}
        '''
    )

# Add Recipe
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        title = request.form['title']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('INSERT INTO recipes (title, ingredients, instructions) VALUES (?, ?, ?)', (title, ingredients, instructions))
        conn.commit()
        conn.close()
        return redirect(url_for('book'))
    return render_template_string(
        BASE_HTML + '''
        {% block body %}
        <h2>Add New Recipe</h2>
        <form method="post" class="mb-3">
            <input type="text" name="title" placeholder="Recipe Title" class="form-control mb-2" required>
            <textarea name="ingredients" placeholder="Ingredients (one per line)" class="form-control mb-2" rows="4" required></textarea>
            <textarea name="instructions" placeholder="Instructions" class="form-control mb-2" rows="6" required></textarea>
            <button type="submit" class="btn btn-primary">Add Recipe</button>
        </form>
        {% endblock %}
        '''
    )

# View All Recipes
@app.route('/book')
def book():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, title FROM recipes')
    recipes = c.fetchall()
    conn.close()
    return render_template_string(
        BASE_HTML + '''
        {% block body %}
        <h2>Recipe Book</h2>
        <ul class="list-group mb-4">
        {% for rid, title in recipes %}
            <li class="list-group-item d-flex justify-content-between align-items-center">
                <a href="{{ url_for('view_recipe', recipe_id=rid) }}">{{ title }}</a>
                <form method="post" action="{{ url_for('delete_recipe', recipe_id=rid) }}" style="display:inline;">
                    <button type="submit" class="btn btn-danger btn-sm">Delete</button>
                </form>
            </li>
        {% else %}
            <li class="list-group-item">No recipes yet.</li>
        {% endfor %}
        </ul>
        {% endblock %}
        ''',
        recipes=recipes
    )

# View One Recipe
@app.route('/recipe/<int:recipe_id>')
def view_recipe(recipe_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT title, ingredients, instructions FROM recipes WHERE id=?', (recipe_id,))
    recipe = c.fetchone()
    conn.close()
    return render_template_string(
        BASE_HTML + '''
        {% block body %}
        <h2>{{ recipe[0] }}</h2>
        <h4>Ingredients</h4>
        <pre>{{ recipe[1] }}</pre>
        <h4>Instructions</h4>
        <pre>{{ recipe[2] }}</pre>
        <a href="{{ url_for('edit_recipe', recipe_id=recipe_id) }}" class="btn btn-warning">Edit</a>
        <a href="{{ url_for('book') }}" class="btn btn-secondary">Back to Book</a>
        {% endblock %}
        ''',
        recipe=recipe, recipe_id=recipe_id
    )

# Edit Recipe
@app.route('/edit/<int:recipe_id>', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if request.method == 'POST':
        title = request.form['title']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        c.execute('UPDATE recipes SET title=?, ingredients=?, instructions=? WHERE id=?', (title, ingredients, instructions, recipe_id))
        conn.commit()
        conn.close()
        return redirect(url_for('view_recipe', recipe_id=recipe_id))
    c.execute('SELECT title, ingredients, instructions FROM recipes WHERE id=?', (recipe_id,))
    recipe = c.fetchone()
    conn.close()
    return render_template_string(
        BASE_HTML + '''
        {% block body %}
        <h2>Edit Recipe</h2>
        <form method="post" class="mb-3">
            <input type="text" name="title" value="{{ recipe[0] }}" class="form-control mb-2" required>
            <textarea name="ingredients" class="form-control mb-2" rows="4" required>{{ recipe[1] }}</textarea>
            <textarea name="instructions" class="form-control mb-2" rows="6" required>{{ recipe[2] }}</textarea>
            <button type="submit" class="btn btn-primary">Save Changes</button>
        </form>
        {% endblock %}
        ''',
        recipe=recipe
    )

# Delete Recipe
@app.route('/delete_recipe/<int:recipe_id>', methods=['POST'])
def delete_recipe(recipe_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM recipes WHERE id=?', (recipe_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('book'))

# Daily Meal Prep
@app.route('/daily_meal')
def daily_meal():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT title, ingredients FROM recipes')
    recipes = c.fetchall()
    conn.close()
    chosen = random.sample(recipes, min(len(recipes), 3)) if recipes else []
    return render_template_string(
        BASE_HTML + '''
        {% block body %}
        <h2>Daily Meal Prep</h2>
        {% if chosen %}
            <p>Today's suggested meals:</p>
            <div class="row">
            {% for title, ingredients in chosen %}
                <div class="col-md-4">
                    <div class="card mb-3">
                        <div class="card-header"><strong>{{ title }}</strong></div>
                        <div class="card-body">
                            <h6>Ingredients</h6>
                            <pre>{{ ingredients }}</pre>
                        </div>
                    </div>
                </div>
            {% endfor %}
            </div>
        {% else %}
            <div class="alert alert-warning">No recipes in book. Add some first!</div>
        {% endif %}
        {% endblock %}
        ''',
        chosen=chosen
    )

if __name__ == '__main__':
    app.run(debug=True)

from app.db.repo import get_recipe_count, list_recipes
print('count:', get_recipe_count())
print('top:', list_recipes(limit=2))

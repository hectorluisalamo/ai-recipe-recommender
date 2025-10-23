from app.db.repo import get_recipe_count, list_recipes

def test_recipe_count_positive():
    assert get_recipe_count() >= 10
    
def test_list_recipes_diet_filter():
    items = list_recipes(diet='vegan', limit=100)
    assert all(i['diet'] == 'vegan' for i in items)
    assert items, 'Expected some vegan recipes, got none'
from __future__ import annotations
import os
from sqlalchemy import (
    Table, Column, Integer, String, MetaData, Text, CheckConstraint, create_engine
)

DB_URL = os.getenv('DB_URL', 'sqlite:///data/recipes.db')
metadata = MetaData()

recipes = Table(
    'recipes',
    metadata,
    Column('id', String, primary_key=True),
    Column('title', String, nullable=False),
    Column('description', Text, nullable=True),
    Column('ingredients', Text, nullable=False),
    Column('cuisine', Text, nullable=False),
    Column('diet', String, nullable=False, server_default='none',),
    Column('time_minutes', Integer, nullable=False),
    Column('popularity', Integer, nullable=False, server_default='0'),
    Column('url', String, nullable=False, unique=True),
    CheckConstraint("diet IN ('none', 'keto', 'vegetarian', 'vegan', 'gluten-free')", name='ck_recipes_diet'),
)

feedback = Table(
    'feedback',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('recipe_id', String, nullable=False),
    Column('query', Text),
    Column('is_relevant', Integer),
    Column('timestamp', String, server_default='(datetime("now")'),
    CheckConstraint('is_relevant IN (0, 1)', name='ck_feedback_is_relevant'),
)

def get_engine(echo: bool = False):
    return create_engine(DB_URL, echo=echo, future=True)
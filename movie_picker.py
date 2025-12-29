# Movie Night Picker v0
# Run with: python3 movie_picker.py

import random

movies = [
    {
        "title": "The Matrix",
        "genre": "Sci-Fi",
        "runtime_minutes": 136,
    },
    {
        "title": "Inception",
        "genre": "Sci-Fi",
        "runtime_minutes": 148,
    },
    {
        "title": "The Grand Budapest Hotel",
        "genre": "Comedy",
        "runtime_minutes": 99,
    },
    {
        "title": "Parasite",
        "genre": "Thriller",
        "runtime_minutes": 132,
    },
]

selected_movie = random.choice(movies)

print("🎬 Tonight's Movie Pick")
print("----------------------")
print(f"Title: {selected_movie['title']}")
print(f"Genre: {selected_movie['genre']}")
print(f"Runtime: {selected_movie['runtime_minutes']} minutes")

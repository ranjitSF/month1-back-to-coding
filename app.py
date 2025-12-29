from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import random

app = FastAPI()

movies = [
    {"title": "The Matrix", "genre": "Sci-Fi", "runtime": 136},
    {"title": "Inception", "genre": "Sci-Fi", "runtime": 148},
    {"title": "The Grand Budapest Hotel", "genre": "Comedy", "runtime": 99},
    {"title": "Parasite", "genre": "Thriller", "runtime": 132},
]

@app.get("/", response_class=HTMLResponse)
def home():
    movie = random.choice(movies)
    return render_movie(movie)


@app.get("/pick", response_class=HTMLResponse)
def pick_again():
    movie = random.choice(movies)
    return render_movie(movie)


def render_movie(movie):
    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Movie Night Picker</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                background: linear-gradient(135deg, #0f172a, #020617);
                color: white;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }}
            .card {{
                background: rgba(255,255,255,0.08);
                padding: 24px 28px;
                border-radius: 16px;
                text-align: center;
                max-width: 320px;
                width: 90%;
                box-shadow: 0 20px 40px rgba(0,0,0,0.4);
            }}
            h1 {{
                font-size: 1.4rem;
                margin-bottom: 8px;
            }}
            .meta {{
                opacity: 0.85;
                margin-bottom: 16px;
            }}
            button {{
                background: #6366f1;
                color: white;
                border: none;
                padding: 12px 16px;
                border-radius: 12px;
                font-size: 1rem;
                cursor: pointer;
                width: 100%;
            }}
            button:hover {{
                background: #4f46e5;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🎬 Movie Night Pick</h1>
            <div class="meta"><strong>{movie['title']}</strong></div>
            <div class="meta">{movie['genre']} · {movie['runtime']} minutes</div>
            <form action="/">
                <button type="submit">🎲 Pick Again</button>
            </form>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
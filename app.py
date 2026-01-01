import os
import json
import uuid
import random
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse


app = FastAPI()
load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_READ_TOKEN = os.getenv("TMDB_READ_TOKEN")

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMG_SMALL = "https://image.tmdb.org/t/p/w92"
TMDB_IMG_CARD = "https://image.tmdb.org/t/p/w185"

EVENTS_FILE = Path("events.json")


# -----------------------------
# Persistence Helpers
# -----------------------------

def load_events() -> dict:
    if EVENTS_FILE.exists():
        return json.loads(EVENTS_FILE.read_text())
    return {}


def save_events(events: dict):
    EVENTS_FILE.write_text(json.dumps(events, indent=2))


def get_event(event_id: str) -> Optional[dict]:
    events = load_events()
    return events.get(event_id)


def save_event(event: dict):
    events = load_events()
    events[event["id"]] = event
    save_events(events)


# -----------------------------
# TMDB Helpers
# -----------------------------

def tmdb_headers():
    if TMDB_READ_TOKEN:
        return {
            "Authorization": f"Bearer {TMDB_READ_TOKEN}",
            "Content-Type": "application/json",
        }
    return {}


def tmdb_get(path: str, params: Optional[dict] = None) -> dict:
    """GET helper that uses bearer token if present, else api_key."""
    params = params or {}
    headers = tmdb_headers()

    if not headers and TMDB_API_KEY:
        params["api_key"] = TMDB_API_KEY

    resp = requests.get(f"{TMDB_BASE}{path}", params=params, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


def tmdb_movie_details(tmdb_id: str) -> Optional[dict]:
    """Fetch a single movie's details by TMDB id."""
    if not tmdb_id:
        return None
    try:
        m = tmdb_get(f"/movie/{tmdb_id}", params={"language": "en-US"})
        return {
            "tmdb_id": m.get("id"),
            "title": m.get("title") or "",
            "year": (m.get("release_date") or "")[:4],
            "poster_path": m.get("poster_path"),
            "rating": m.get("vote_average"),
        }
    except Exception:
        return None


def tmdb_search_first(title: str) -> Optional[dict]:
    """If user didn't pick from autocomplete, search and take best match."""
    title = (title or "").strip()
    if len(title) < 2:
        return None

    try:
        data = tmdb_get(
            "/search/movie",
            params={
                "query": title,
                "include_adult": "false",
                "language": "en-US",
                "page": 1,
            },
        )
        results = data.get("results", [])
        if not results:
            return None

        m = results[0]
        return {
            "tmdb_id": m.get("id"),
            "title": m.get("title") or title,
            "year": (m.get("release_date") or "")[:4],
            "poster_path": m.get("poster_path"),
            "rating": m.get("vote_average"),
        }
    except Exception:
        return None


# -----------------------------
# Shared Styles
# -----------------------------

def base_styles():
    return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0f172a, #020617);
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
            box-sizing: border-box;
        }
        .card {
            background: rgba(255,255,255,0.08);
            padding: 24px 28px;
            border-radius: 16px;
            text-align: center;
            max-width: 460px;
            width: 100%;
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        }
        h1 { font-size: 1.4rem; margin-bottom: 8px; }
        h2 { font-size: 1.1rem; margin: 16px 0 8px; opacity: 0.9; }
        .meta { opacity: 0.85; margin-bottom: 16px; }

        input, button {
            padding: 12px 16px;
            border-radius: 12px;
            font-size: 1rem;
            width: 100%;
            box-sizing: border-box;
            margin-bottom: 12px;
        }
        input {
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            color: white;
        }
        input::placeholder { color: rgba(255,255,255,0.5); }

        button {
            background: #6366f1;
            color: white;
            border: none;
            cursor: pointer;
        }
        button:hover { background: #4f46e5; }
        button.secondary {
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
        }
        button.secondary:hover { background: rgba(255,255,255,0.15); }
        button.danger { background: #dc2626; }
        button.danger:hover { background: #b91c1c; }

        .error {
            background: rgba(220, 38, 38, 0.2);
            border: 1px solid #dc2626;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 16px;
        }
        .success {
            background: rgba(34, 197, 94, 0.2);
            border: 1px solid #22c55e;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 16px;
        }

        .pick-list {
            text-align: left;
            margin: 16px 0;
        }
        .pick-item {
            background: rgba(255,255,255,0.05);
            padding: 12px;
            border-radius: 12px;
            margin-bottom: 10px;
        }
        .pick-name { font-weight: 700; margin-bottom: 6px; }

        .winner {
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            padding: 16px;
            border-radius: 12px;
            margin: 16px 0;
            text-align: left;
        }

        .link-box {
            background: rgba(255,255,255,0.1);
            padding: 12px;
            border-radius: 8px;
            word-break: break-all;
            margin: 12px 0;
        }

        /* Autocomplete */
        .movie-field { position: relative; }

        .suggestions {
            position: absolute;
            left: 0;
            right: 0;
            top: calc(100% - 8px);
            background: rgba(15, 23, 42, 0.98);
            border: 1px solid rgba(255,255,255,0.18);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0,0,0,0.45);
            display: none;
            z-index: 50;
        }

        .suggestion {
            display: flex;
            gap: 10px;
            align-items: center;
            padding: 10px 12px;
            cursor: pointer;
            border-top: 1px solid rgba(255,255,255,0.08);
        }
        .suggestion:first-child { border-top: none; }
        .suggestion:hover { background: rgba(255,255,255,0.08); }

        .poster {
            width: 32px;
            height: 48px;
            border-radius: 6px;
            object-fit: cover;
            background: rgba(255,255,255,0.08);
            flex: 0 0 auto;
        }

        .suggestion-title { font-size: 0.95rem; font-weight: 600; }
        .suggestion-meta { opacity: 0.75; font-size: 0.85rem; margin-top: 2px; }
        .suggestion-text { text-align: left; line-height: 1.1; }

        /* Movie cards */
        .movie-cards {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 8px;
        }

        .movie-card {
            display: flex;
            gap: 10px;
            align-items: center;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.10);
            padding: 10px;
            border-radius: 12px;
            width: 100%;
        }

        .movie-card img {
            width: 44px;
            height: 66px;
            border-radius: 8px;
            object-fit: cover;
            background: rgba(255,255,255,0.08);
            flex: 0 0 auto;
        }

        .movie-card .info {
            text-align: left;
            line-height: 1.2;
        }

        .movie-card .title {
            font-weight: 700;
            font-size: 0.95rem;
        }

        .movie-card .sub {
            opacity: 0.8;
            font-size: 0.85rem;
            margin-top: 4px;
        }
    """


# -----------------------------
# Home Page
# -----------------------------

@app.get("/", response_class=HTMLResponse)
def home():
    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Movie Night</title>
        <style>{base_styles()}</style>
    </head>
    <body>
        <div class="card">
            <h1>🎬 Movie Night</h1>
            <p class="meta">Create a movie night event and let your friends vote!</p>
            <form action="/api/events" method="post">
                <input type="text" name="title" placeholder="Event title (e.g., Friday Night)" required>
                <input type="date" name="date" required>
                <button type="submit">Create Event</button>
            </form>
        </div>
    </body>
    </html>
    """


# -----------------------------
# Create Event
# -----------------------------

@app.post("/api/events")
def create_event(title: str = Form(...), date: str = Form(...)):
    event_id = uuid.uuid4().hex[:8]
    event = {
        "id": event_id,
        "title": title,
        "date": date,
        "picks": [],
        "finalized": False,
        "selected_movie": None,
    }
    save_event(event)
    return RedirectResponse(url=f"/m/{event_id}", status_code=303)


# -----------------------------
# View Event
# -----------------------------

@app.get("/m/{event_id}", response_class=HTMLResponse)
def view_event(event_id: str, error: str = None, success: str = None):
    event = get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    error_html = f'<div class="error">{error}</div>' if error else ""
    success_html = f'<div class="success">{success}</div>' if success else ""

    # Build picks list HTML (movie cards)
    if event["picks"]:
        picks_html = '<div class="pick-list">'
        for pick in event["picks"]:
            picks_html += f'''
                <div class="pick-item">
                    <div class="pick-name">{pick.get("name","")}</div>
                    <div class="movie-cards">
            '''
            for m in pick.get("movies", []):
                title = m.get("title", "")
                year = m.get("year", "")
                rating = m.get("rating", None)
                poster_path = m.get("poster_path", None)

                poster_url = f"{TMDB_IMG_CARD}{poster_path}" if poster_path else ""
                poster_html = f'<img src="{poster_url}" alt="">' if poster_url else '<img src="" alt="" style="opacity:0;">'

                rating_str = f"⭐ {float(rating):.1f}" if rating is not None else ""
                year_str = year if year else ""
                meta = " • ".join([x for x in [year_str, rating_str] if x])

                picks_html += f'''
                    <div class="movie-card">
                        {poster_html}
                        <div class="info">
                            <div class="title">{title}</div>
                            <div class="sub">{meta}</div>
                        </div>
                    </div>
                '''
            picks_html += '''
                    </div>
                </div>
            '''
        picks_html += "</div>"
    else:
        picks_html = '<p class="meta">No picks yet. Be the first!</p>'

    share_url = f"/m/{event_id}"

    # If finalized, show winner (also with movie card styling)
    if event["finalized"]:
        winner = event["selected_movie"] or {"title": "Unknown", "poster_path": None, "year": "", "rating": None}
        w_title = winner.get("title", "Unknown")
        w_year = winner.get("year", "")
        w_rating = winner.get("rating", None)
        w_poster_path = winner.get("poster_path", None)
        w_poster_url = f"{TMDB_IMG_CARD}{w_poster_path}" if w_poster_path else ""
        w_poster_html = f'<img src="{w_poster_url}" alt="">' if w_poster_url else '<img src="" alt="" style="opacity:0;">'
        w_meta = " • ".join([x for x in [w_year if w_year else "", (f"⭐ {float(w_rating):.1f}" if w_rating is not None else "")] if x])

        return f"""
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{event["title"]} - Movie Night</title>
            <style>{base_styles()}</style>
        </head>
        <body>
            <div class="card">
                <h1>🎬 {event["title"]}</h1>
                <p class="meta">📅 {event["date"]}</p>

                <div class="winner">
                    <div style="opacity:0.9; margin-bottom:10px;">🎉 Tonight's Movie</div>
                    <div class="movie-card" style="margin:0; background: rgba(255,255,255,0.10);">
                        {w_poster_html}
                        <div class="info">
                            <div class="title">{w_title}</div>
                            <div class="sub">{w_meta}</div>
                        </div>
                    </div>
                </div>

                <h2>All Submissions</h2>
                {picks_html}

                <a href="/"><button class="secondary">Create New Event</button></a>
            </div>
        </body>
        </html>
        """

    # Not finalized: show form + autocomplete JS
    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{event["title"]} - Movie Night</title>
        <style>{base_styles()}</style>
    </head>
    <body>
        <div class="card">
            <h1>🎬 {event["title"]}</h1>
            <p class="meta">📅 {event["date"]}</p>
            {error_html}
            {success_html}

            <h2>Share This Link</h2>
            <div class="link-box">{share_url}</div>

            <h2>Submit Your Picks</h2>
            <form action="/api/events/{event_id}/picks" method="post">
                <input type="text" name="name" placeholder="Your name" required>

                <div class="movie-field">
                    <input type="text" id="movie1" name="movie1" placeholder="Movie pick #1" autocomplete="off" required>
                    <input type="hidden" id="movie1_tmdb_id" name="movie1_tmdb_id">
                    <div class="suggestions" id="movie1_suggestions"></div>
                </div>

                <div class="movie-field">
                    <input type="text" id="movie2" name="movie2" placeholder="Movie pick #2" autocomplete="off" required>
                    <input type="hidden" id="movie2_tmdb_id" name="movie2_tmdb_id">
                    <div class="suggestions" id="movie2_suggestions"></div>
                </div>

                <button type="submit">Submit Picks</button>
            </form>

            <h2>Current Submissions ({len(event["picks"])})</h2>
            {picks_html}

            <form action="/api/events/{event_id}/finalize" method="post" style="margin-top: 20px;">
                <button type="submit" class="danger">🎲 Finalize & Pick Winner</button>
            </form>
        </div>

        <script>
          function setupAutocomplete(inputId, hiddenId, suggestionsId) {{
            const input = document.getElementById(inputId);
            const hidden = document.getElementById(hiddenId);
            const box = document.getElementById(suggestionsId);

            let debounceTimer = null;

            function hide() {{
              box.style.display = "none";
              box.innerHTML = "";
            }}

            function show(results) {{
              if (!results || results.length === 0) {{
                hide();
                return;
              }}

              box.innerHTML = results.map(r => {{
                const year = r.year ? `• ${{r.year}}` : "";
                const rating = (r.rating !== null && r.rating !== undefined) ? `• ⭐ ${{Number(r.rating).toFixed(1)}}` : "";
                const poster = r.poster_path
                  ? `{TMDB_IMG_SMALL}${{r.poster_path}}`
                  : "";
                const posterHtml = poster
                  ? `<img class="poster" src="${{poster}}" alt="">`
                  : `<div class="poster"></div>`;

                const safeTitle = (r.title || "").replace(/"/g, '&quot;');

                return `
                  <div class="suggestion" data-id="${{r.tmdb_id}}" data-title="${{safeTitle}}">
                    ${{posterHtml}}
                    <div class="suggestion-text">
                      <div class="suggestion-title">${{r.title}}</div>
                      <div class="suggestion-meta">${{year}} ${{rating}}</div>
                    </div>
                  </div>
                `;
              }}).join("");

              box.style.display = "block";

              box.querySelectorAll(".suggestion").forEach(el => {{
                el.addEventListener("click", () => {{
                  input.value = el.getAttribute("data-title");
                  hidden.value = el.getAttribute("data-id");
                  hide();
                }});
              }});
            }}

            input.addEventListener("input", () => {{
              hidden.value = ""; // clear if user types again
              const q = input.value.trim();
              if (q.length < 2) {{
                hide();
                return;
              }}

              clearTimeout(debounceTimer);
              debounceTimer = setTimeout(async () => {{
                try {{
                  const resp = await fetch(`/api/tmdb/search?q=${{encodeURIComponent(q)}}`);
                  const data = await resp.json();
                  show(data.results || []);
                }} catch (e) {{
                  hide();
                }}
              }}, 250);
            }});

            document.addEventListener("click", (e) => {{
              if (!box.contains(e.target) && e.target !== input) hide();
            }});

            input.addEventListener("keydown", (e) => {{
              if (e.key === "Escape") hide();
            }});
          }}

          setupAutocomplete("movie1", "movie1_tmdb_id", "movie1_suggestions");
          setupAutocomplete("movie2", "movie2_tmdb_id", "movie2_suggestions");
        </script>
    </body>
    </html>
    """


# -----------------------------
# Submit Picks
# -----------------------------

@app.post("/api/events/{event_id}/picks")
def submit_picks(
    event_id: str,
    name: str = Form(...),
    movie1: str = Form(...),
    movie2: str = Form(...),
    movie1_tmdb_id: Optional[str] = Form(None),
    movie2_tmdb_id: Optional[str] = Form(None),
):
    event = get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if event["finalized"]:
        return RedirectResponse(
            url=f"/m/{event_id}?error=Event is finalized. No more picks allowed.",
            status_code=303,
        )

    if not movie1.strip() or not movie2.strip():
        return RedirectResponse(
            url=f"/m/{event_id}?error=Please provide exactly 2 movie picks.",
            status_code=303,
        )

    # Enrich each pick
    m1 = tmdb_movie_details(movie1_tmdb_id) if movie1_tmdb_id else None
    if not m1:
        m1 = tmdb_search_first(movie1.strip())
    if not m1:
        m1 = {"title": movie1.strip(), "tmdb_id": None, "poster_path": None, "year": "", "rating": None}

    m2 = tmdb_movie_details(movie2_tmdb_id) if movie2_tmdb_id else None
    if not m2:
        m2 = tmdb_search_first(movie2.strip())
    if not m2:
        m2 = {"title": movie2.strip(), "tmdb_id": None, "poster_path": None, "year": "", "rating": None}

    pick = {
        "name": name.strip(),
        "movies": [m1, m2],
    }

    event["picks"].append(pick)
    save_event(event)

    return RedirectResponse(
        url=f"/m/{event_id}?success=Your picks have been submitted!",
        status_code=303,
    )


# -----------------------------
# Finalize Event
# -----------------------------

@app.post("/api/events/{event_id}/finalize")
def finalize_event(event_id: str):
    event = get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if event["finalized"]:
        return RedirectResponse(
            url=f"/m/{event_id}?error=Event is already finalized.",
            status_code=303,
        )

    if not event["picks"]:
        return RedirectResponse(
            url=f"/m/{event_id}?error=Cannot finalize. Need at least 1 submission.",
            status_code=303,
        )

    all_movies = []
    for pick in event["picks"]:
        all_movies.extend(pick.get("movies", []))

    event["selected_movie"] = random.choice(all_movies)
    event["finalized"] = True
    save_event(event)

    return RedirectResponse(url=f"/m/{event_id}", status_code=303)


# -----------------------------
# TMDB Search Endpoint (Autocomplete)
# -----------------------------

@app.get("/api/tmdb/search")
def tmdb_search(q: str):
    q = (q or "").strip()
    if len(q) < 2:
        return {"results": []}

    data = tmdb_get(
        "/search/movie",
        params={
            "query": q,
            "include_adult": "false",
            "language": "en-US",
            "page": 1,
        },
    )

    results = []
    for m in data.get("results", [])[:8]:
        results.append(
            {
                "tmdb_id": m.get("id"),
                "title": m.get("title"),
                "year": (m.get("release_date") or "")[:4],
                "poster_path": m.get("poster_path"),
                "rating": m.get("vote_average"),
            }
        )

    return {"results": results}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
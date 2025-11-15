from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Response, Request, Cookie
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from models import Movie, Movietop
from pydantic import ValidationError
import os
import shutil
import uuid
import jwt
from typing import Optional, Dict
from datetime import datetime, timedelta

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

movies_data = []
movie_id_counter = 1

users_db = {
    "admin": "admin123",
    "user": "user123"
}

# === ЗАДАНИЕ В: Cookie-сессии ===
sessions: Dict[str, datetime] = {}

def verify_session(session_token: str) -> bool:
    if session_token in sessions:
        if datetime.now() < sessions[session_token]:
            sessions[session_token] = datetime.now() + timedelta(minutes=2)
            return True
        else:
            del sessions[session_token]
    return False

# === ЗАДАНИЕ Г: JWT настройки ===
JWT_SECRET = "your-secret-key"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 30

def create_jwt_token(username: str) -> str:
    payload = {
        "username": username,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def verify_jwt_token(token: str) -> Optional[Dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user_jwt(authorization: str = None):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    payload = verify_jwt_token(token)
    return payload

# === ЗАДАНИЕ А.3: Top 10 фильмов ===
movies_top_data = [
    Movietop(name="The Shawshank Redemption", id=1, cost=25, director="Frank Darabont"),
    Movietop(name="The Godfather", id=2, cost=6, director="Francis Ford Coppola"),
    Movietop(name="The Dark Knight", id=3, cost=185, director="Christopher Nolan"),
    Movietop(name="Pulp Fiction", id=4, cost=8, director="Quentin Tarantino"),
    Movietop(name="Forrest Gump", id=5, cost=55, director="Robert Zemeckis"),
    Movietop(name="Inception", id=6, cost=160, director="Christopher Nolan"),
    Movietop(name="The Matrix", id=7, cost=63, director="Wachowskis"),
    Movietop(name="Schindler's List", id=8, cost=22, director="Steven Spielberg"),
    Movietop(name="The Lord of the Rings: The Fellowship of the Ring", id=9, cost=93, director="Peter Jackson"),
    Movietop(name="Green Book", id=10, cost=23, director="Peter Farrelly")
]

movies_dict = {movie.name.lower(): movie for movie in movies_top_data}

@app.get("/")
def root():
    return HTMLResponse(content="""
    <html>
        <head><title>Movie Server</title></head>
        <body>
            <h1>Movie Collection Server</h1>
            <p><strong>Running on port 8165</strong></p>
            
            <h2>🎓 Задание А - Учеба и Top 10 фильмов</h2>
            <ul>
                <li><a href="/study">/study - Страница учебы</a></li>
                <li><a href="/movietop/inception">/movietop/inception - Поиск фильма</a></li>
            </ul>
            
            <h2>🎬 Задание Б - Добавление фильмов</h2>
            <ul>
                <li><a href="/movies/add-form">/movies/add-form - Форма добавления</a></li>
            </ul>
            
            <h2>🍪 Задание В - Cookie аутентификация</h2>
            <ul>
                <li><a href="/login-cookie-form">/login-cookie-form - Вход (Cookie)</a></li>
                <li><a href="/user-cookie">/user-cookie - Профиль (Cookie)</a></li>
            </ul>
            
            <h2>🔑 Задание Г - JWT аутентификация</h2>
            <ul>
                <li><a href="/login-jwt-form">/login-jwt-form - Вход (JWT)</a></li>
                <li><a href="/user-jwt">/user-jwt - Профиль (JWT)</a></li>
            </ul>
        </body>
    </html>
    """)

# === ЗАДАНИЕ А.2: Страница учебы ===
@app.get("/study", response_class=HTMLResponse)
def study_info():
    return HTMLResponse(content="""
    <html>
        <head>
            <title>University</title>
        </head>
        <body>
            <h1>Bryansk State Engineering Technological University</h1>
            <p><strong>Faculty:</strong> Information Technologies</p>
            <p><strong>Specialty:</strong> Computer Science</p>
            <p><strong>Year:</strong> 2025</p>
            <p><a href="/">← На главную</a></p>
        </body>
    </html>
    """)

# === ЗАДАНИЕ А.3: Top 10 фильмов ===
@app.get("/movietop/{movie_name:path}")
def get_movie(movie_name: str):
    import urllib.parse
    decoded_name = urllib.parse.unquote(movie_name).lower()
    
    if decoded_name in movies_dict:
        return movies_dict[decoded_name]
    return {"error": "Movie not found in top 10", "searched_name": decoded_name}

# === ЗАДАНИЕ Б: Форма добавления фильмов ===
@app.get("/movies/add-form")
def add_movie_form():
    return HTMLResponse(content="""
    <html>
        <head><title>Add Movie</title></head>
        <body>
            <h1>Add New Movie</h1>
            <form action="/movies/add" method="post" enctype="multipart/form-data">
                <p>Name: <input type="text" name="name" required></p>
                <p>Genre: <input type="text" name="genre" required></p>
                <p>Rating: <input type="number" name="rating" step="0.1" min="0" max="10" required></p>
                <p>Comment: <textarea name="comment" required></textarea></p>
                <p>Image: <input type="file" name="image" accept="image/*"></p>
                <button type="submit">Add Movie</button>
            </form>
            <p><a href="/">← На главную</a></p>
        </body>
    </html>
    """)

@app.post("/movies/add")
async def add_movie(
    name: str = Form(...),
    genre: str = Form(...),
    rating: float = Form(...),
    comment: str = Form(...),
    image: Optional[UploadFile] = File(None)
):
    global movie_id_counter
    
    try:
        movie = Movie(
            name=name,
            genre=genre,
            rating=rating,
            comment=comment
        )
        
        image_filename = None
        if image:
            file_extension = os.path.splitext(image.filename)[1]
            image_filename = f"movie_{movie_id_counter}{file_extension}"
            with open(f"static/images/{image_filename}", "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
        
        movie_dict = movie.dict()
        movie_dict["image_filename"] = image_filename
        movie_dict["id"] = movie_id_counter
        movies_data.append(movie_dict)
        movie_id_counter += 1
        
        return HTMLResponse(content=f"""
        <html>
            <body>
                <h1>Movie Added Successfully!</h1>
                <p>ID: {movie_dict['id']}</p>
                <p><a href="/movies/{movie_dict['id']}">View Movie</a></p>
                <p><a href="/movies/add-form">Add Another Movie</a></p>
                <p><a href="/">← На главную</a></p>
            </body>
        </html>
        """)
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/movies/{movie_id}")
def get_movie_by_id(movie_id: int):
    for movie in movies_data:
        if movie["id"] == movie_id:
            image_html = "No image"
            if movie["image_filename"]:
                image_html = f'<img src="/static/images/{movie["image_filename"]}" width="300">'
            
            return HTMLResponse(content=f"""
            <html>
                <head><title>{movie['name']}</title></head>
                <body>
                    <h1>{movie['name']}</h1>
                    {image_html}
                    <p><strong>Genre:</strong> {movie['genre']}</p>
                    <p><strong>Rating:</strong> {movie['rating']}/10</p>
                    <p><strong>Comment:</strong> {movie['comment']}</p>
                    <p><strong>ID:</strong> {movie['id']}</p>
                    <p><a href="/movies/add-form">Add another movie</a></p>
                    <p><a href="/">← На главную</a></p>
                </body>
            </html>
            """)
    
    return HTMLResponse(content="""
    <html>
        <body>
            <h1>Movie not found</h1>
            <p><a href="/">← На главную</a></p>
        </body>
    </html>
    """)

# === ЗАДАНИЕ В: Cookie-аутентификация ===
@app.get("/login-cookie-form")
def login_cookie_form():
    return HTMLResponse(content="""
    <html>
        <head><title>Cookie Login</title></head>
        <body>
            <h1>Cookie Login (Задание В)</h1>
            <form action="/login-cookie" method="post">
                <p>Username: <input type="text" name="username" required></p>
                <p>Password: <input type="password" name="password" required></p>
                <button type="submit">Login</button>
            </form>
            <p>Test users: admin/admin123 or user/user123</p>
            <p><a href="/">← На главную</a></p>
        </body>
    </html>
    """)

@app.post("/login-cookie")
async def login_cookie(response: Response, username: str = Form(...), password: str = Form(...)):
    if username in users_db and users_db[username] == password:
        session_token = str(uuid.uuid4())
        sessions[session_token] = datetime.now() + timedelta(minutes=30)
        
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            max_age=1800,
            path="/"
        )
        
        return HTMLResponse(content=f"""
        <html>
            <body>
                <h1>Login Successful! (Cookie)</h1>
                <p>Welcome, {username}!</p>
                <p><strong>Your Session Token:</strong> {session_token}</p>
                <p><a href="/user-cookie?session_token={session_token}">Go to Profile</a></p>
                <p><a href="/">← На главную</a></p>
            </body>
        </html>
        """)
    
    return HTMLResponse(content="""
    <html>
        <body>
            <h1>Login Failed</h1>
            <p>Invalid username or password</p>
            <p><a href="/login-cookie-form">Try again</a></p>
            <p><a href="/">← На главную</a></p>
        </body>
    </html>
    """, status_code=401)

@app.get("/user-cookie")
async def get_user_profile_cookie(
    session_token: Optional[str] = Cookie(None),
    request: Request = None
):
    final_token = session_token or (request.query_params.get("session_token") if request else None)
    
    if not final_token:
        return JSONResponse(
            status_code=401,
            content={"message": "Unauthorized", "reason": "No session token provided"}
        )
    
    if not verify_session(final_token):
        return JSONResponse(
            status_code=401,
            content={"message": "Unauthorized", "reason": "Invalid session token"}
        )
    
    return {
        "message": "Authorized",
        "profile": {
            "session_active": True,
            "session_expires": sessions[final_token].isoformat(),
            "auth_type": "cookie" if session_token else "cookie_url_param"
        },
        "movies_count": len(movies_data)
    }

# === ЗАДАНИЕ Г: JWT аутентификация ===
@app.get("/login-jwt-form")
def login_jwt_form():
    return HTMLResponse(content="""
    <html>
        <head><title>JWT Login</title></head>
        <body>
            <h1>JWT Login (Задание Г)</h1>
            <form action="/login-jwt" method="post">
                <p>Username: <input type="text" name="username" required></p>
                <p>Password: <input type="password" name="password" required></p>
                <button type="submit">Login</button>
            </form>
            <p>Test users: admin/admin123 or user/user123</p>
            <p><a href="/">← На главную</a></p>
        </body>
    </html>
    """)

@app.post("/login-jwt")
async def login_jwt(username: str = Form(...), password: str = Form(...)):
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")
    
    if username in users_db and users_db[username] == password:
        token = create_jwt_token(username)
        
        return HTMLResponse(content=f"""
        <html>
            <body>
                <h1>JWT Login Successful!</h1>
                <p>Welcome, {username}!</p>
                <p><strong>Your JWT Token:</strong></p>
                <textarea readonly style="width: 100%; height: 100px; font-family: monospace;">{token}</textarea>
                <p>Use this token in Authorization header: <code>Bearer {token}</code></p>
                <p><a href="/user-jwt?token={token}">Go to Profile with token</a></p>
                <p><a href="/">← На главную</a></p>
            </body>
        </html>
        """)
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/user-jwt")
async def get_user_profile_jwt(authorization: Optional[str] = None, token: Optional[str] = None):
    if token and not authorization:
        authorization = f"Bearer {token}"
    
    try:
        user = await get_current_user_jwt(authorization)
        
        return {
            "message": "Authorized",
            "profile": {
                "username": user["username"],
                "authenticated": True,
                "token_expires": datetime.fromtimestamp(user["exp"]).isoformat(),
                "auth_type": "jwt"
            },
            "movies_count": len(movies_data)
        }
    except HTTPException as e:
        return JSONResponse(
            status_code=401,
            content={"message": "Unauthorized", "reason": e.detail}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8165)
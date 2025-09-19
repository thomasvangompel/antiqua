from app import create_app
from pathlib import Path

app = create_app()

# Ensure the upload directory exists
PROFILE_PICS_DIR = Path(__file__).parent / "app" / "static" / "profile_pics"
PROFILE_PICS_DIR.mkdir(parents=True, exist_ok=True)
app.config.setdefault("PROFILE_PICS_DIR", str(PROFILE_PICS_DIR))

if __name__ == '__main__':
    app.run(debug=True)

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ["DATABASE_URL"] = "sqlite:///" + str(ROOT / "data" / "pytest.db")
os.environ["COURSE_MATERIALS_DIR"] = str(ROOT / "course-materials")
sys.path.insert(0, str(ROOT / "services" / "api"))

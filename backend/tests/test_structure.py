from pathlib import Path


def test_required_backend_structure_exists():
    root = Path(__file__).resolve().parents[1]
    required_paths = [
        root / "agents",
        root / "agents" / "tools",
        root / "models",
        root / "tools",
        root / "tests",
        root / "requirements.txt",
        root / "main.py",
    ]
    for p in required_paths:
        assert p.exists(), f"Missing required path: {p}"

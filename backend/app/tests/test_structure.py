from pathlib import Path


def test_required_backend_structure_exists():
    root = Path(__file__).resolve().parents[2]
    required_paths = [
        root / "app" / "main.py",
        root / "app" / "models",
        root / "app" / "routers",
        root / "app" / "services",
        root / "app" / "tests",
        root / "app" / "tools",
        root / "requirements.txt",
        root / "rmrr_mcp" / "medical_mcp_server.py",
    ]
    for p in required_paths:
        assert p.exists(), f"Missing required path: {p}"

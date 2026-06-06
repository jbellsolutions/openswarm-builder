"""Swarm directory validation."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def merge(self, other: ValidationResult) -> ValidationResult:
        return ValidationResult(
            ok=self.ok and other.ok,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
        )


def validate_swarm_dir(swarm_dir: Path, *, smoke: bool = False) -> ValidationResult:
    result = ValidationResult(ok=True)

    if not swarm_dir.is_dir():
        return ValidationResult(ok=False, errors=[f"Not a directory: {swarm_dir}"])

    required = ["swarm.py", "server.py"]
    for name in required:
        if not (swarm_dir / name).is_file():
            result.ok = False
            result.errors.append(f"Missing required file: {name}")

    manifest = swarm_dir / "manifest.yaml"
    if not manifest.is_file():
        result.warnings.append("manifest.yaml missing (optional but recommended)")

    build_spec = swarm_dir / ".build" / "spec.json"
    if not build_spec.is_file() and swarm_dir.name not in {"default"}:
        result.warnings.append(".build/spec.json missing — swarm may be vendor-only")

    if smoke:
        try:
            import importlib.util
            import sys

            swarm_root = str(swarm_dir.resolve())
            added_path = False
            if swarm_root not in sys.path:
                sys.path.insert(0, swarm_root)
                added_path = True
            try:
                spec = importlib.util.spec_from_file_location("swarm_module", swarm_dir / "swarm.py")
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    if not hasattr(mod, "swarm") and not hasattr(mod, "create_swarm"):
                        result.warnings.append("swarm.py has no `swarm` or `create_swarm` export")
            finally:
                if added_path:
                    sys.path.remove(swarm_root)
        except Exception as exc:
            result.warnings.append(f"smoke import skipped: {exc}")

    return result

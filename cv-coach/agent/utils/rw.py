import json
import os
import tempfile
from pathlib import Path

from ..models import (
    CurriculumVitae,
    ProfileContent,
    ExperienceContent,
    EducationContent,
    SkillsContent,
    SectionContent,
)

_CV_COACH_ROOT = Path(__file__).parent.parent.parent
_ATS_RULES_DIR = _CV_COACH_ROOT / "ats_rules"
_OUTPUT_PATH = _CV_COACH_ROOT / "output" / "output.json"

_SECTION_KEY: dict[type, str] = {
    ProfileContent: "profile",
    ExperienceContent: "experience",
    EducationContent: "education",
    SkillsContent: "skills",
}


def get_ats_rule(name: str) -> str:
    """Return the markdown content of an ATS rule file by name.

    Matches files like '05_work_experience.md' when name='work_experience'.
    Raises FileNotFoundError if no match is found.
    """
    matches = list(_ATS_RULES_DIR.glob(f"*_{name}.md"))
    if not matches:
        available = [p.stem.split("_", 1)[1] for p in sorted(_ATS_RULES_DIR.glob("*.md"))]
        raise FileNotFoundError(
            f"ATS rule '{name}' not found. Available: {available}"
        )
    return matches[0].read_text(encoding="utf-8")


def load_cv() -> CurriculumVitae:
    """Load and validate the current CV from output.json."""
    raw = json.loads(_OUTPUT_PATH.read_text(encoding="utf-8"))
    return CurriculumVitae.model_validate(raw)


def update_cv_section(section: SectionContent) -> None:
    """Validate and persist a single CV section to output.json.

    Merges only the model-defined fields into the existing JSON, preserving
    any extra keys (e.g. contact, name, title) that live outside the model.
    Write is atomic: a temp file is written first, then renamed.
    """
    section_key = _SECTION_KEY.get(type(section))
    if section_key is None:
        raise TypeError(f"Unsupported section type: {type(section)}")

    raw = json.loads(_OUTPUT_PATH.read_text(encoding="utf-8"))

    existing_section = raw.get(section_key, {})
    updated_section = {**existing_section, **section.model_dump(mode="json")}
    raw[section_key] = updated_section

    _atomic_write(_OUTPUT_PATH, json.dumps(raw, indent=2, ensure_ascii=False))


def _atomic_write(path: Path, content: str) -> None:
    dir_ = path.parent
    fd, tmp_path = tempfile.mkstemp(dir=dir_, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, path)
    except Exception:
        os.unlink(tmp_path)
        raise

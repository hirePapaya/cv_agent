import json
from pathlib import Path

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "output" / "output.json"

_MONTHS = ["Jan.", "Feb.", "Mar.", "Apr.", "May", "Jun.", "Jul.", "Aug.", "Sep.", "Oct.", "Nov.", "Dec."]


def _format_range(start: str | None, end: str | None, year_only: bool = False) -> str:
    def fmt(d: str | None) -> str:
        if not d:
            return "Present"
        year, month, *_ = d.split("-")
        return year if year_only else f"{_MONTHS[int(month) - 1]} {year}"

    return f"{fmt(start)} — {fmt(end)}"


def _contact_links(contact: dict) -> list[dict]:
    links = []
    phone = contact.get("phone")
    if phone:
        links.append({"label": phone, "href": "tel:" + phone.replace(" ", "")})
    email = contact.get("email")
    if email:
        links.append({"label": email, "href": f"mailto:{email}"})
    github = contact.get("github")
    if github:
        links.append({"label": github, "href": f"https://{github}"})
    linkedin = contact.get("linkedin")
    if linkedin:
        links.append({"label": linkedin, "href": f"https://{linkedin}"})
    return links


def load_cv_studio_data() -> dict:
    """Load the persisted CV (output.json) and adapt it to the CV Studio shape."""
    raw = json.loads(OUTPUT_PATH.read_text())

    profile = raw.get("profile", {})
    jobs = raw.get("experience", {}).get("jobs", [])
    entries = raw.get("education", {}).get("entries", [])
    categories = raw.get("skills", {}).get("categories", {})

    return {
        "name": profile.get("name", ""),
        "title": profile.get("title", ""),
        "summary": profile.get("text", ""),
        "contact": _contact_links(raw.get("contact", {})),
        "experience": [
            {
                "company": job.get("company", ""),
                "role": job.get("title", ""),
                "location": job.get("location") or "",
                "dates": _format_range(job.get("start_date"), job.get("end_date")),
                "bullets": job.get("achievements", []),
            }
            for job in jobs
        ],
        "education": [
            {
                "school": entry.get("institution", ""),
                "degree": entry.get("degree", ""),
                "location": entry.get("location") or "",
                "dates": _format_range(entry.get("start_date"), entry.get("end_date"), year_only=True),
            }
            for entry in entries
        ],
        "skills": [
            {"label": label, "items": ", ".join(items)}
            for label, items in categories.items()
        ],
    }

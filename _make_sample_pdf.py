"""One-off generator for sample_syllabus.pdf. Safe to delete after running."""

from pathlib import Path


PAGES = [
    [
        "CSC1201 Introduction to Programming",
        "Faculty of Computing, GDG on Campus demo syllabus",
        "Lecturer: Dr. Aisha Rahman",
        "Email: aisha.rahman@campus.edu",
        "Course code: CSC1201",
        "Credits: 3",
        "Semester: 2026/2027 Semester 1",
        "Class hours: Tuesday 10:00-12:00, Lab Thursday 14:00-16:00, Room B204",
    ],
    [
        "Attendance policy",
        "Students must attend at least 80 percent of lectures and labs.",
        "Falling below 80 percent without approved leave means you cannot sit the final exam.",
        "Email the lecturer at least 24 hours before class for planned absences.",
        "Medical leave requires a clinic or hospital letter within 7 days.",
        "Assessment",
        "Quizzes: 10 percent",
        "Lab assignments: 20 percent",
        "Midterm exam: 30 percent, held in Week 7 on 20 November 2026, 10:00-12:00, Hall A",
        "Final exam: 40 percent, date to be announced by the exams office",
        "Late lab work loses 10 percent per day and is not accepted after 3 days.",
    ],
    [
        "Weekly topics",
        "Week 1: Python basics and campus lab setup",
        "Week 2: Variables, types, and input",
        "Week 3: Conditionals and loops",
        "Week 4: Functions",
        "Week 5: Lists and dictionaries",
        "Week 6: Files and exceptions",
        "Week 7: Midterm exam",
        "Week 8-12: Small project and revision",
        "Office hours: Wednesday 15:00-16:00 in Room B210",
        "Required tool: Python 3.12",
        "This document does not include building Wi-Fi passwords or personal student records.",
    ],
]


def pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def page_stream(lines: list[str]) -> bytes:
    commands = ["BT", "/F1 12 Tf", "50 TL", "72 740 Td"]
    for index, line in enumerate(lines):
        commands.append(f"({pdf_escape(line)}) Tj")
        if index != len(lines) - 1:
            commands.append("T*")
    commands.append("ET")
    return "\n".join(commands).encode("latin-1")


def build_pdf(pages: list[list[str]]) -> bytes:
    objects = ["placeholder"]  # 1-based
    catalog_id, pages_id = 1, 2
    font_id = 3
    page_ids = []
    content_ids = []
    next_id = 4

    for _ in pages:
        page_ids.append(next_id)
        content_ids.append(next_id + 1)
        next_id += 2

    objects.append("<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>")
    objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    for page_id, content_id, lines in zip(page_ids, content_ids, pages):
        stream = page_stream(lines)
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {content_id} 0 R /Resources << /Font << /F1 {font_id} 0 R >> >> >>"
        )
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1") + stream + b"\nendstream")

    # Mixed str/bytes in objects; normalize to bytes
    encoded = []
    for obj in objects[1:]:
        encoded.append(obj if isinstance(obj, bytes) else obj.encode("latin-1"))

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, body in enumerate(encoded, start=1):
        offsets.append(len(out))
        out.extend(f"{index} 0 obj\n".encode("latin-1"))
        out.extend(body)
        out.extend(b"\nendobj\n")

    xref_pos = len(out)
    out.extend(f"xref\n0 {len(encoded) + 1}\n".encode("latin-1"))
    out.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        out.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    out.extend(
        f"trailer << /Size {len(encoded) + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode(
            "latin-1"
        )
    )
    return bytes(out)


if __name__ == "__main__":
    path = Path(__file__).with_name("sample_syllabus.pdf")
    path.write_bytes(build_pdf(PAGES))
    print(f"Wrote {path}")

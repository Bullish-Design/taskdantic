from __future__ import annotations

BEGIN_MARKER = "# BEGIN TASKDANTIC UDAS"
END_MARKER = "# END TASKDANTIC UDAS"


def parse_existing_uda_names(taskrc_text: str) -> set[str]:
    names: set[str] = set()
    for raw in taskrc_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("uda.") and ".type=" in line:
            rest = line[len("uda.") :]
            name = rest.split(".type=", 1)[0].strip()
            if name:
                names.add(name)
    return names


def upsert_uda_block(taskrc_text: str, block_body: str) -> str:
    managed = (
        f"{BEGIN_MARKER}\n# Generated from Pydantic Task models. Do not edit by hand.\n\n{block_body}\n{END_MARKER}\n"
    )

    start = taskrc_text.find(BEGIN_MARKER)
    end = taskrc_text.find(END_MARKER)
    if start != -1 and end != -1 and start < end:
        pre = taskrc_text[:start].rstrip() + "\n\n"
        post = taskrc_text[end + len(END_MARKER) :].lstrip()
        return pre + managed + "\n" + post

    sep = "\n\n" if not taskrc_text.endswith("\n") else "\n"
    return taskrc_text + sep + managed

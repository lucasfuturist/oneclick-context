TEE, CORNER, PIPE, SPACE = "├──", "└──", "│   ", "    "

def render(node, prefix=""):
    lines = []
    children = node["children"]
    pointers = [TEE] * (len(children) - 1) + [CORNER]
    for pointer, child in zip(pointers, children):
        lines.append(f"{prefix}{pointer} {child['name']}")
        if child["type"] == "dir":
            extension = PIPE if pointer == TEE else SPACE
            lines.extend(render(child, prefix + extension))
    return lines

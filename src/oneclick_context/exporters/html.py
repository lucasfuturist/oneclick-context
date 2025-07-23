def _render_li(node):
    if node["type"] == "file":
        return f"<li>{node['name']}</li>"
    children_html = "".join(_render_li(c) for c in node["children"])
    return f"<li><details><summary>{node['name']}</summary><ul>{children_html}</ul></details></li>"

def render_html(tree_obj):
    return f"<ul>{_render_li(tree_obj)}</ul>"

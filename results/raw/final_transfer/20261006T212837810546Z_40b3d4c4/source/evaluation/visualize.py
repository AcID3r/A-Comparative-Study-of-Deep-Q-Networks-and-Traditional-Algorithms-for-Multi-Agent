"""Text and standalone SVG path displays, with no external dependencies."""

from html import escape
from environments.grid_graph import GridGraph, Position


def _check_path(graph, start, goal, path):
    graph.validate_endpoints(start, goal)
    if path is not None:
        graph.path_cost(path)
        if path[0] != start or path[-1] != goal:
            raise ValueError("Displayed path must connect the stated endpoints")


def render_text(graph: GridGraph, start: Position, goal: Position,
                path: list[Position] | None) -> str:
    _check_path(graph, start, goal, path)
    route = set(path or [])
    lines = []
    for r in range(graph.rows):
        cells = []
        for c in range(graph.cols):
            pos = (r, c)
            symbol = ("B" if pos == start == goal else "S" if pos == start
                      else "G" if pos == goal else "#" if pos in graph.obstacles
                      else "*" if pos in route else ".")
            cells.append(symbol)
        lines.append(" ".join(cells))
    lines.append("B=Start+Goal S=Start G=Goal #=Wall *=Path .=Free")
    if path is None:
        lines.append("No route exists.")
    if not graph.uniform_costs or graph.minimum_cost != 1:
        lines.append("Cell costs: " + ", ".join(
            f"{pos}={cost:g}" for pos, cost in sorted(graph.cell_costs.items())))
    return "\n".join(lines)


def render_svg(graph: GridGraph, start: Position, goal: Position,
               path: list[Position] | None, title: str = "Path") -> str:
    _check_path(graph, start, goal, path)
    cell = 40
    width, height = max(480, graph.cols * cell + 40), graph.rows * cell + 130
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
             f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">',
             f'<title id="title">{escape(title)}</title>',
             '<desc id="description">Four-direction grid. Dark cells are walls; '
             'blue cells show the route. S is start, G is goal, B is both.</desc>',
             '<rect width="100%" height="100%" fill="white"/>',
             f'<text x="20" y="26" font-family="sans-serif" font-size="16">{escape(title)}</text>']
    route = set(path or [])
    for r in range(graph.rows):
        for c in range(graph.cols):
            pos = (r, c)
            x, y = 20 + c * cell, 40 + r * cell
            color = ("#334155" if pos in graph.obstacles else "#bfdbfe" if pos in route else "#f8fafc")
            label = "B" if pos == start == goal else "S" if pos == start else "G" if pos == goal else ""
            if not label and graph.is_free(pos) and graph.cost(pos) != 1:
                label = f"{graph.cost(pos):g}"
            parts.append(f'<rect x="{x}" y="{y}" width="40" height="40" fill="{color}" stroke="#94a3b8"/>')
            if label:
                parts.append(f'<text x="{x + 20}" y="{y + 25}" text-anchor="middle" '
                             f'font-family="sans-serif" font-size="14">{escape(label)}</text>')
    foot = graph.rows * cell + 65
    parts.append(f'<text x="20" y="{foot}" font-family="sans-serif" font-size="12">'
                 'S=start G=goal B=both; blue=path; dark=wall</text>')
    note = "No route exists." if path is None else f"Moves: {len(path) - 1}; cost: {graph.path_cost(path):g}"
    parts.append(f'<text x="20" y="{foot + 22}" font-family="sans-serif" font-size="12">{escape(note)}</text>')
    parts.append('</svg>')
    return "\n".join(parts)

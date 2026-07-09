"""Export the LangGraph pipeline as a Mermaid diagram.

    python3 scripts/draw_graph.py        # prints mermaid + writes graph.mmd

Uses an empty agents dict — the node functions are only called at runtime,
so the graph *structure* can be drawn without any models or API keys.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph import build_graph


def main():
    graph = build_graph({})
    mermaid = graph.get_graph().draw_mermaid()

    out_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "graph.mmd"
    )
    with open(out_path, "w") as f:
        f.write(mermaid)

    print(mermaid)
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()

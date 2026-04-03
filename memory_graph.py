# memory_graph.py
import objgraph
import gc

# After running agent...

# Show what objects exist and how many
objgraph.show_most_common_types(limit=20)

# Show what's referencing a specific object type
# (e.g., find all dicts that might be memory stores)
objgraph.show_backrefs(
    objgraph.by_type('dict')[0],
    max_depth=3,
    filename='memory_refs.png'
)
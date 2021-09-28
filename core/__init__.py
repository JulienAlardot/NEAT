import os
import sys
import time
import warnings

import pydot as dot


def timeit(func, stdout=sys.stdout):
    """Decorator to compute function execution time"""

    def inner(*args, **kwargs):
        t = time.time()
        r = func(*args, **kwargs)
        t = time.time() - t
        stdout.write(
            f"Execution of {func} took {int(t // 3600):0>2}:{int(t % 3600 // 60):0>2}:{int(t % 60):0>2}:{round((t - int(t))) * 1000:0>3}")
        return r

    return inner


def specimen_to_graph(specimen):
    graph_name = f"{specimen.generation:0>4}-{specimen.id:0>5}"
    graph: dot.Graph = dot.Graph(graph_name=graph_name, rankdir="LR")

    input_graph = dot.Subgraph("Inputs Nodes", color="blue", label="Input Nodes")
    for node in specimen.input_nodes:
        new_node = dot.Node(str(node), color="blue", shape="square")
        input_graph.add_node(new_node)
    graph.add_subgraph(input_graph)

    out_graph = dot.Subgraph("Output Nodes", color="red", label="Output Nodes")
    for node in specimen.output_nodes:
        new_node = dot.Node(str(node), color="red", shape="diamond")
        out_graph.add_node(new_node)
    graph.add_subgraph(out_graph)
    hidden_graph = dot.Subgraph("Hidden Nodes", color="gray", label="Hidden Nodes")
    for node in specimen.hidden_nodes:
        new_node = dot.Node(str(node), color="gray")
        hidden_graph.add_node(new_node)
    graph.add_subgraph(hidden_graph)
    print("\n" * 5)
    for id, in_node, out_node, weight, enabled in specimen.connections:
        edge = dot.Edge(str(in_node),
                        str(out_node),
                        color="blue" if enabled else "red",
                        label=str(round(weight, 1)),
                        shape="vee")
        graph.add_edge(edge)
    print("\n" * 5)
    out = f"{graph_name}.dot"
    with open(out, "wt") as outfile:
        outfile.write(graph.to_string())
    try:
        os.system(f"dot {out}")
    except:
        warnings.warn("dot is not installed")

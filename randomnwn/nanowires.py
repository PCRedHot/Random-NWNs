#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Functions to create nanowire networks.
# 
# Author: Marcus Kasdorf
# Date:   May 17, 2021

from typing import List, Dict, Tuple
import numpy as np
import scipy
from numpy.random import uniform
from shapely.geometry import LineString, Point
import networkx as nx
import matplotlib.pyplot as plt

def create_line(length=1, xmin=0, xmax=1, ymin=0, ymax=1, rng=None) -> LineString:
    """
    Generate random lines with random orientations with midpoints 
    ranging from area from ``xmin`` to ``xmax`` and from ``ymin``
    to ``ymax``.

    Parameters
    ----------
    length : float
        Length of line
    
    xmin : float
        Minimum x coordinate midpoint.

    xmax : float
        Minimum x coordinate midpoint.

    ymin : float
        Minimum y coordinate midpoint.

    ymax : float
        Minimum y coordinate midpoint.

    rng : Generator
        Generator object usually created from ``default_rng``
        from ``numpy.random``. A seeded generator can be passed
        for consistent random numbers. If None, uses the default
        NumPy random functions.

    Returns
    -------
    out : LineString
        LineString of the generated line.

    """
    if rng is not None:
        xmid, ymid, angle = rng.uniform(xmin, xmax), rng.uniform(ymin, ymax), rng.uniform(0, np.pi)
    else:
        xmid, ymid, angle = uniform(xmin, xmax), uniform(ymin, ymax), uniform(0, np.pi)

    xhalf, yhalf = length / 2 * np.cos(angle), length / 2 * np.sin(angle)

    xstart, xend = xmid - xhalf, xmid + xhalf
    ystart, yend = ymid - yhalf, ymid + yhalf

    out = LineString([(xstart, ystart), (xend, yend)])
    return out

def find_intersects(lines: list) -> Dict[Tuple[int, int], Point]:
    """
    Given a list of LineStrings, finds all the lines that intersect 
    and where.

    Parameters
    ----------
    lines : list of LineStrings
        List of the LineStrings to find the intersections of.

    loc : bool
        Whether or not to return the intersect locations.
        Defaults to false.

    Returns
    -------
    out : dict
        Dictionary where the key is a tuple of the pair of
        intersecting lines and the value is the intersection
        locations.

    """
    out = {}

    for i, j in zip(*np.triu_indices(n=len(lines), k=1)):
        # Check for intersection first before calculating it
        if lines[i].intersects(lines[j]):
            out.update({(i, j): lines[i].intersection(lines[j])})

    return out

def find_line_intersects(ind: int, lines: List[LineString]) -> Dict[Tuple[int, int], Point]:
    """
    Given a list of LineStrings, find all the lines that intersect
    with a specified line in the list given by the index ``ind``.

    """
    out = {}

    for j in range(len(lines)):
        # Skip intersection with the line itself
        if ind == j:
            continue
        
        # Checking if these's an intersection first is faster
        if lines[ind].intersects(lines[j]):
            if ind < j:
                out.update({(ind, j): lines[ind].intersection(lines[j])})
            else:
                out.update({(j, ind): lines[ind].intersection(lines[j])})

    return out

def create_NWN(
        wire_length: float = 7.0, 
        width: float = 50.0, 
        density: float = 0.3, 
        seed: int = None,
        resistance: float = 10
    ) -> nx.Graph:
    """
    Create a nanowire network stored in a networkx graph. The wires are 
    the graph's vertices, while the wire junctions are represented by the edges.

    The density might not be attainable with the given size as there can
    only be a integer number of wires. Thus, the closest density to get
    an integer number is used.

    Wire length and grid width are in micrometers. Resistance is in ohms.

    """
    # Get closest density with an integer number of wires.
    size = width * width
    wire_num = round(size * density)
    density = wire_num / size

    # Create NWN graph
    NWN = nx.Graph(
        wire_length = wire_length, 
        width = width, 
        size = size,
        wire_density = density, 
        wire_num = wire_num,
        electrodes = 0,
        junction_resistance = resistance,
        electrode_list = []
    )

    # Create seeded random generator for testing
    rng = np.random.default_rng(seed)

    # Add the wires as nodes to the graph
    for i in range(NWN.graph["wire_num"]):
        NWN.add_node(
            i, line=create_line(NWN.graph["wire_length"], xmax=NWN.graph["width"], ymax=NWN.graph["width"], rng=rng), electrode=False
        )
        NWN.nodes[i]["midpoint"] = np.array(NWN.nodes[i]["line"].centroid)
        
    # Find intersects
    intersect_dict = find_intersects(NWN.nodes.data("line"))
    NWN.add_edges_from(intersect_dict.keys(), resistance=resistance)
    NWN.graph["loc"] = intersect_dict
    
    # Find junction density
    NWN.graph["junction_density"] = len(intersect_dict) / size

    return NWN

def plot_NWN(NWN, intersections=True, rnd_color=False):
    """
    Plots a given nanowire network.

    """
    fig, ax = plt.subplots(figsize=(8, 6))

    # Plot intersection plots if required
    if intersections:
        ax.scatter(
            *np.array([(point.x, point.y) for point in NWN.graph["loc"].values()]).T, 
            zorder=10, s=5, c="blue"
        )

    # Defaults to blue and pink lines, else random colors are used.
    if rnd_color:
        for i in range(NWN.graph["wire_num"]):
            ax.plot(*np.array(NWN.nodes[i]["line"]).T)
    else:
        for i in range(NWN.graph["wire_num"]):
            if NWN.nodes[i]["electrode"]:
                ax.plot(*np.array(NWN.nodes[i]["line"]).T, c="xkcd:light blue")
            else:
                ax.plot(*np.array(NWN.nodes[i]["line"]).T, c="pink")

    plt.show()
    return fig, ax

def add_wires(NWN: nx.Graph, lines: List[LineString], electrodes: List[bool]):
    """
    Adds wires to a given nanowire network.
    
    """
    new_wire_num = len(lines)

    if new_wire_num != len(electrodes):
        raise ValueError("Length of new lines list must equal length of electrode boolean list.")

    # Update wire number in NWN
    start_ind = NWN.graph["wire_num"]
    NWN.graph["wire_num"] += new_wire_num
    NWN.graph["electrodes"] += np.sum(electrodes)

    # Add wires to NWN
    for i in range(new_wire_num):
        NWN.add_node(
            start_ind + i, line=lines[i], 
            midpoint = np.array(lines[i].centroid), 
            electrode = electrodes[i],
        )

        if electrodes[i]:
            NWN.graph["electrode_list"].append(start_ind + i)

        # Find intersects
        intersect_dict = find_line_intersects(start_ind + i, NWN.nodes.data("line"))

        # Custom contact junction resistances
        # for ind in intersect_dict.keys():
        #     resistance = NWN.graph["junction_resistance"]
        #     if ind[0] in NWN.graph["electrode_list"] or ind[1] in NWN.graph["electrode_list"]:
        #         resistance = 0.0
        #     NWN.add_edge(*ind, resistance=resistance)
        
        # Uniform junction resistances
        NWN.add_edges_from(
            intersect_dict.keys(), 
            resistance = NWN.graph["junction_resistance"]
        )
        NWN.graph["loc"].update(intersect_dict)

    # Update wire density
    NWN.graph["wire_density"] = (NWN.graph["wire_num"] - NWN.graph["electrodes"]) / NWN.graph["size"]

def conductance_matrix(NWN: nx.Graph, drain_node: int):
    """
    Create the (sparse) conductance matrix for a given NWN.

    """
    wire_num = NWN.graph["wire_num"]
    G = scipy.sparse.dok_matrix((wire_num, wire_num))
    
    for i in range(wire_num):
        for j in range(wire_num):
            if i == j:
                if i == drain_node:
                    G[i, j] = 1.0
                else:
                    G[i, j] = sum(
                        [1 / NWN[edge[0]][edge[1]]["resistance"] for edge in NWN.edges(i) if NWN[edge[0]][edge[1]]["resistance"] != 0]
                    )

                    # Ground every node with a large resistor: 1e-8 -> 100 MΩ
                    G[i, j] += 1e-8
            else:
                if i != drain_node:
                    edge_data = NWN.get_edge_data(i, j)
                    if edge_data:
                        G[i, j] = -1 / edge_data["resistance"]
    return G

def solve_network(NWN: nx.Graph, source_node: int, drain_node: int, voltage: float):
    """
    Solve for the voltages of each wire in a given NWN.
    The source node will be at the specified voltage and
    the drain node will be grounded.
    
    """
    wire_num = NWN.graph["wire_num"]
    G = conductance_matrix(NWN, source_node, drain_node)

    B = scipy.sparse.dok_matrix((wire_num, 1))
    B[source_node, 0] = -1

    C = -B.T

    D = None

    A = scipy.sparse.bmat([[G, B], [C, D]])
    z = scipy.sparse.dok_matrix((wire_num + 1, 1))
    z[-1] = voltage

    # SparseEfficiencyWarning: spsolve requires A be CSC or CSR matrix format
    x = scipy.sparse.linalg.spsolve(A.tocsr(), z)
    return x

# Testing code
if __name__ == "__main__":
    from timeit import timeit

    setup = "from __main__ import create_line"
    test = "create_line()"

    print(timeit(setup=setup, stmt=test))


# Description:
# This file contains functions that defines the basic structure for representation of a node in the network

import itertools
import helper  # custom made helper file


# "universal_dict" is basically a dict representing all the BN nodes,
#   format: {"(node_name)" : {"(node_value)": (probability_value)}}   example: {"A":{"0":0.9, "1":0.1}}
# "node_stats" is used to maintain the tally/statistics of nodes (total nodes, total sum nodes, total product nodes)
# "indicator_nodes" is used to identify duplicate indicator nodes and thus prevent them being counted in the stats
universal_dict = {}
nodes_stats = {
    "total": 0,
    "product": 0,
    "sum": 0,
    "parameter": 0,
    "indicator": 0,
}
indicator_nodes = []


# Function uses the bn_graph_nodes dict to create a universal dict
# Input: {"A":{"states":["0", "1"], "parents":[], "values":[[0.9, 0.1]}}
# Output: {"A":{"0":0.9, "1":0.1}}
def create_universal_dict(bn_graph_nodes):
    for key, value in bn_graph_nodes.items():
        universal_dict[key] = {}
        states = value["states"]
        parents = value["parents"]
        values = helper.flatten(value["values"])

        if len(parents) != 0:  # code to calculate the values based on itertools.product for every possible permutation
            states_list = [states]
            for parent in parents:  # loop to get the parents states
                states_list.append(bn_graph_nodes[parent]["states"])
            states = helper.convert_list_items_to_string(itertools.product(*states_list))

        for i in range(len(states)):
            universal_dict[key][states[i]] = values[i]
    # print("UNIVERSAL:", universal_dict)
    return universal_dict


# Common function that creates a node in the network with the format:
# {
#     "type": "", ## possible values: sum/product/value/indicator
#     "value": , ## probability value
#     "references": [], ## contains dict representing other nodes
#     "node": "", ## name of variable, ex: A
#     "variable_value": "", ## possible value of variable, ex: 0
# }
# references to denote that this node is a parent to these child node in the network
# Input: {node_type: "value", value: 0.2, references: [], node: "A", variable_value: "0"}
# Output: {type: "value", value: 0.2, references: [], node: A,  variable_value: "0"}
def create_node(node_type, value, references, node, variable_value):
    nodes_stats["total"] += 1
    if node_type == "sum":
        nodes_stats["sum"] += 1
    elif node_type == "product":
        nodes_stats["product"] += 1
    elif node_type == "value":
        nodes_stats["parameter"] += 1
    if node_type == "indicator":
        nodes_stats["indicator"] += 1
        # condition checks if an indicator nodes already exists, if yes, we subtract its count from total
        if node_type+"-"+node+"-"+variable_value in indicator_nodes:
            # print("found-duplicate", node_type+"-"+node+"-"+variable_value)
            nodes_stats["total"] -= 1
            nodes_stats["indicator"] -= 1
        indicator_nodes.append(node_type+"-"+node+"-"+variable_value)

    return {
        "type": node_type,
        "value": value,
        "references": references,
        "node": node.strip(),
        "variable_value": variable_value.strip(),
    }

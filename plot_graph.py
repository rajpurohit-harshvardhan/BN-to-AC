# Description:
# This file is responsible for plotting the Arithmetic circuit, which is received as an input along with the file name.
# After this file is executed with appropriate inputs, the output would be an SVG file of the Arithmetic circuit.
# Format of a single node ::
# {
#     "type": "", ## possible values: sum/product/value/indicator
#     "value": , ## probability value
#     "references": [], ## contains dict representing other nodes
#     "node": "", ## name of variable, ex: A
#     "variable_value": "", ## possible value of variable, ex: 0
# }


import graphviz

# "duplicates" variable is used to detect & prevent duplicate nodes to be created in graph,thus plotting wrong network
# "edges" variable is used for the same purpose, but the difference being, it stores the edges between nodes.
duplicates = {}
edges = []


# This function provides all the required attributes for a node in the network, attributes being: name/label/fillcolor
# It takes the name of the node
# (which is of format "(name of variable)_(type)", ex: for variable A and value type node, the name becomes: A_value),
# node type (value/indicator/sum/product),
# value of node (probability value),
# variable_value(indicator of the possible values for node),
# counter(Used to allow multiple sum/product nodes with same name/label and not let graphviz detect them as duplicates).
# Input: {node_name: "A_value", type: "value", node_value: 0.5, variable_value: "0", counter: [4]}
# Output:{node_name: A_value_0.5_5, label: "A_value_0.5", fillcolor: "Lavender"}
def get_node_attributes(node_name, type, node_value, variable_value, counter):
    label = node_name
    fillcolor = "white"
    if type != "indicator" and type != "value":
        counter[0] += 1
        node_name += str(counter)

    if type == "value":
        label += "_" + str(node_value)
        node_name = label
        counter[0] += 1
        node_name += str(counter)
        fillcolor = "Lavender"
    elif type == "indicator":
        label += "_" + str(variable_value)
        node_name = label
        fillcolor = "Thistle"
    elif type == "sum":
        label = "+"
        fillcolor = "LightCoral"
    elif type == "product":
        label = "*"
        fillcolor = "LightCyan"
    else:
        label = "#"
        fillcolor = "DarkSeaGreen"

    return {"node_name": node_name, "label": label, "fillcolor": fillcolor}


# The idea behind this function is that the nodes dict contains every node created until the moment this func is called.
# We search for these nodes to check whether a node with the given node_name exists,
# if yes, we return the existing node OR we return None
# Input: {node_name: "A_sum4", node_references: [{ ..node_format.. }], nodes: {"A_sum2":[{ ..node_format.. }]}}
# Output: None OR "A_sum2"
def find_duplicate(node_name, node_references, nodes):
    keys = list(nodes.keys())
    for i in range(len(keys)):
        node1 = nodes[keys[i]]
        if node_references == node1 and node_name != keys[i]:
            # print(node_name, keys[i])
            duplicates[node_name] = keys[i]
            return keys[i]

    return None


# The brain of the file, is responsible for converting the dict of dict representing the AC into a visual network
# Input: {data: {"A":{"0": { ..node_format.. }, "1": { ..node_format.. }}}, dot: ..Graphviz_digraph..}
# Output: ..Graphviz_digraph..
def create_graphviz(data, dot):
    nodes = {}  # used for detecting duplicates
    counter = [0]  # used to allow duplicate sum/product/variable nodes which have same name.

    # This function is responsible for creation of edges between every node in the network
    def add_edges(parent_name, children):
        # This condition is to check whether a node with the same name has been created in the graph,
        # if yes, then we have already created all the edges concerning this node and need not create duplicates
        if parent_name in duplicates:
            # print("FOUND in duplicates:", parent_name, ":: changed to ==", duplicates[parent_name])
            return True

        # Children here is a list of dicts, with the same format as that of a single node.
        # They are the references for a given node.
        for child in children:
            child_node_name = child["node"] + "_" + child["type"]  # creating the node name, for unique identity
            child_node_attrib = get_node_attributes(child_node_name, child["type"], child["value"], child["variable_value"], counter)

            # condition is specific to sum/product nodes because they will have the same label
            # thus their node_name needs to be unique to mark them as unique
            duplicate = None
            if child["type"] == "sum" or child["type"] == "product":
                nodes[child_node_attrib["node_name"]] = child["references"]
                duplicate = find_duplicate(child_node_attrib["node_name"], child["references"], nodes)

            if duplicate is not None:
                # this means that a node with the same values has been created so just create an edge.
                dot.edge(duplicate, parent_name)
            else:
                # this means that either the node is a new node and thus needs to be created with and edge
                dot.node(child_node_attrib["node_name"], child_node_attrib["label"], style='filled', fillcolor=child_node_attrib["fillcolor"])
                dot.edge(child_node_attrib["node_name"], parent_name)
            add_edges(child_node_attrib["node_name"], child.get("references", []))  # recursive call to same function

    node_name = data["node"]+"_"+data["type"]
    node_attrib = get_node_attributes(node_name, data["type"], data["value"], data["variable_value"], counter)
    dot.node(node_attrib["node_name"], node_attrib["label"], style='filled', fillcolor=node_attrib["fillcolor"])
    add_edges(node_attrib["node_name"], data["references"])
    return dot


# Main function of the file, is responsible for plotting the network with the provided input values.
# Input: {data: {"A":{"0": { ..node_format.. }, "1": { ..node_format.. }}}, file_name: "asia"}
# Output: None
def plot_graphviz(data, file_name, nodes_stats):
    # For loop because we receive a dict where keys = possible values of root variable & values = dict of a node format
    for node in data:
        dot = graphviz.Digraph("AC_" + file_name + "_" + node, comment='Arithmetic Circuit', format='svg')  # creates a file with the file_name and format
        dot = create_graphviz(data[node], dot)  # uses the file to plot the network
        dot.attr(label="Node Stats :: " + str(nodes_stats), labelloc="nodes_stats")
        dot.render(directory='arithmetic-circuits/'+file_name).replace('\\', '/')
        print("Created arithmetic circuit at folder: arithmetic-circuits/"+file_name)

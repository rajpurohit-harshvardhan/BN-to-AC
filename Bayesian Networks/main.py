# Description:
# The main file that combines all the others together to implement the conversion of a BN to AC

import plot_graph as plot
import structure_functions as sf
import bn_functions as bnf


# Function uses different function calls from other files to create the final sum product network
# Input: {elimination_order: ["B","C","A"], universal_dict: {"A":{"0":0.9, "1":0.1}},
#         parents_dict: {"A":[],"B":["A"]}, non_leaf_nodes: ["A", "B"]}
# Output: {"A":{..node_format..}} where A is the root node of the BN
def create_sum_product_network(elimination_order, universal_dict, parents_dict, non_leaf_nodes):
    buckets = {}

    for node in elimination_order:
        # creates the product nodes between each indicator and value accordingly.
        nodes = bnf.create_product_nodes(node, parents_dict[node], universal_dict, non_leaf_nodes)
        marginalized_onto = nodes["marginalized_onto"]
        # print("node",node, "buckets", buckets, "marginalized::", marginalized_onto, "nodes", nodes)

        # FOR loop only executes for a leaf node
        for marginalized_onto_node in marginalized_onto:
            # print(buckets.get(marginalized_onto_node), marginalized_onto_node)
            if buckets.get(marginalized_onto_node) is None:
                # print("created New node in the bucket ::", marginalized_onto_node)
                buckets[marginalized_onto_node] = nodes[marginalized_onto_node]["product_nodes"]
                # buckets[marginalized_onto_node] = nodes["product_nodes"]
                continue

            for key, value in nodes[marginalized_onto_node]["product_nodes"].items():
                product_node = sf.create_node("product", None, [buckets[marginalized_onto_node][key], value],
                                              marginalized_onto_node, key)
                buckets[marginalized_onto_node][key] = product_node

        # if marginalized_onto == None, then that means the node we are removing is not a leaf node
        # which means we will have to calculate potentials and then delete the current node
        if not marginalized_onto:
            node_value_obj = nodes["product_nodes"]
            # print("key", nodes["node_key"], node_obj)
            buckets = bnf.eliminate_node(node, node_value_obj, buckets, nodes["node_name"])
            # print("Buckets:", buckets)

    # print("BUCKETS ::", buckets)
    return buckets


def main(absolute_file_path, evidence=None):
    bn_network = bnf.read_bn_file(absolute_file_path)  # reads BIF file
    bnf.check_bn_model(bn_network)  # verify the BN is correct
    bn_graph_nodes, parents_dict, non_leaf_nodes = bnf.get_bn_graph_nodes(bn_network)  # converts data into usable format
    universal_dict = sf.create_universal_dict(bn_graph_nodes)  # create a universal dict: {"A":{"0":0.9, "1":0.1}}
    elimination_orders = bnf.find_elimination_order(bn_network, bn_graph_nodes)  # calculate elimination orders for BN

    elimination_order = elimination_orders["topological"]
    print("Elimination Order (Topological - Reversed) :: ", elimination_order)

    buckets = create_sum_product_network(elimination_order, universal_dict, parents_dict, non_leaf_nodes)

    for key, value in buckets.items():
        print("Evaluation of Arithmetic circuit yields " + key + ": " + str(bnf.evaluate_arithmetic_circuit(value)))
        if evidence:
            print("Evaluation of Arithmetic Circuit based on evidence "+evidence+" yields :: ", str(bnf.evaluate_arithmetic_circuit(value, evidence)))

    file_name = absolute_file_path.split("/")[-1].split(".")[0]
    plot.plot_graphviz(buckets, file_name, sf.nodes_stats)

    print("Nodes statistics ::", sf.nodes_stats)


bif_file = ''  # Path of the Bif file.
main(bif_file, None)  # Provide Evidence values here.

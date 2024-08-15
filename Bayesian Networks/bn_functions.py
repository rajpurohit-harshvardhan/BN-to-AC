# Description:
# This file contains all the functions implementing the functionalities of a bayesian network

from pgmpy.readwrite import BIFReader
from pgmpy.models import BayesianNetwork
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference.EliminationOrder import WeightedMinFill, MinFill, MinWeight, MinNeighbors
import networkx as nx

import helper
import structure_functions as sf


# reads the bif file and converts it into common format using BIFReader
# Input: {path: "....Absolute_path_to_bif_file...."}
# Output: {...bn_object_from_pgmpy...}
def read_bn_file(path):
    return BIFReader(path)


# checks whether the BN model, read from the file, is correct or incorrect. Throws an error if incorrect
# Input: {bn_network: ...bn_object_from_pgmpy...}
# Output: True or ERROR
def check_bn_model(bn_network):
    if bn_network.get_model().check_model():
        return True
    else:
        raise Exception("Bayesian Network model is Incorrect!")


# reads the bn_network and creates common dict used for further conversions.
# Input: {bn_network: ...bn_object_from_pgmpy...}
# Output: {bn_graph_nodes: {"A":{"states":["0", "1"], "parents":[], "values":[[0.9, 0.1]}},
#           parents: {"B": ["A"]},
#           non_leaf_nodes: ["A"]}
def get_bn_graph_nodes(bn_network):
    bn_graph_nodes = {}
    non_leaf_nodes = []
    states = bn_network.get_states()
    values = bn_network.get_values()
    parents = bn_network.get_parents()
    for node in bn_network.get_variables():
        bn_graph_nodes[node] = {
            "states": states[node],
            "values": values[node],
            "parents": parents[node]
        }
        non_leaf_nodes = list(set(non_leaf_nodes + parents[node]))
    return bn_graph_nodes, parents, non_leaf_nodes


# Calculates the marginal and updates the distribution accordingly as per the representation of a node format
# Input: {distribution: {"0,0": {..node_format..}, "0,1": {..}}, node: "B", parents: "A", variable_index: 5}
# Output: {"0": {..node_format..}, "1": {..node_format..}}
# The output is basically a marginalized distribution of A obtained by summing appropriate values of B
def marginalize(distribution, node, parents, variable_index=0):
    distribution = helper.convert_keys_to_tuple(distribution)  # conversion to tuple for easier calculation
    marginalized_distribution = {}

    for key, value in distribution.items():
        marginalized_key = key[:variable_index] + key[
                                                  variable_index + 1:]  # selecting every other keys except the one to be removed

        # creating indicator and value nodes and the product node for the same indicator node
        indicator_node = sf.create_node("indicator", 1, [], node, key[variable_index])
        value_node = sf.create_node("value", value, [], node, key[variable_index])
        product_node = sf.create_node("product", None, [indicator_node, value_node], node, key[variable_index])

        if marginalized_key in marginalized_distribution:
            # Just adding thus node to the references of an already present sum node
            marginalized_distribution[marginalized_key]["references"].append(product_node)
        else:
            # Creating a sum node to highlight the summing of 2 product nodes
            marginalized_distribution[marginalized_key] = sf.create_node("sum", None, [product_node], parents,
                                                                         ",".join(marginalized_key))
    return helper.convert_keys_to_string(marginalized_distribution)  # conversion of keys to string


# Same functionality as the function above with the only difference of not creation of indicator/sum/product nodes
# Input: {distribution: {"0,0": {..node_format..}, "0,1": {..}}, variables_other_than_node: "B", variable_index: 5}
# Output: {"0": {..node_format..}, "1": {..node_format..}}
def marginalize_onto(distribution, variables_other_than_node, variable_index):
    distribution = helper.convert_keys_to_tuple(distribution)
    marginalized_distribution = {}

    for key, value in distribution.items():
        marginalized_key = key[:variable_index] + key[variable_index + 1:]

        if marginalized_key in marginalized_distribution:
            marginalized_distribution[marginalized_key]["references"].append(value)
        else:
            marginalized_distribution[marginalized_key] = sf.create_node("sum", None, [value],
                                                                         variables_other_than_node,
                                                                         ",".join(marginalized_key))
    helper.convert_keys_to_string(distribution)
    return helper.convert_keys_to_string(marginalized_distribution)


# Function used to create the initial product nodes between the indicator nodes and probability nodes
# Input: {node:"B", parents:["A"], universal_dict: {"A":{"0":0.9, "1":0.1} ..}, non_leaf_nodes: ["A"]}
# Output: {product_nodes: {"0": {..node_format..} ..}, marginalized_onto: ["A"], node_name: "B,A"}
def create_product_nodes(node, parents, universal_dict, non_leaf_nodes):
    product_nodes = {}

    # This condition identifies if the current node is a leaf node,
    # in that case we directly calculate marginal over its parents
    if len(parents) != 0 and node not in non_leaf_nodes:
        # Marginalize onto the parents
        marginalized = {
            ",".join(parents): {
                "product_nodes": marginalize(universal_dict[node], node, ",".join(parents))
            },
            "marginalized_onto": [",".join(parents)]
        }
        return marginalized

    # node_name is used for creating potentials later on in the process
    node_name = node
    if len(parents) != 0:
        node_name = node + "," + ",".join(parents)

    # creates indicator/value and their product nodes in the graph
    for key, value in universal_dict[node].items():
        indicator_node = sf.create_node("indicator", 1, [], node, key.split(",")[0])
        value_node = sf.create_node("value", value, [], node, key)
        product_node = sf.create_node("product", None, [indicator_node, value_node], node, key)
        product_nodes[key] = product_node
    return {"product_nodes": product_nodes, "marginalized_onto": [], "node_name": node_name}


# Functions evaluates the created AC and returns appropriate responses as per the inputs
# Input: {node: {..node_format..}, evidence: "B=0|A=1"}
# Output: 0.55
def evaluate_arithmetic_circuit(node, evidence=None):
    # print(node["type"])
    node_type = node["type"]

    if node_type == "value":
        return node["value"]
    elif node_type == "sum":
        if type(node["references"]) == list:
            result = sum(evaluate_arithmetic_circuit(child, evidence) for child in node["references"])
            # print(node_type + ":" + node["node"] + ":" + node["variable_value"] + ":" + str(result))
            return result
        else:
            result = sum(evaluate_arithmetic_circuit(child_value, evidence) for child_key, child_value in
                         node["references"].items())
            # print(node_type + ":" + node["node"] + ":" + node["variable_value"] + ":" + str(result))
            return result
    elif node_type == "product":
        result = 1
        for child in node["references"]:
            result *= evaluate_arithmetic_circuit(child, evidence)
        # print(node_type+":"+node["node"]+":"+node["variable_value"]+":"+str(result))
        return result

    # if the interpreter reaches here it means, that current node is an indicator node,
    # and since no evidence is provided, meaning we have all the indicator set to 1
    if not evidence:
        return 1

    indicator_value = None
    for item in evidence.split("|"):
        item = item.split("=")   # Example: evidence = "B=0|A=1" then item = B=0
        item_variable = item[0].strip()  # item[0] = B
        item_value = item[1].strip()  # item[1] = 0

        if node["node"] == item_variable and node["variable_value"] == item_value:
            # print("TURNING ON Indicator for ::", node)
            indicator_value = 1
        elif node["node"] == item_variable and node["variable_value"] != item_value:
            # print("OFFF for Indicator for ::", node)
            indicator_value = 0

    # Execution of this condition checks for the case when current_node = C and evidence is on B and A,
    # in that case, all the indicators for current node (which is C) have to be turned on
    if indicator_value is None:
        indicator_value = 1

    # print(node_type + ":" + node["node"] + ":" + node["variable_value"] + ":" + str(indicator_value))
    return indicator_value


# function finds the elimination orders using the bn_network and common bn_graph_node network
# Input: {bn_network: ...bn_object_from_pgmpy...,
#         bn_graph_nodes: {"A":{"states":["0", "1"], "parents":[], "values":[[0.9, 0.1]}}
#         }
# Output: {"topological": ["B", "A"], "min_fill": [..], "min_weight": [..],
#           "min_neighbors": [..], "weighted_min_fill": [..]}
def find_elimination_order(bn_network, bn_graph_nodes):
    edges = bn_network.get_edges()
    cpds = []

    model = BayesianNetwork(edges)

    for node in bn_graph_nodes:
        parents_states_dimension = []
        for parent in bn_graph_nodes[node]['parents']:
            parents_states_dimension.append(len(bn_graph_nodes[parent]['states']))

        if len(parents_states_dimension):
            cpds.append(TabularCPD(
                node,
                len(bn_graph_nodes[node]['states']),
                bn_graph_nodes[node]['values'],
                bn_graph_nodes[node]['parents'],
                parents_states_dimension))
        else:
            cpds.append(TabularCPD(
                node,
                len(bn_graph_nodes[node]['states']),
                bn_graph_nodes[node]['values']))

    model.add_cpds(*cpds)

    model.check_model()
    elimination_orders = {}
    elimination_orders['min_fill'] = MinFill(model).get_elimination_order(bn_network.get_variables())
    elimination_orders['min_weight'] = MinWeight(model).get_elimination_order(bn_network.get_variables())
    elimination_orders['min_neighbors'] = MinNeighbors(model).get_elimination_order(bn_network.get_variables())
    elimination_orders['weighted_min_fill'] = WeightedMinFill(model).get_elimination_order(bn_network.get_variables())
    elimination_orders['topological'] = list(reversed(list(nx.topological_sort(model))))
    return elimination_orders


# function used to remove the node from a distribution, basically create a marginal over the rest of the variables
# Input: {new_buckets: {"B,C,A": {..node_format..}}, bucket_name: "B,C,A", selected_node_index: 1}
# Output: {"B,A": {..node_format..}}
def remove_node_from_potential(new_buckets, bucket_name, selected_node_index):
    delete_bucket_item = True  # used to delete the existing bucket from new_buckets dict

    # deduce the bucket name when node C is removed from B,C,A
    variables_other_than_node = bucket_name.split(",")
    del variables_other_than_node[selected_node_index]
    variables_other_than_node = ",".join(variables_other_than_node)

    # Handles the case when you want to remove the only bucket that exists in new_bucket
    if len(variables_other_than_node) == 0:
        variables_other_than_node = bucket_name
        delete_bucket_item = False

    # calculates the marginal distribution over every other variable except the one we need to remove
    marginalized_distribution = marginalize_onto(new_buckets[bucket_name], variables_other_than_node,
                                                 selected_node_index)

    # delete the old bucket, in our case delete "B,C,A": {..node_format..}
    if delete_bucket_item:
        del new_buckets[bucket_name]

    # handles the case when we have {new_buckets: {"B,C,A":{..}, "B,A":{..}}, bucket_name: "B,C,A"}
    # basically the case when we already have a bucket with the same name as we created after marginalizing,
    # In that case, we will have to create a potential over the contents of both the buckets
    if variables_other_than_node in new_buckets and delete_bucket_item:
        return calculate_potential(new_buckets[variables_other_than_node], marginalized_distribution,
                                   variables_other_than_node, {}, selected_node_index, 0, False,
                                   variables_other_than_node, True)

    # When we only have 1 bucket in new_bucket, and we create the marginal over itself, we get key:"" as response.
    # To handle that we just check for the length of the key to assign the proper values
    for key in marginalized_distribution.keys():
        if len(key) == 0:
            new_buckets[variables_other_than_node] = marginalized_distribution[key]
            break
        else:
            new_buckets[variables_other_than_node] = marginalized_distribution
            break
    return new_buckets


# function provides the bucket name after checking all the necessary conditions
# Input: {new_buckets: {"A":{..}}, bucket_item: "B,C", current_node_name:"A"}
# Output: {bucket_name: "B,C,A", is_name_changed: True, new_buckets:{}}
def deduce_bucket_name(new_buckets, bucket_item, current_node_name):
    is_name_changed = False
    bucket_name = bucket_item

    # this condition checks that if there are variables that are not in the potential to be calculated, then we add them
    if len(",".join(current_node_name)) > 0 and ",".join(current_node_name) not in bucket_name:
        is_name_changed = True
        bucket_name = ",".join(bucket_item.split(",") + current_node_name)

    # we remove the existing network since we will be calculating a new potential over the new variables
    if bucket_item in new_buckets:
        del new_buckets[bucket_item]
    return bucket_name, is_name_changed, new_buckets


# This function uses the functions defined above and calculates a potential over variables
# Input: {selected_node_obj: {"0,0":{..}, "0,1":{..}}, current_node_obj: {"0,0":{..}, "0,1":{..}},
#         bucket_name: "B,C,A", new_buckets:{"B,C":{..}}, selected_node_index: 1, current_node_index: 0,
#         is_name_changed: True, current_node: "B", is_bucket_item_equal_to_bucket_name: False}
# Output: {"B,C,A":{..}}
def calculate_potential(selected_node_obj, current_node_obj, bucket_name, new_buckets, selected_node_index,
                        current_node_index, is_name_changed, current_node, is_bucket_item_equal_to_bucket_name):
    for selected_node_key, selected_node_value in selected_node_obj.items():  # loop over all the possible values
        selected_node_key = selected_node_key.split(",")  # splitting for ease in calculation

        for current_node_key, current_node_value in current_node_obj.items(): # loop over all values for current node
            current_node_key = current_node_key.split(",")  # splitting for ease in calculation

            # Condition is to identify the case when we want to create potential between 2 buckets with same key-values
            # pairs but different altogether
            if is_bucket_item_equal_to_bucket_name:
                if ",".join(current_node_key) == ",".join(selected_node_key):
                    if bucket_name not in new_buckets:
                        new_buckets[bucket_name] = {}
                    new_buckets[bucket_name][",".join(selected_node_key)] = sf.create_node("product", None,
                                                                                           [selected_node_value,
                                                                                            current_node_value],
                                                                                           current_node,
                                                                                           ",".join(current_node_key))
                    continue
                else:
                    continue

            # Condition to check for the same variable value for node in either keys
            # if selected_node is for B,C > selected_node_key can be 0,0 / 0,1 / 1,0 / 0,0 and selected_node_index = 0
            # if current_node is for B,A > current_node_key can be 0,0 / 0,1 / 1,0 / 0,0 and current_node_index = 0
            # therefore we need to check selected_node_key[0] = current_node_key[0] for all these cases
            if selected_node_key[selected_node_index] == current_node_key[current_node_index]:

                if bucket_name not in new_buckets:
                    new_buckets[bucket_name] = {}

                current_key = current_node_key
                del current_key[current_node_index]

                new_bucket_node_key = ",".join(selected_node_key)
                if is_name_changed:
                    # if name is changed, meaning we have appended another node in the name and thus will have new key
                    new_bucket_node_key = ",".join(selected_node_key + current_key)

                # if we have already created a product node for the given key, we do not want to overwrite it.
                is_duplicate = False
                if new_bucket_node_key in new_buckets[bucket_name]:
                    is_duplicate = True
                if not is_duplicate:
                    new_buckets[bucket_name][new_bucket_node_key] = sf.create_node("product", None,
                                                                                   [selected_node_value,
                                                                                    current_node_value],
                                                                                   current_node,
                                                                                   ",".join(current_node_key))
    return new_buckets


# function uses all the above functions to eliminate a node from the dict of buckets.
# First, it calculates the new bucket name based on the inputs
# then it calculates the potentials and updates the buckets
# then removes the node from the buckets
# Input : {node: "B", node_value_obj: {"0,0":{..}, "0,1":{..}}, buckets: {"B,C,A": {..}}, current_node_name: "B,A"}
# Output: {"C,A": {..}}
def eliminate_node(node, node_value_obj, buckets, current_node_name):
    # print("Eliminating node ::", node)

    # removing the node to be eliminated from the node_name to achieve nodes for which potential bucket would be created
    current_node_index = current_node_name.split(",").index(node)
    current_node_name = current_node_name.split(",")
    del current_node_name[current_node_index]

    new_buckets = {}
    # print("BUCKET ::", buckets.keys())

    for item in buckets:
        if node not in item:
            # if the current bucket does not contain the node variable, then we leave that bucket as it is
            new_buckets[item] = buckets[item]
            continue

        # finding the index of the node variable to be removed for calculation of potentials
        index = item.split(",").index(node)
        if index > -1:
            bucket_name, is_name_changed, new_buckets = deduce_bucket_name(new_buckets, item, current_node_name)

            # True, means potential bucket we will be calculating already exists in the buckets' dict,
            # False, means they are different buckets and thus requires normal calculation
            is_bucket_item_equal_to_bucket_name = item == bucket_name and len(buckets[item].keys()) == len(
                node_value_obj.keys())
            new_buckets = calculate_potential(buckets[item], node_value_obj, bucket_name, new_buckets, index,
                                              current_node_index, is_name_changed, node,
                                              is_bucket_item_equal_to_bucket_name)
            new_buckets = remove_node_from_potential(new_buckets, bucket_name, index)
        else:
            # if the current bucket does not contain the node variable, then we leave that bucket as it is
            new_buckets[item] = buckets[item]

    return new_buckets

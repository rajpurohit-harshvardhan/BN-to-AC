# Description:
# Helper functions that are commonly used in all the files

# used to convert a n-dimension array to 1D
def flatten(xss):
    return [x for xs in xss for x in xs]


# converts the items of list to string
def convert_list_items_to_string(input_list):
    result = []
    for item in input_list:
        result.append(','.join(map(str, item)))
    return result


# converts the keys of the dict to string
def convert_keys_to_string(dictionary):
    for item in list(dictionary):
        if type(item) is tuple:
            dictionary[",".join(map(str, item))] = dictionary.pop(item)
    return dictionary


# converts the keys of the dict to tuple
def convert_keys_to_tuple(dictionary):
    for item in list(dictionary):
        dictionary[tuple(item.split(","))] = dictionary.pop(item)
    return dictionary

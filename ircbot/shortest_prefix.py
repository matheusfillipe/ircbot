import itertools


# A class to store a Trie node
class TrieNode:
    def __init__(self):
        # each node stores a dictionary to its child nodes
        self.child = {}

        # keep track of the total number of times the current node is visited
        # while inserting data in Trie
        self.freq = 0


# Function to insert a given string into a Trie
def insert(root, word):

    # start from the root node
    curr = root
    for c in word:
        # create a new node if the path doesn't exist
        curr.child.setdefault(c, TrieNode())

        # increment frequency
        curr.child[c].freq += 1

        # go to the next node
        curr = curr.child[c]


# Function to recursively traverse the Trie in a preorder fashion and
def shortest_prefix(root, word_so_far):
    if root is None:
        return ""

    # print `word_so_far` if the current Trie node is visited only once
    if root.freq == 1:
        return word_so_far

    # recur for all child nodes
    r = []
    for k, v in root.child.items():
        r.append(shortest_prefix(v, word_so_far + k))
    return r


# Find the shortest unique prefix for every word in a given array
def find_shortest_prefix(words):

    # construct a Trie from the given items
    root = TrieNode()
    for s in words:
        insert(root, s)

    # Recursively traverse the Trie in a preorder fashion to list all prefixes
    r = shortest_prefix(root, "")
    R = list(itertools.chain(*r))
    while any([isinstance(elm, list) for elm in R]):
        R = list(itertools.chain(*R))

    # DIRT FIX HERE
    reordered = {}
    for r in R:
        w = None
        for w in words:
            if w.startswith(r):
                reordered[w] = r
                break
        if w is not None:
            words.remove(w)
    return reordered


if __name__ == "__main__":
    print(
        find_shortest_prefix(["board", "move", "colors", "undo", "hint", "score", "label", "start", "accept", "help"])
    )

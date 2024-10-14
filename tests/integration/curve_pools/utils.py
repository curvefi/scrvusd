from itertools import combinations
import address_book as ab
import random


def generate_list_combinations(data_list, combo_sizes, randomize=False):
    combos = []
    for count in combo_sizes:
        for combo in combinations(data_list, count):
            combos.append(list(combo))  # Convert each combination to a list
    if randomize:
        random.shuffle(combos)
    return combos


# test functionality if run as a script
if __name__ == "__main__":
    combos = generate_list_combinations(ab.all_stables, [1, 2])
    print(combos)
    print(len(combos))

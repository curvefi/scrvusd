from itertools import combinations
import address_book as ab


def generate_token_combinations(other_tokens):
    """Generate all unique combinations with my_token and 1–2 other tokens."""
    combos = []
    for count in range(1, 3):  # for 2 or 3 tokens in total
        for combo in combinations(other_tokens.values(), count):
            combos.append([*combo])
    return combos


# test functionality if run as a script
if __name__ == "__main__":
    combos = generate_token_combinations(ab.all_stables)
    print(combos)
    print(len(combos))

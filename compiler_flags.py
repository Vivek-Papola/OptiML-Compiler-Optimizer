import random
all_flags = [
    "-O1", "-O2", "-O3", "-Os"
]

def generate_random_flags():
    return [random.randint(0, 1) for _ in all_flags]

def apply_flags(bit_vector):
    return [flag for flag, bit in zip(all_flags, bit_vector) if bit]

import os
import random
import subprocess
import time
from compiler_flags import all_flags, generate_random_flags, apply_flags
from benchmark_runner import compile_and_run

# GA hyperparameters
POP_SIZE = 20
GENS = 10
MUTATION_RATE = 0.2
C_SOURCE = 'test_program.c'

def fitness(flag_set):
    exec_time = compile_and_run(C_SOURCE, flag_set)
    return 1 / exec_time if exec_time > 0 else 0

def selection(pop, scores):
    selected = random.choices(population=pop, weights=scores, k=2)
    return selected

def crossover(parent1, parent2):
    idx = random.randint(1, len(parent1)-1)
    return parent1[:idx] + parent2[idx:]

def mutate(child):
    if random.random() < MUTATION_RATE:
        flip_index = random.randint(0, len(child) - 1)
        child[flip_index] = 1 - child[flip_index]
    return child

def main():
    population = [generate_random_flags() for _ in range(POP_SIZE)]
    
    for gen in range(GENS):
        print(f"\n[Generation {gen+1}]")
        scores = [fitness(apply_flags(ind)) for ind in population]
        
        best_idx = scores.index(max(scores))
        print("Best flags this gen:", apply_flags(population[best_idx]), f"Score: {scores[best_idx]:.4f}")
        
        new_population = []
        while len(new_population) < POP_SIZE:
            p1, p2 = selection(population, scores)
            child = crossover(p1, p2)
            child = mutate(child)
            new_population.append(child)
        
        population = new_population
    
    # Final output
    scores = [fitness(apply_flags(ind)) for ind in population]
    best_idx = scores.index(max(scores))
    best_flags = apply_flags(population[best_idx])
    print("\n🏁 Final best flag combination:", best_flags)

if __name__ == "__main__":
    main()

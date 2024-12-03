import numpy as np
from simulation import RestaurantSimulator
import pandas as pd
import time

class DifferentialEvolution:
    def __init__(self, simulator, bounds, population_size, 
                 mutation_factor, crossover_rate, generations):
        """
        Initialize the Differential Evolution optimizer.

        Parameters:
        - simulator (RestaurantSimulator): An instance of the RestaurantSimulator class.
        - bounds (list of tuples): List of (lower_bound, upper_bound) for each parameter to optimize.
        - population_size (int): Number of individuals in the population.
        - mutation_factor (float): Mutation factor (m) in [0, 2].
        - crossover_rate (float): Crossover rate (c) in (0, 1).
        - generations (int): Number of generations (iterations).
        """
        self.simulator = simulator
        self.bounds = bounds
        self.population_size = population_size
        self.mutation_factor = mutation_factor
        self.crossover_rate = crossover_rate
        self.generations = generations

        # Placeholder for the population initialization
        self.population = None

    def initialize_population(self):
        """
        Initialize the population uniformly within the given bounds.
        """
        samples = []
        
        for low, high in self.bounds:
            low = max(low, 0)
            samples.append(np.random.randint(low, high + 1, size=self.population_size)) 
        
        self.population = np.stack(samples, axis=-1)

    def mutate(self, current_idx):
        """
        Create a mutant vector using three randomly selected, distinct vectors.
        """
        mutant = np.zeros_like(self.population[0])
        valid_indexes = np.delete(np.arange(self.population_size), current_idx)  
        random_indexes = np.random.choice(valid_indexes, size=3, replace=False)  # Choose 3 random indexes
            
        mutant = (self.population[random_indexes[0]] + 
            self.mutation_factor * (self.population[random_indexes[1]] - self.population[random_indexes[2]]))
        
        mutant = np.maximum(mutant, 0) 
        return mutant

    def recombine(self, target_vector, mutant_vector):
        """
        Generate a trial vector by recombining the target and mutant vectors.
        """
        D = len(target_vector)
        child = np.zeros_like(self.population[0])
        randj = np.random.randint(0, D)  # Random index for crossover enforcement
        for j in range(D):
            unif = np.random.uniform(0, 1)
            if unif < self.crossover_rate or j == randj:
                child[j] = mutant_vector[j]
            else:
                child[j] = target_vector[j]
        
        child = np.maximum(child, 0)  # Clamp values to 0 or higher
        return child

    def select(self, target_vector, trial_vector):
        """
        Select the better vector based on the objective function value.
        """
        target_profit = self.objective_function(target_vector)
        trial_profit =  self.objective_function(trial_vector)
        if trial_profit > target_profit:
            return trial_vector, trial_profit
        else:
            return target_vector, target_profit

    def objective_function(self, params, num_runs = 1):
        # Maybe this should be ran multiple times to get a accurate expectation
        """
        Define the objective function to minimize (e.g., negative profit).
        This should use the RestaurantSimulator instance to evaluate the performance.
        """
        num_cooks, num_servers, inventory_list = self.unpack_params(params)

        self.simulator.num_cooks = num_cooks
        self.simulator.num_servers = num_servers
        self.simulator.init_inventory_df['Quantity'] = inventory_list
        profit = []
        for _ in range(num_runs):
            self.simulator.run_simulation()
            profit.append(self.simulator.calculate_profit())
        return np.mean(profit)
        
    
    def unpack_params(self, params):
        num_cooks = params[0]
        num_servers = params[1]
        inventory_list = np.array(params[2:], dtype=int)
        return num_cooks, num_servers, inventory_list
    
    def pack_params (self, num_cooks, num_servers, inventory_list):
        params = [num_cooks, num_servers]
        params.extend(inventory_list)
        return params

    def optimize(self):
        """
        Perform the Differential Evolution optimization loop.
        """
        self.initialize_population()
        best_profit = -float('inf')  
        best_params = None
        for g in range(self.generations):
            start_time = time.time()
            for i in range(self.population_size):
                # Select the target vector for the current individual
                target_vector = self.population[i]
                
                # Create a mutant vector through mutation
                mutant_vector = self.mutate(i)
                
                # Recombine target and mutant vectors to create a trial vector
                trial_vector = self.recombine(target_vector, mutant_vector)
                
                trial_vector = np.maximum(trial_vector, 0)  # Clamp values to 0 or higher
                # Select the best vector between target and trial based on objective function
                best_vector, profit = self.select(target_vector, trial_vector)
                
                # Update the population
                self.population[i] = best_vector

                if profit > best_profit:
                    best_profit = profit
                    best_params = self.population[i]
                
                if np.all(self.population == self.population[0]):
                    print(f"Convergence reached at generation {g}. All vectors are identical.")
                    break
            execution_time = time.time() - start_time
            print(f"Execution time: {execution_time} seconds")
    
            if g % 10 == 0:
                print(f"Generation {g}: Best Objective Value = {best_profit}, Best Parameters = {best_params}")

        return self.unpack_params(best_params)

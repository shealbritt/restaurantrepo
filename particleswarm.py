import numpy as np
import pandas as pd
from simulation import RestaurantSimulator 

class PSOOptimizer:
    def __init__(self, simulation_params, swarm_size=20, max_iter=50):
        """
        Initialize the PSO optimizer.

        Parameters:
        - simulation_params (dict): Parameters to initialize the RestaurantSimulator.
        - swarm_size (int): Number of particles in the swarm.
        - max_iter (int): Maximum number of iterations.
        """
        self.simulation_params = simulation_params
        self.swarm_size = swarm_size
        self.max_iter = max_iter
        self.dimension = 2 + len(simulation_params['inventory_df'])  # num_servers, num_cooks, inventory quantities
        self.bounds = {
            "num_servers": (1, 10), 
            "num_cooks": (1, 10),
            "inventory": (0, 100) 
        }
        self.global_best_position = None
        self.global_best_value = float('-inf')
    
    def initialize_particles(self):
        """
        Initialize the particles with random positions and velocities.
        """
        particles = []
        velocities = []
        for _ in range(self.swarm_size):
            position = np.array([
                np.random.randint(self.bounds['num_servers'][0], self.bounds['num_servers'][1] + 1),
                np.random.randint(self.bounds['num_cooks'][0], self.bounds['num_cooks'][1] + 1),
                *np.random.randint(self.bounds['inventory'][0], self.bounds['inventory'][1] + 1, len(self.simulation_params['inventory_df']))
            ])
            velocity = np.random.uniform(-1, 1, self.dimension)
            particles.append(position)
            velocities.append(velocity)
        return np.array(particles), np.array(velocities)

    def evaluate_particle(self, position):
        """
        Evaluate the fitness of a particle using the simulation.

        Parameters:
        - position (array): Particle position (num_servers, num_cooks, inventory quantities).

        Returns:
        - profit (float): The profit calculated by the simulator.
        """
        params = self.simulation_params.copy()
        params['num_servers'] = int(position[0])
        params['num_cooks'] = int(position[1])
        params['inventory_df']['Quantity'] = position[2:]
        simulator = RestaurantSimulator(**params)
        simulator.run_simulation()
        return simulator.calculate_profit()

    def optimize(self):
        """
        Perform PSO optimization.
        """
        particles, velocities = self.initialize_particles()
        personal_best_positions = particles.copy()
        personal_best_values = np.array([self.evaluate_particle(p) for p in particles])
        self.global_best_position = personal_best_positions[np.argmax(personal_best_values)]
        self.global_best_value = np.max(personal_best_values)
        
        w = 0.5  # Inertia weight
        c1, c2 = 1.5, 1.5  # Coefs

        # Make sure shape matches particle[i]
        lower_bounds = np.array([
            self.bounds["num_servers"][0],
            self.bounds["num_cooks"][0],
            *[self.bounds["inventory"][0]] * (self.dimension - 2)
        ])
        upper_bounds = np.array([
            self.bounds["num_servers"][1],
            self.bounds["num_cooks"][1],
            *[self.bounds["inventory"][1]] * (self.dimension - 2)
        ])

        for _ in range(self.max_iter):
            for i in range(self.swarm_size):
                r1, r2 = np.random.rand(), np.random.rand()
                cognitive_component = c1 * r1 * (personal_best_positions[i] - particles[i])
                social_component = c2 * r2 * (self.global_best_position - particles[i])
                velocities[i] = w * velocities[i] + cognitive_component + social_component
                particles[i] = np.clip(particles[i] + velocities[i], lower_bounds, upper_bounds)  # Update positions

                # Make sure integers because discrete variables
                particles[i][:2] = np.rint(particles[i][:2])  # num_servers, num_cooks
                particles[i][2:] = np.rint(particles[i][2:])  # inventory quantities

                # Evaluate fitness
                fitness = self.evaluate_particle(particles[i])
                if fitness > personal_best_values[i]:
                    personal_best_values[i] = fitness
                    personal_best_positions[i] = particles[i]

                if fitness > self.global_best_value:
                    self.global_best_value = fitness
                    self.global_best_position = particles[i]

        return self.global_best_position, self.global_best_value
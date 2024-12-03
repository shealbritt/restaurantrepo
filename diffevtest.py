import numpy as np
import pandas as pd
from simulation import RestaurantSimulator  # Assuming RestaurantSimulator is in 'simulation.py'
from diffev import DifferentialEvolution  # Assuming your DifferentialEvolution class is in 'optimization.py'

menu_data = {
            'Dish': ['Ramen', 'Sushi', 'Tsunami', 'Sakana/Okazu'],
            'Cost': [2.5, 2, 2, 3], # From Bosso meeting
            'SalePrice': [17, 6.5, 9, 19], # From Bosso menu
            'PrepTime': [0.0167+5/60, 0.0083 + 5/60, 0.0416 + 5/60, 0.0416 + 5/60],  # in hours (1 mins, 0.5 mins, 2.5 mins, 2.5 mins) From Bosso
            'DemandRating': [200/407, 67/407, 82/407, 158/407]
            }
menu_df = pd.DataFrame(menu_data)

        # Create a sample inventory DataFrame
inventory_data = {
                'Dish': ['Ramen', 'Sushi', 'Tsunami', 'Sakana/Okazu'],
                'Quantity': [483, 0, 0, 444]
            }
arrivalrates = [3, 38, 16, 2, 41, 44, 44, 34, 13, 4, 1]
arrivalrates = [3 * i for i in arrivalrates]
inventory_df = pd.DataFrame(inventory_data)
simulation_params = {
                "duration": 11,
                "arrival_rates": arrivalrates,
                "menu_df": menu_df,  
                "seating_capacity": 60, # Should be updated to be more accurate
                "num_cooks": 9, 
                "num_servers": 1, 
                "inventory_df": inventory_df, 
                "server_capacity": 10,
                "cook_capacity": 3,
                "cook_wage": 17.5, # Data from Bosso meeting
                "server_wage": 6.75, # Data from Bosso meeting
                "avg_consumption_time": 1. 
            }


simulator = RestaurantSimulator(**simulation_params)

# Define the bounds for the optimization (e.g., num_cooks, num_servers, inventory quantities)
bounds = [
    (1, 6),  # num_cooks (1 to 10 cooks)
    (1, 6),  # num_servers (1 to 10 servers)
    (10, 500),  # Inventory for Dish A
    (10, 500),  # Inventory for Dish B
    (10, 500),  # Inventory for Dish C
    (10, 500)  # Inventory for Dish C
]

# Set up Differential Evolution optimizer
optimizer = DifferentialEvolution(
    simulator=simulator,
    bounds=bounds,
    population_size=30,
    mutation_factor=0.8,
    crossover_rate=0.5,
    generations=75,
)

# Run the optimization
best_params = optimizer.optimize()

# Print the best parameters found by the optimization process
num_cooks, num_servers, inventory_list = optimizer.unpack_params(best_params)

# Print the best configuration
print(f"Best configuration:")
print(f"Number of Cooks: {num_cooks}")
print(f"Number of Servers: {num_servers}")
print(f"Inventory: {inventory_list[0]}")

# Set the best parameters into the simulator
simulator.num_cooks = num_cooks
simulator.num_servers = num_servers
simulator.inventory_df['Quantity'] = inventory_list[0]

# Run the simulation with the optimized parameters
simulator.run_simulation()

# Calculate the profit
profit = simulator.calculate_profit()
print(f"Profit from optimized configuration: {profit}")

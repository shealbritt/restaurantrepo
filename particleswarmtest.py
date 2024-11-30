import pandas as pd
from simulation import RestaurantSimulator
from particleswarm import PSOOptimizer

menu_data = {
    'Dish': ['Ramen', 'Sushi', 'Tsunami'],
    'Cost': [2.5, 2, 2], # From Bosso meeting
    'SalePrice': [17, 6.5, 9], # From Bosso menu
    'PrepTime': [0.167, 0.167, 0.25],  # in hours (10 mins, 10 mins, 15 mins)
    'DemandRating': [0.5, 0.3, 0.2]
    }
menu_df = pd.DataFrame(menu_data)

# Create a sample inventory DataFrame
inventory_data = {
        'Dish': ['Ramen', 'Sushi', 'Tsunami'],
        'Quantity': [100, 100, 100]
    }
inventory_df = pd.DataFrame(inventory_data)
simulation_params = {
        "duration": 12,
        "arrival_rate": 100,
        "menu_df": menu_df,  
        "seating_capacity": 50, # Should be updated to be more accurate
        "num_cooks": 5, 
        "num_servers": 5, 
        "inventory_df": inventory_df, 
        "server_capacity": 10,
        "cook_capacity": 10,
        "cook_wage": 17.5, # Data from Bosso meeting
        "server_wage": 6.75, # Data from Bosso meeting
        "avg_consumption_time": 30 
    }

optimizer = PSOOptimizer(simulation_params)
best_solution, best_profit = optimizer.optimize()
# num_servers, num_cooks, ramen quantity, sushi quantity, tsunami quantity
print("Best solution:", best_solution)
print("Maximum profit:", best_profit)

# Import necessary libraries
import numpy as np
import pandas as pd
from simulation import RestaurantSimulator
# Create a sample menu DataFrame
menu_data = {
    'Dish': ['Pizza', 'Burger', 'Salad'],
    'Cost': [5, 3, 2],
    'SalePrice': [10, 7, 5],
    'PrepTime': [0.25, 0.167, 0.083],  # in hours (15 mins, 10 mins, 5 mins)
    'DemandRating': [0.5, 0.3, 0.2]
}
menu_df = pd.DataFrame(menu_data)

# Create a sample inventory DataFrame
inventory_data = {
    'Dish': ['Pizza', 'Burger', 'Salad'],
    'Quantity': [10, 15, 20]
}
inventory_df = pd.DataFrame(inventory_data)

# Set labor costs and other parameters
labor_costs = {'cook': 10, 'server': 8}  # hourly wages
seating_capacity = 20
num_cooks = 2
num_servers = 3
server_capacity = 5  # max tables a server can handle
cook_capacity = 2  # max meals a cook can prepare simultaneously
cook_wage = 10
server_wage = 8
avg_consumption_time = 0.5  # in hours (30 minutes)

# Initialize the simulator
simulator = RestaurantSimulator(
    menu_df=menu_df,
    labor_costs=labor_costs,
    seating_capacity=seating_capacity,
    num_cooks=num_cooks,
    num_servers=num_servers,
    inventory_df=inventory_df,
    server_capacity=server_capacity,
    cook_capacity=cook_capacity,
    cook_wage=cook_wage,
    server_wage=server_wage,
    avg_consumption_time=avg_consumption_time
)

# Test simulation run
duration = 2  # in hours
arrival_rate = 30  # customers per hour

# Run the simulation
simulator.run_simulation(duration, arrival_rate)

# Calculate profit
profit = simulator.calculate_profit()
print(f"Net Profit: ${profit:.2f}")

# Check the order log
#print("Order Log:")
print(simulator.order_log)

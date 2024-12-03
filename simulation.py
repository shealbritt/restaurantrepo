import numpy as np
import pandas as pd
import heapq

class RestaurantSimulator:
    def __init__(self, duration, arrival_rates, 
                 menu_df, seating_capacity, num_cooks, 
                 num_servers, inventory_df, server_capacity, 
                 cook_capacity, cook_wage, server_wage, 
                 avg_consumption_time, inventory_discount = 0.2, variation_factor=0.5):
        """
        Initialize the restaurant simulator with key parameters.

        Parameters:
        - menu_df (DataFrame): DataFrame containing dishes with columns ['Dish', 'Cost', 'SalePrice', 'PrepTime', 'DemandRating'].
        - Note Prep time takes into account all time from the point in which a customer is seated to the time in which they're food arrives
        - seating_capacity (int): Number of tables in the restaurant.
        - num_cooks (int): Number of cooks available.
        - num_servers (int): Number of servers available.
        - inventory_df (DataFrame): DataFrame with columns ['Dish', 'Quantity'] for tracking inventory.
        """
        inventory_df['Quantity'] = inventory_df['Quantity'].clip(lower=0)
        self.menu_df = menu_df
        self.inventory_discount = inventory_discount
        self.seating_capacity = seating_capacity
        self.server_capacity = server_capacity
        self.variation_factor = variation_factor
        self.cook_capacity = cook_capacity
        self.num_cooks = max(num_cooks, 0)
        self.num_servers = max(num_servers, 0)
        self.init_inventory_df = inventory_df
        self.duration = duration
        self.arrival_rates = arrival_rates if isinstance(arrival_rates, list) else [arrival_rates]

        # State variables
        self.inventory_df = inventory_df.copy()
        self.available_tables = seating_capacity
        self.available_servers = self.server_capacity * self.num_servers
        self.available_cooks = self.cook_capacity * self.num_cooks
        self.customer_counter = 0 
        self.avg_consumption_time = avg_consumption_time
        self.cook_wage = cook_wage
        self.server_wage = server_wage
        self.customer_dissatisfaction = 0

        # queues
        self.event_queue = []
        self.server_queue = []
        self.cook_queue = []
    
    def reset(self):
        # State variables
        self.inventory_df = self.init_inventory_df.copy()
        self.num_cooks = max(self.num_cooks, 0)
        self.num_servers = max(self.num_servers, 0)
        self.available_tables = self.seating_capacity
        self.available_servers = self.server_capacity * self.num_servers
        self.available_cooks = self.cook_capacity * self.num_cooks
        self.order_log = pd.DataFrame(columns=['CustomerID', 'ArrivalTime', 'Dish', 'WaitTime', 'ConsumptionTime', 'Revenue', 'Cost', 'DepartureTime'])
        self.customer_counter = 0 
        self.customer_dissatisfaction = 0
        self.inventory_df['Quantity'] = self.inventory_df['Quantity'].clip(lower=0)
    

        # queues
        self.event_queue = []
        self.server_queue = []
        self.cook_queue = []

    def schedule_event(self, time, event_type, customer_id=None):
        """
        Add an event to the priority queue.
        """
        heapq.heappush(self.event_queue, (time, event_type, customer_id))

    def process_event(self):
        """
        Process the next event from the queue.
        """
        if not self.event_queue:
            return False

        current_time, event_type, customer_id,  = heapq.heappop(self.event_queue)
        if current_time > self.duration:
            return False
        if event_type == 'arrival':
            self.handle_arrival(current_time, customer_id)
        elif event_type == 'order':
            self.handle_order(current_time, customer_id)
        elif event_type == 'meal_prep':
            self.handle_meal_prep(current_time, customer_id)
        elif event_type == 'departure':
            self.handle_departure(current_time, customer_id)
        return True
    
    def handle_arrival(self, time, customer_id):
        if self.available_tables > 0:
            self.available_tables -= 1
            #seat customer
            self.add_customer(time, customer_id)
            self.schedule_event(time, 'order', customer_id)

    def handle_order(self, time, customer_id):
        if self.available_servers > 0:
            self.available_servers -= 1
            dish, isInventory = self.take_order(customer_id)
            if isInventory:
                prep_time = np.random.exponential(self.menu_df.loc[self.menu_df['Dish'] == dish, 'PrepTime'].values[0])
                if self.available_cooks > 0:
                    self.available_cooks -= 1
                    self.schedule_event(time + prep_time, 'meal_prep', customer_id)
                else:
                    self.cook_queue.append((prep_time, customer_id))
            else:
                print("Out of Inventory")
        else:
            self.server_queue.append((time, customer_id))
    
    def handle_meal_prep(self, time, customer_id):
        # Update logs
        self.available_cooks += 1
        arrival_time = self.order_log.loc[self.order_log['CustomerID'] == customer_id, 'ArrivalTime'].values[0]
        self.order_log.loc[self.order_log['CustomerID'] == customer_id, 'WaitTime'] = time - arrival_time
        consumption_time = np.random.exponential(self.avg_consumption_time)
        self.schedule_event(time + consumption_time, 'departure', customer_id)
        
        if self.cook_queue and self.available_cooks > 0:
            self.available_cooks -= 1
            queued_time, queued_id = self.cook_queue.pop(0)
            dish = self.order_log.loc[self.order_log["CustomerID"]==queued_id, "Dish"] .values[0]
            prep_time = np.random.exponential(self.menu_df.loc[self.menu_df['Dish'] == dish, 'PrepTime'].values[0])
            self.schedule_event(max(time, queued_time) + prep_time,"meal_prep", queued_id)

    def handle_departure(self, time, customer_id):
        self.available_tables += 1
        self.available_servers += 1
        arrival_time = self.order_log.loc[self.order_log['CustomerID'] == customer_id, 'ArrivalTime'].values[0]
        wait_time =  self.order_log.loc[self.order_log['CustomerID'] == customer_id, 'WaitTime'].values[0]
        self.order_log.loc[self.order_log["CustomerID"]==customer_id, "ConsumptionTime"] = time - arrival_time - wait_time
        self.order_log.loc[self.order_log["CustomerID"]==customer_id, "DepartureTime"] = time 
        dish =self.order_log.loc[self.order_log["CustomerID"]==customer_id, "Dish"].iloc[0] 
        sale_price = self.menu_df.loc[self.menu_df['Dish'] == dish, "SalePrice"].iloc[0]
        self.order_log.loc[self.order_log["CustomerID"]==customer_id, "Revenue"] = sale_price
        cost = self.menu_df.loc[self.menu_df['Dish'] == dish, "Cost"].iloc[0]
        self.order_log.loc[self.order_log["CustomerID"]==customer_id, "Cost"] = cost

        if self.server_queue and self.available_servers > 0:
            queued_time, queued_id = self.server_queue.pop(0)
            #print(time, queued_time)
            self.schedule_event(max(time, queued_time), 'order', queued_id)


    def generate_customer_id(self):
        self.customer_counter += 1
        return self.customer_counter
    
    def add_customer(self,time, customer_id):
    # Add a new row with just the CustomerID, rest as None
        new_row = pd.DataFrame([{'CustomerID': customer_id,  
                   'ArrivalTime': time, 
                   'Dish': None, 
                   'WaitTime': None, 
                   'ConsumptionTime': None, 
                   'Revenue': None, 
                   'Cost': None,
                   'DepartureTime': None}])
        self.order_log.loc[len(self.order_log)] = new_row.iloc[0]


    def take_order(self, customer_id):
        """
        Select a dish based on demand ranking and update the order log.
        """
        total_demand = self.menu_df['DemandRating'].sum()
        probabilities = self.menu_df['DemandRating'] / total_demand
        dish = np.random.choice(self.menu_df['Dish'], p=probabilities)    
        
        dish_inventory = self.inventory_df.loc[self.inventory_df['Dish'] == dish, 'Quantity'].values[0]
        if dish_inventory > 0:
            self.order_log.loc[self.order_log['CustomerID'] == customer_id, 'Dish'] = dish
            self.manage_inventory(dish)
            return dish, True
        else:
            self.customer_dissatisfaction += 1
            available_dishes = self.inventory_df[self.inventory_df['Quantity'] > 0]

            if available_dishes.empty:
                return None, False
            else:
                return self.take_order(customer_id)

        

    def manage_inventory(self, dish):
        """
        Update the inventory DataFrame based on the ingredients used for the dish.
        """
        self.inventory_df.loc[self.inventory_df['Dish'] == dish, 'Quantity'] -= 1
        
        
    def run_simulation(self):
        """
        Run the simulation loop for a given duration with the specified arrival rate.
        Duration is in hours 
        """
        self.reset()
        interval_length = self.duration / len(self.arrival_rates)
        t = 0 
        arrival_times = []
        
        for rate_index, rate in enumerate(self.arrival_rates):
            while t < self.duration and t < (rate_index + 1) * interval_length:
                time = np.random.exponential(1 / rate)
                if t + time > (rate_index + 1) * interval_length:
                    # dont cross into next interval
                    break
                arrival_times.append(t + time)
                t += time
            
            t = max(t, (rate_index + 1) * interval_length)
      
        for t in arrival_times:
            customer_id = self.generate_customer_id()
            self.schedule_event(t, 'arrival', customer_id)

        while self.event_queue:
            self.process_event()
            if(self.inventory_df['Quantity'] == 0).all():
                break
                



    def calculate_profit(self):
        """
        Calculate total revenue, total costs, and return the net profit.
        Wage per Hour
        """
        #print(self.order_log)
        total_revenue = self.order_log['Revenue'].sum()
        #print("revenue", total_revenue)
        labor_costs = self.duration * (self.num_cooks * self.cook_wage  + self.num_servers * self.server_wage)
        # Cost of Goods Sold
        sold_good_costs = self.order_log['Cost'].sum()
        
        # Cost 0f remaining inventory
        inventory_costs = 0
        merged_df = self.inventory_df.merge(self.menu_df[['Dish', 'Cost']], on='Dish', how='left')
        merged_df['Cost'] = merged_df['Cost'].fillna(0) 
        inventory_costs = (merged_df['Cost'] * merged_df['Quantity']).sum()
        return total_revenue - labor_costs - self.inventory_discount * inventory_costs - sold_good_costs - self.variation_factor * self.customer_dissatisfaction
    
    def transactions(self):
        total_revenue = self.order_log['Revenue'].sum()
        #print("revenue", total_revenue)
        labor_costs = self.duration * (self.num_cooks * self.cook_wage  + self.num_servers * self.server_wage)
        # Cost of Goods Sold
        sold_good_costs = self.order_log['Cost'].sum()
        
        return  total_revenue - labor_costs - sold_good_costs

if __name__ == "__main__":
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
    simulator.run_simulation()
    print("profit", simulator.calculate_profit())
    print("Order Log", simulator.order_log)
    print("inventory", simulator.inventory_df)
  

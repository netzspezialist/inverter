from collections import deque
import logging

class BMSStateManager:
    def __init__(self, logger):
        self.bms_state = {
            'voltage': None,
            'soc': None,
            'lowest_cell_voltage': None,
            'highest_cell_voltage': None,
            'timestamp': None
        }
        
        # Initialize a FIFO list for the last 10 states
        self.bms_state_history = deque(maxlen=10)
        
        # Initialize logger
        self.logger = logger

    def set_bms_state(self, state):
        """Set the current BMS state."""
        # Log the previous state
        self.logger.info(f"Previous BMS state: {self.previous_bms_state}")
        
        # Update previous state before setting the new state
        
        # Log the new state being set
        self.logger.info(f"Setting new BMS state: {state}")

        self.bms_state_history.append(self.state.copy())
        
        # Log the updated current state
        self.logger.info(f"Updated BMS state: {self.bms_state}")

    def get_previous_bms_state_from_history(self):
        """Get the previous state from the history list."""
        if len(self.bms_state_history) > 1:
            return self.bms_state_history[-2]
        else:
            return None

    def get_bms_state(self):
        """Get the last state from the history list."""
        if self.bms_state_history:
            return self.bms_state_history[-1]
        else:
            return None
    
    def get_bms_state_history(self):
        return self.bms_state_history[-1]
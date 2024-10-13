class InverterChargeManager:
    def __init__(self):
        self.charge_level = 0  # Initialize with a default charge level

    def update_charge_voltage(self, level):
        """Set the charge level."""
        self.charge_level = level
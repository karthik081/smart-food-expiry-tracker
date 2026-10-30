
import json
from pathlib import Path
from datetime import date, datetime, timedelta


class FoodExpiryTracker:
    def __init__(self, filename="food_inventory.json"):
        self.filename = Path(filename)
        self.food_items = []
        self.load_data()

    # Load saved records from the JSON file
    def load_data(self):
        if not self.filename.exists():
            self.save_data()
            return

        try:
            with self.filename.open("r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, list):
                raise ValueError("Inventory must be a JSON list.")

            self.food_items = data

        except (json.JSONDecodeError, ValueError) as error:
            print(f"Could not load inventory: {error}")
            print("Starting with an empty inventory.")
            self.food_items = []

    # Save records so they remain available after closing
    def save_data(self):
        with self.filename.open("w", encoding="utf-8") as file:
            json.dump(self.food_items, file, indent=4)

    @staticmethod
    def read_date(prompt):
        while True:
            value = input(prompt).strip()

            try:
                return datetime.strptime(
                    value, "%Y-%m-%d"
                ).date()
            except ValueError:
                print("Invalid date. Enter YYYY-MM-DD.")

    @staticmethod
    def read_positive_number(prompt):
        while True:
            try:
                value = float(input(prompt))

                if value <= 0:
                    print("Value must be greater than zero.")
                    continue

                return value

            except ValueError:
                print("Please enter a valid positive number.")

    def add_food(self):
        print("\n--- Add Food Item ---")

        name = input("Food name: ").strip().title()
        if not name:
            print("Food name cannot be empty.")
            return

        category = input(
            "Category (Dairy/Fruits/Vegetables/Other): "
        ).strip().title()

        if not category:
            print("Category cannot be empty.")
            return

        quantity = self.read_positive_number(
            "Quantity (units, kg, litres, etc.): "
        )

        unit = input("Quantity unit (kg, litre, packet, etc.): ").strip()
        if not unit:
            print("Unit cannot be empty.")
            return

        purchase_date = self.read_date(
            "Purchase date (YYYY-MM-DD): "
        )

        expiry_date = self.read_date(
            "Expiry date (YYYY-MM-DD): "
        )

        if expiry_date < purchase_date:
            print("Expiry date cannot be before purchase date.")
            return

        unit_price = self.read_positive_number(
            "Price per quantity unit (INR): "
        )

        next_id = max(
            (item.get("id", 0) for item in self.food_items),
            default=0
        ) + 1

        item = {
            "id": next_id,
            "name": name,
            "category": category,
            "quantity": quantity,
            "unit": unit,
            "purchase_date": purchase_date.isoformat(),
            "expiry_date": expiry_date.isoformat(),
            "unit_price": unit_price,
            "wasted_quantity": 0.0,
            "wasted_cost": 0.0
        }

        self.food_items.append(item)
        self.save_data()

        print(f"{name} added successfully. Item ID: {next_id}")

    def view_inventory(self):
        print("\n--- Food Inventory ---")

        if not self.food_items:
            print("No food items found.")
            return

        for item in self.food_items:
            print(
                f"ID: {item['id']} | {item['name']} | "
                f"Category: {item['category']} | "
                f"Quantity: {item['quantity']} {item['unit']} | "
                f"Expires: {item['expiry_date']} | "
                f"Unit price: Rs. {item['unit_price']:.2f}"
            )

    def search_food(self):
        keyword = input(
            "Enter food name or category to search: "
        ).strip().lower()

        matches = [
            item for item in self.food_items
            if keyword in item["name"].lower()
            or keyword in item["category"].lower()
        ]

        if not matches:
            print("No matching food items found.")
            return

        print("\n--- Search Results ---")
        for item in matches:
            print(
                f"ID: {item['id']} | {item['name']} | "
                f"{item['quantity']} {item['unit']} | "
                f"Expires: {item['expiry_date']}"
            )

    def expiry_report(self):
        today = date.today()
        limit = today + timedelta(days=7)

        expired = []
        expiring_soon = []
        safe = []

        for item in self.food_items:
            expiry = date.fromisoformat(item["expiry_date"])

            if item["quantity"] <= 0:
                continue

            if expiry < today:
                expired.append(item)
            elif expiry <= limit:
                expiring_soon.append(item)
            else:
                safe.append(item)

        print("\n--- Expiry Report ---")
        print(f"Today: {today.isoformat()}")

        print("\nEXPIRED ITEMS")
        self.display_items(expired)

        print("\nEXPIRING WITHIN 7 DAYS")
        self.display_items(expiring_soon)

        print("\nSAFE FOR NOW")
        self.display_items(safe)

    @staticmethod
    def display_items(items):
        if not items:
            print("None")
            return

        for item in items:
            print(
                f"{item['name']} | Quantity: "
                f"{item['quantity']} {item['unit']} | "
                f"Expiry: {item['expiry_date']}"
            )

    def mark_food_wasted(self):
        self.view_inventory()

        try:
            item_id = int(input("\nEnter food item ID: "))
        except ValueError:
            print("Please enter a valid ID.")
            return

        item = next(
            (x for x in self.food_items if x["id"] == item_id),
            None
        )

        if item is None:
            print("Food item not found.")
            return

        if item["quantity"] <= 0:
            print("No remaining quantity to record as waste.")
            return

        quantity = self.read_positive_number(
            f"Quantity wasted (maximum {item['quantity']}): "
        )

        if quantity > item["quantity"]:
            print("Wasted quantity cannot exceed available quantity.")
            return

        waste_cost = quantity * item["unit_price"]

        item["quantity"] = round(item["quantity"] - quantity, 6)
        item["wasted_quantity"] = round(
            item.get("wasted_quantity", 0) + quantity, 6
        )
        item["wasted_cost"] = round(
            item.get("wasted_cost", 0) + waste_cost, 2
        )

        self.save_data()

        print(f"Waste recorded: Rs. {waste_cost:.2f}")
        print(f"Remaining quantity: {item['quantity']} {item['unit']}")

    def delete_food(self):
        self.view_inventory()

        try:
            item_id = int(input("\nEnter item ID to delete: "))
        except ValueError:
            print("Please enter a valid ID.")
            return

        for item in self.food_items:
            if item["id"] == item_id:
                self.food_items.remove(item)
                self.save_data()
                print("Item deleted successfully.")
                return

        print("Item ID not found.")

    def analytics_report(self):
        print("\n--- Inventory and Waste Analytics ---")

        if not self.food_items:
            print("No records available for analysis.")
            return

        total_items = len(self.food_items)
        available = [
            item for item in self.food_items
            if item["quantity"] > 0
        ]

        inventory_value = sum(
            item["quantity"] * item["unit_price"]
            for item in self.food_items
        )

        waste_value = sum(
            item.get("wasted_cost", 0)
            for item in self.food_items
        )

        total_wasted_quantity = sum(
            item.get("wasted_quantity", 0)
            for item in self.food_items
        )

        print(f"Total recorded food types: {total_items}")
        print(f"Food types with stock remaining: {len(available)}")
        print(f"Estimated current inventory value: Rs. {inventory_value:.2f}")
        print(f"Recorded food waste cost: Rs. {waste_value:.2f}")
        print(f"Recorded wasted quantity: {total_wasted_quantity:.2f}")

        category_totals = {}

        for item in self.food_items:
            category = item["category"]
            category_totals[category] = (
                category_totals.get(category, 0)
                + item["quantity"] * item["unit_price"]
            )

        print("\nInventory value by category:")
        for category, amount in category_totals.items():
            print(f"{category}: Rs. {amount:.2f}")

        if waste_value > 0:
            print(
                "\nRecommendation: Review the food items with the "
                "highest recorded waste cost."
            )
        else:
            print(
                "\nNo food waste has been recorded yet. "
                "Record wasted quantities to generate waste insights."
            )

    def export_report(self):
        filename = "food_inventory_report.csv"

        try:
            import csv

            if not self.food_items:
                print("No inventory records to export.")
                return

            with open(filename, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.DictWriter(
                    file, fieldnames=self.food_items[0].keys()
                )
                writer.writeheader()
                writer.writerows(self.food_items)

            print(f"Report exported to {Path(filename).resolve()}")

        except OSError as error:
            print(f"Could not export report: {error}")


def main():
    tracker = FoodExpiryTracker()

    menu = """
========================================
 SMART FOOD EXPIRY TRACKER
========================================
1. Add Food Item
2. View Inventory
3. Search Food
4. Check Expiry Dates
5. Record Food Waste
6. View Analytics Report
7. Delete Food Item
8. Export CSV Report
9. Exit
========================================
"""

    while True:
        print(menu)
        choice = input("Enter your choice (1-9): ").strip()

        try:
            if choice == "1":
                tracker.add_food()
            elif choice == "2":
                tracker.view_inventory()
            elif choice == "3":
                tracker.search_food()
            elif choice == "4":
                tracker.expiry_report()
            elif choice == "5":
                tracker.mark_food_wasted()
            elif choice == "6":
                tracker.analytics_report()
            elif choice == "7":
                tracker.delete_food()
            elif choice == "8":
                tracker.export_report()
            elif choice == "9":
                print("Thank you for using Smart Food Expiry Tracker!")
                break
            else:
                print("Invalid choice. Enter a number from 1 to 9.")

        except (OSError, KeyError, TypeError, ValueError) as error:
            print(f"An error occurred: {error}")


if __name__ == "__main__":
    main()

import sys
import sqlite3

import db_queries
from app_functions import (
    add_item,
    change_quantity,
    checkout,
    display_basket,
    find_or_create_basket,
    remove_item,
    show_order_history,
)

# Force the terminal output to use UTF-8. 
sys.stdout.reconfigure(encoding="utf-8")

# Database file
DB_FILE = "parana.db"

# Open the database connection
db = sqlite3.connect(DB_FILE)
cursor = db.cursor()

# Ask for the shopper ID
shopper_id_text = input("Enter shopper ID: ")

if not shopper_id_text.isdigit():
    print("Invalid shopper ID")
    db.close()
    raise SystemExit

shopper_id = int(shopper_id_text)

# Find the shopper
shopper_row = db_queries.get_shopper(cursor, shopper_id)

if shopper_row is None:
    print("Shopper ID not found")
    db.close()
    raise SystemExit

# Only the first name is shown in the welcome message
print(f"\nWelcome {shopper_row[0]}")

# Find or create today's basket (silently - no message printed)
basket_id = find_or_create_basket(cursor, db, shopper_id)

# Main menu
while True:
    print("\nPARANÁ - SHOPPER MAIN MENU\n")
    print("-" * 50)
    print("    [1] Display your order history")
    print("    [2] Add an item to your basket")
    print("    [3] View your basket")
    print("    [4] Change the quantity of an item in your basket")
    print("    [5] Remove an item from your basket")
    print("    [6] Checkout")
    print("    [7] Exit")

    choice = input("Enter the number you want to choose: ")

    if choice == "1":
        show_order_history(cursor, shopper_id)

    elif choice == "2":
        basket_id = add_item(cursor, db, basket_id, shopper_id)

    elif choice == "3":
        display_basket(cursor, basket_id)

    elif choice == "4":
        change_quantity(cursor, db, basket_id)

    elif choice == "5":
        remove_item(cursor, db, basket_id)

    elif choice == "6":
        basket_id = checkout(cursor, db, basket_id, shopper_id)

    elif choice == "7":
        print("Goodbye")
        break

    else:
        print("Please enter a number from 1 to 7")

# Close the database after the menu ends
db.close()
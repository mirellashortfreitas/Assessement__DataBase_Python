import sqlite3

import db_queries

# Generic function to print an aligned table.

def print_table(headers, rows, aligns):
    widths = []
    for col_index, header in enumerate(headers):
        values_in_column = [str(row[col_index]) for row in rows]
        widths.append(max([len(header)] + [len(v) for v in values_in_column]))

    def format_row(values):
        cells = []
        for value, width, align in zip(values, widths, aligns):
            text = str(value)
            cells.append(text.rjust(width) if align == "r" else text.ljust(width))
        return "  ".join(cells)

    print(format_row(headers))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(format_row(row))

    return widths

# Display a numbered list and return the selected database ID
def display_options(all_options, title, option_type):
    print(f"\n{title}\n")

    for number, option in enumerate(all_options, start=1):
        print(f"{number}.\t{option[1]}")

    while True:
        try:
            selected_number = int(input(
                f"Enter the number {option_type} you want to choose: "
            ))

            if 1 <= selected_number <= len(all_options):
                return all_options[selected_number - 1][0]

        except ValueError:
            pass

        print("Please enter a valid option number")


# Display the current basket as a "Basket Contents" table and return the total
def display_basket(cursor, basket_id):
    basket_items = db_queries.get_basket_items(cursor, basket_id)

    if len(basket_items) == 0:
        print("Your basket is empty")
        return 0

    print("\nBasket Contents")

    table_rows = []
    basket_total = 0

    for item_number, row in enumerate(basket_items, start=1):
        _, _, description, seller_name, quantity, price = row
        item_total = quantity * price
        basket_total = basket_total + item_total

        table_rows.append([
            item_number,
            description,
            seller_name,
            quantity,
            f"£{price:.2f}",
            f"£{item_total:.2f}",
        ])

    widths = print_table(
        ["Basket Item", "Product Description", "Seller Name", "Qty", "Price", "Total"],
        table_rows,
        ["l", "l", "l", "r", "r", "r"],
    )

    print("  ".join("-" * w for w in widths))

    # "Basket Total" spans across the Qty and Price columns.
    
    label_width = widths[3] + 2 + widths[4]
    blank_columns = "  ".join(" " * w for w in widths[0:3])
    print(
        blank_columns + "  " +
        "Basket Total".rjust(label_width) + "  " +
        f"£{basket_total:.2f}".rjust(widths[5])
    )

    return basket_total


# Create a new empty basket for the shopper (no message printed)
def create_basket(cursor, db, shopper_id):
    basket_id = db_queries.get_next_id(cursor, "shopper_baskets", "basket_id")
    db_queries.insert_basket(cursor, basket_id, shopper_id)
    db.commit()
    return basket_id


# Find today's most recent basket or create a new one
def find_or_create_basket(cursor, db, shopper_id):
    basket_id = db_queries.get_todays_basket_id(cursor, shopper_id)

    if basket_id is not None:
        return basket_id

    return create_basket(cursor, db, shopper_id)


# Add a product to the current basket
def add_item(cursor, db, basket_id, shopper_id):
    category_rows = db_queries.get_categories(cursor)
    category_id = display_options(
        category_rows,
        "Product Categories",
        "product category"
    )

    product_rows = db_queries.get_available_products(cursor, category_id)

    if len(product_rows) == 0:
        print("No products are available in this category")
        return basket_id

    product_id = display_options(product_rows, "Products", "product")

    seller_rows = db_queries.get_sellers_for_product(cursor, product_id)
    seller_id = display_options(seller_rows, "Sellers who sell this product", "seller")

    while True:
        try:
            quantity = int(input("Enter the quantity of the selected product you want to buy: "))

            if quantity > 0:
                break

        except ValueError:
            pass

        print("The quantity must be greater than 0. Please enter a positive whole number.")

    price = db_queries.get_price(cursor, product_id, seller_id)

    if basket_id is None:
        basket_id = create_basket(cursor, db, shopper_id)

    try:
        db_queries.insert_basket_item(cursor, basket_id, product_id, seller_id, quantity, price)
        db.commit()
        print("\nItem added to your basket")

    except sqlite3.Error:
        db.rollback()
        print("\nThe item could not be added to your basket")

    return basket_id


# Change the quantity of a basket item
def change_quantity(cursor, db, basket_id):
    basket_items = db_queries.get_basket_items(cursor, basket_id)

    if len(basket_items) == 0:
        print("Your basket is empty")
        return

    display_basket(cursor, basket_id)

    if len(basket_items) == 1:
        selected_item_number = 1
    else:
        while True:
            try:
                selected_item_number = int(input(
                    "\nEnter the basket item no. of the item you want to change: "
                ))
                if 1 <= selected_item_number <= len(basket_items):
                    break
            except ValueError:
                pass
            print("The basket item no. you have entered is invalid")

    selected_item = basket_items[selected_item_number - 1]

    while True:
        try:
            new_quantity = int(input("Enter the new quantity of the selected product you want to buy: "))
            if new_quantity > 0:
                break
        except ValueError:
            pass
        print("The quantity must be greater than 0. Please enter a positive number.")

    # selected_item = (product_id, seller_id, description, seller_name, quantity, price)
    db_queries.update_basket_item_quantity(
        cursor, basket_id, selected_item[0], selected_item[1], new_quantity
    )
    db.commit()

    display_basket(cursor, basket_id)


# Remove an item from the basket
def remove_item(cursor, db, basket_id):
    basket_items = db_queries.get_basket_items(cursor, basket_id)

    if len(basket_items) == 0:
        print("Your basket is empty")
        return

    display_basket(cursor, basket_id)

    if len(basket_items) == 1:
        selected_item_number = 1
    else:
        while True:
            try:
                selected_item_number = int(input(
                    "\nEnter the basket item no. of the item you want to remove: "
                ))
                if 1 <= selected_item_number <= len(basket_items):
                    break
            except ValueError:
                pass
            print("The basket item no. you have entered is invalid")

    selected_item = basket_items[selected_item_number - 1]

    # different wording when removing the last item, since it will empty the basket
    if len(basket_items) == 1:
        confirm_prompt = "Do you definitely want to delete this product and empty your basket (Y/N)? "
    else:
        confirm_prompt = "Do you definitely want to delete this product from your basket (Y/N)? "

    confirmation = input(confirm_prompt).upper()

    if confirmation == "Y":
        db_queries.delete_basket_item(cursor, basket_id, selected_item[0], selected_item[1])
        db.commit()
        print()
        display_basket(cursor, basket_id)


# Display the shopper's order history as a table
def show_order_history(cursor, shopper_id):
    order_rows = db_queries.get_order_history(cursor, shopper_id)

    if len(order_rows) == 0:
        print("No orders placed by this customer")
        return

    print("\nOrder History")

    table_rows = []
    last_order_id = None

    for row in order_rows:
        order_id, order_date, description, seller, price, qty, status = row

        # only show the order id/date on the first line of that order,
        # leave it blank for the other products belonging to the same order
        if order_id == last_order_id:
            order_id_display = ""
            order_date_display = ""
        else:
            order_id_display = order_id
            order_date_display = order_date
            last_order_id = order_id

        table_rows.append([
            order_id_display,
            order_date_display,
            description,
            seller,
            f"£{price:.2f}",
            qty,
            status,
        ])

    print_table(
        ["Order ID", "Order Date", "Product Description", "Seller", "Price", "Qty", "Status"],
        table_rows,
        ["l", "l", "l", "l", "r", "r", "l"],
    )


# Complete the checkout as one database transaction
def checkout(cursor, db, basket_id, shopper_id):
    basket_items = db_queries.get_basket_items(cursor, basket_id)

    if len(basket_items) == 0:
        print("Your basket is empty")
        return basket_id

    display_basket(cursor, basket_id)

    while True:
        confirmation = input(
            "\nDo you wish to proceed with the checkout (Y/N)? "
        ).upper()

        if confirmation in ("Y", "N"):
            break

        print("Please enter Y or N")

    if confirmation == "N":
        return basket_id

    try:
        cursor.execute("BEGIN TRANSACTION")

        order_id = db_queries.get_next_id(cursor, "shopper_orders", "order_id")
        db_queries.insert_order(cursor, order_id, shopper_id)

        for product_id, seller_id, _, _, quantity, price in basket_items:
            db_queries.insert_ordered_product(cursor, order_id, product_id, seller_id, quantity, price)

        db_queries.delete_basket_contents(cursor, basket_id)
        db_queries.delete_basket(cursor, basket_id)

        db.commit()
        print("\nCheckout complete, your order has been placed.")
        return None

    except sqlite3.Error:
        db.rollback()
        print("Checkout failed; all changes have been rolled back")
        return basket_id
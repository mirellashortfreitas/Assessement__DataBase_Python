
# Shoppers

def get_shopper(cursor, shopper_id):
    """Return (first_name, surname) for this shopper_id, or None if not found."""
    query = """
        SELECT shopper_first_name, shopper_surname
        FROM shoppers
        WHERE shopper_id = ?
    """
    cursor.execute(query, (shopper_id,))
    return cursor.fetchone()

# Baskets - function retrieves data and returns it without changing anything in the database

def get_todays_basket_id(cursor, shopper_id):
    """Return the most recent basket_id created today for this shopper, or None."""
    query = """
        SELECT basket_id
        FROM shopper_baskets
        WHERE shopper_id = ?
        AND DATE(basket_created_date_time) = DATE('now')
        ORDER BY basket_created_date_time DESC
        LIMIT 1
    """
    cursor.execute(query, (shopper_id,))
    row = cursor.fetchone()
    return row[0] if row else None


def insert_basket(cursor, basket_id, shopper_id):
    query = """
        INSERT INTO shopper_baskets
            (basket_id, shopper_id, basket_created_date_time)
        VALUES (?, ?, datetime('now'))
    """
    cursor.execute(query, (basket_id, shopper_id))


def get_basket_items(cursor, basket_id):
    """Return every row in the current basket as:
    (product_id, seller_id, product_description, seller_name, quantity, price)
    """
    query = """
        SELECT basket_contents.product_id,
               basket_contents.seller_id,
               products.product_description,
               sellers.seller_name,
               basket_contents.quantity,
               basket_contents.price
        FROM basket_contents
        INNER JOIN products
            ON basket_contents.product_id = products.product_id
        INNER JOIN sellers
            ON basket_contents.seller_id = sellers.seller_id
        WHERE basket_contents.basket_id = ?
        ORDER BY products.product_description
    """
    cursor.execute(query, (basket_id,))
    return cursor.fetchall()


def insert_basket_item(cursor, basket_id, product_id, seller_id, quantity, price):
    query = """
        INSERT INTO basket_contents
            (basket_id, product_id, seller_id, quantity, price)
        VALUES (?, ?, ?, ?, ?)
    """
    cursor.execute(query, (basket_id, product_id, seller_id, quantity, price))


def update_basket_item_quantity(cursor, basket_id, product_id, seller_id, quantity):
    query = """
        UPDATE basket_contents
        SET quantity = ?
        WHERE basket_id = ?
        AND product_id = ?
        AND seller_id = ?
    """
    cursor.execute(query, (quantity, basket_id, product_id, seller_id))


def delete_basket_item(cursor, basket_id, product_id, seller_id):
    query = """
        DELETE FROM basket_contents
        WHERE basket_id = ?
        AND product_id = ?
        AND seller_id = ?
    """
    cursor.execute(query, (basket_id, product_id, seller_id))


def delete_basket_contents(cursor, basket_id):
    cursor.execute(
        "DELETE FROM basket_contents WHERE basket_id = ?", (basket_id,)
    )


def delete_basket(cursor, basket_id):
    cursor.execute(
        "DELETE FROM shopper_baskets WHERE basket_id = ?", (basket_id,)
    )

# Categories, products and sellers (used when adding an item)

def get_categories(cursor):
    query = """
        SELECT category_id, category_description
        FROM categories
        ORDER BY category_description
    """
    cursor.execute(query)
    return cursor.fetchall()


def get_available_products(cursor, category_id):
    query = """
        SELECT product_id, product_description
        FROM products
        WHERE category_id = ?
        AND product_status = 'Available'
        ORDER BY product_description
    """
    cursor.execute(query, (category_id,))
    return cursor.fetchall()


def get_sellers_for_product(cursor, product_id):
    """Return (seller_id, 'Seller Name  £price') for every seller of this product."""
    query = """
        SELECT sellers.seller_id,
               sellers.seller_name || '  £' ||
               printf('%.2f', product_sellers.price)
        FROM product_sellers
        INNER JOIN sellers
            ON product_sellers.seller_id = sellers.seller_id
        WHERE product_sellers.product_id = ?
        ORDER BY sellers.seller_name
    """
    cursor.execute(query, (product_id,))
    return cursor.fetchall()

def get_price(cursor, product_id, seller_id):
    query = """
        SELECT price
        FROM product_sellers
        WHERE product_id = ?
        AND seller_id = ?
    """
    cursor.execute(query, (product_id, seller_id))
    return cursor.fetchone()[0]

# Orders

def get_order_history(cursor, shopper_id):
    query = """
        SELECT shopper_orders.order_id,
               shopper_orders.order_date,
               products.product_description,
               sellers.seller_name,
               ordered_products.price,
               ordered_products.quantity,
               ordered_products.ordered_product_status
        FROM shopper_orders
        INNER JOIN ordered_products
            ON shopper_orders.order_id = ordered_products.order_id
        INNER JOIN products
            ON ordered_products.product_id = products.product_id
        INNER JOIN sellers
            ON ordered_products.seller_id = sellers.seller_id
        WHERE shopper_orders.shopper_id = ?
        ORDER BY shopper_orders.order_date DESC, shopper_orders.order_id DESC
    """
    cursor.execute(query, (shopper_id,))
    return cursor.fetchall()

def insert_order(cursor, order_id, shopper_id):
    query = """
        INSERT INTO shopper_orders
            (order_id, shopper_id, order_date, order_status)
        VALUES (?, ?, DATE('now'), 'Placed')
    """
    cursor.execute(query, (order_id, shopper_id))

def insert_ordered_product(cursor, order_id, product_id, seller_id, quantity, price):
    query = """
        INSERT INTO ordered_products
            (order_id, product_id, seller_id,
             quantity, price, ordered_product_status)
        VALUES (?, ?, ?, ?, ?, 'Placed')
    """
    cursor.execute(query, (order_id, product_id, seller_id, quantity, price))

# Generic helper used whenever we need to work out the next id ourselves

def get_next_id(cursor, table_name, column_name):
    sequence_query = """
        SELECT seq + 1
        FROM sqlite_sequence
        WHERE name = ?
    """
    cursor.execute(sequence_query, (table_name,))
    sequence_row = cursor.fetchone()

    if sequence_row is not None:
        return sequence_row[0]

    cursor.execute(
        f"SELECT COALESCE(MAX({column_name}), 0) + 1 FROM {table_name}"
    )
    return cursor.fetchone()[0]
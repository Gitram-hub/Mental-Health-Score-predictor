from app.services.db_connection import get_db_connection


def get_dataset_summary():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM customers")
    customer_count = cur.fetchone()[0]
    cur.execute("SELECT name, signup_date FROM customers ORDER BY signup_date DESC LIMIT 3")
    customer_sample = [{"name": r[0], "signup_date": str(r[1])} for r in cur.fetchall()]

    cur.execute("SELECT COUNT(*) FROM products")
    product_count = cur.fetchone()[0]
    cur.execute("SELECT DISTINCT category FROM products")
    categories = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT name, category, price FROM products ORDER BY price DESC LIMIT 3")
    product_sample = [{"name": r[0], "category": r[1], "price": str(r[2])} for r in cur.fetchall()]

    cur.execute("SELECT order_status, COUNT(*) FROM orders GROUP BY order_status")
    status_counts = {row[0]: row[1] for row in cur.fetchall()}

    cur.execute("SELECT COUNT(*) FROM payments")
    payment_count = cur.fetchone()[0]
    cur.execute("SELECT DISTINCT payment_method FROM payments")
    payment_methods = [r[0] for r in cur.fetchall()]

    cur.close()
    conn.close()

    return {
        "customers": {"count": customer_count, "sample": customer_sample},
        "products": {"count": product_count, "categories": categories, "sample": product_sample},
        "orders": {"count": sum(status_counts.values()), "by_status": status_counts},
        "payments": {"count": payment_count, "methods": payment_methods},
    }
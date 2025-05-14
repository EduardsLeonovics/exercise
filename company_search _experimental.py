import psycopg2
import pandas as pd
import tkinter as tk
from tkinter import messagebox, ttk
from typing import List, Dict, Optional, Tuple
from datetime import datetime

def search_companies(
    financial_filters: Optional[Dict[str, Tuple[str, float]]] = None,
    tag_filters: Optional[List[str]] = None,
    order_by: Optional[str] = "company_id",
    order_direction: str = "ASC",
    limit: Optional[int] = None
) -> List[Dict]:

    db_params = {
        "dbname": "Sehner",
        "user": "postgres",
        "password": "1023",
        "host": "localhost",
        "port": "8888"
    }

    # Valid columns for ordering and financial metrics
    valid_columns = {
        "company_id", "company_name", "earnings", "earnings_avg", "balance", "balance_avg"
    }
    valid_operators = {">", "<", ">=", "<=", "="}

    # Validate inputs. Breaks the program if incorrect inputs are provided
    if financial_filters:
        for metric, (op, _) in financial_filters.items():
            if metric not in valid_columns - {"company_id", "company_name"}:
                raise ValueError(f"Invalid financial metric: {metric}")
            if op not in valid_operators:
                raise ValueError(f"Invalid operator: {op}")
    if order_by not in valid_columns:
        raise ValueError(f"Invalid order_by column: {order_by}")
    if order_direction not in {"ASC", "DESC"}:
        raise ValueError(f"Invalid order_direction: {order_direction}")
    if limit is not None and (not isinstance(limit, int) or limit <= 0):
        raise ValueError("Limit must be a positive integer")

    select_clause = """
        SELECT 
            c.id AS company_id,
            c.name AS company_name,
            COALESCE(ARRAY_AGG(t.name) FILTER (WHERE t.name IS NOT NULL), ARRAY[]::VARCHAR[]) AS tag_names,
            cf.earnings,
            cf.earnings_avg,
            cf.balance,
            cf.balance_avg
    """
    from_clause = """
        FROM companies c
        LEFT JOIN company_financials cf ON c.id = cf.company_id
        LEFT JOIN tag_values ct ON c.id = ct.company_id
        LEFT JOIN tags t ON ct.tag_id = t.id
    """
    where_clauses = []
    params = []

    # clauses and filters
    if financial_filters:
        for metric, (op, value) in financial_filters.items():
            where_clauses.append(f"cf.{metric} {op} %s")
            params.append(value)

    if tag_filters:
        where_clauses.append("t.name = ANY(%s)")
        params.append(tag_filters)

    where_clause = ""
    if where_clauses:
        where_clause = "WHERE " + " AND ".join(where_clauses)

    group_by_clause = """
        GROUP BY c.id, c.name, cf.earnings, cf.earnings_avg, cf.balance, cf.balance_avg
    """

    order_by_clause = f"""
        ORDER BY {order_by} {order_direction} NULLS LAST
    """

    limit_clause = f"LIMIT %s" if limit is not None else ""
    if limit:
        params.append(limit)

    query = f"""
        {select_clause}
        {from_clause}
        {where_clause}
        {group_by_clause}
        {order_by_clause}
        {limit_clause}
    """.strip()

    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        cur.execute(query, params)
        results = cur.fetchall()

        # Format results as list of dictionaries. Not the best approach for big datasets
        companies = [
            {
                "company_id": row[0],
                "company_name": row[1],
                "tag_names": ", ".join(row[2]) if row[2] else "",  # Join tags for Excel
                "earnings": row[3],
                "earnings_avg": row[4],
                "balance": row[5],
                "balance_avg": row[6]
            }
            for row in results
        ]

        return companies

    except Exception as e:
        raise Exception(f"Database error: {e}")

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def save_to_excel(companies: List[Dict], filename: str = "company_search_results.xlsx") -> None:

    if not companies:
        messagebox.showwarning("No Results", "No companies found matching the criteria.")
        return

    df = pd.DataFrame(companies)

    # Save as Excel
    try:
        df.to_excel(filename, index=False, engine="openpyxl")
        messagebox.showinfo("Success", f"Results saved to {filename}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save Excel file: {e}")

class CompanySearchGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Company Search")
        self.root.geometry("600x600")

        # Filters
        tk.Label(root, text="Financial Filters", font=("Arial", 12, "bold")).pack(pady=5)
        self.financial_frame = tk.Frame(root)
        self.financial_frame.pack(pady=5, fill=tk.X, padx=10)
        self.financial_entries = []
        self.add_financial_filter()

        tk.Button(root, text="Add Financial Filter", command=self.add_financial_filter).pack(pady=5)

        # Tag Filters
        tk.Label(root, text="Tag Filters (comma-separated, e.g., Healthcare,Pharmaceuticals)", font=("Arial", 12, "bold")).pack(pady=5)
        self.tag_entry = tk.Entry(root, width=50)
        self.tag_entry.pack(pady=5, padx=10)

        # Order By
        tk.Label(root, text="Order By", font=("Arial", 12, "bold")).pack(pady=5)
        self.order_by_var = tk.StringVar(value="company_id")
        order_by_options = ["company_id", "company_name", "earnings", "earnings_avg", "balance", "balance_avg"]
        ttk.Combobox(root, textvariable=self.order_by_var, values=order_by_options, state="readonly").pack(pady=5)

        # Order Direction
        tk.Label(root, text="Order Direction", font=("Arial", 12, "bold")).pack(pady=5)
        self.order_direction_var = tk.StringVar(value="ASC")
        ttk.Combobox(root, textvariable=self.order_direction_var, values=["ASC", "DESC"], state="readonly").pack(pady=5)

        # Limit
        tk.Label(root, text="Limit (number of results, leave blank for no limit)", font=("Arial", 12, "bold")).pack(pady=5)
        self.limit_entry = tk.Entry(root, width=10)
        self.limit_entry.pack(pady=5)

        # Search Button
        tk.Button(root, text="Search and Save to Excel", command=self.run_search, bg="green", fg="white", font=("Arial", 12)).pack(pady=20)


    def add_financial_filter(self):
        """Add a new row for financial filter input."""
        frame = tk.Frame(self.financial_frame)
        frame.pack(fill=tk.X, pady=2)

        # Metric
        metric_var = tk.StringVar(value="earnings")
        ttk.Combobox(frame, textvariable=metric_var, values=["earnings", "earnings_avg", "balance", "balance_avg"], state="readonly", width=15).pack(side=tk.LEFT, padx=5)

        # Operator
        op_var = tk.StringVar(value=">")
        ttk.Combobox(frame, textvariable=op_var, values=[">", "<", ">=", "<=", "="], state="readonly", width=5).pack(side=tk.LEFT, padx=5)

        # Value
        value_entry = tk.Entry(frame, width=20)
        value_entry.pack(side=tk.LEFT, padx=5)

        # Remove Button
        tk.Button(frame, text="Remove", command=lambda: self.remove_financial_filter(frame), fg="red").pack(side=tk.LEFT, padx=5)

        self.financial_entries.append((frame, metric_var, op_var, value_entry))

    def remove_financial_filter(self, frame: tk.Frame):
        """Remove a financial filter row."""
        frame.destroy()
        self.financial_entries = [(f, m, o, v) for f, m, o, v in self.financial_entries if f != frame]

    def run_search(self):
        """Collect inputs, run search, and save results to Excel."""
        try:
            # Financial Filters
            financial_filters = {}
            for _, metric_var, op_var, value_entry in self.financial_entries:
                metric = metric_var.get()
                op = op_var.get()
                value_str = value_entry.get().strip()
                if value_str:
                    try:
                        value = float(value_str)
                        financial_filters[metric] = (op, value)
                    except ValueError:
                        messagebox.showerror("Error", f"Invalid value for {metric}: {value_str} must be a number")
                        return

            # Tag Filters
            tag_filters = [t.strip() for t in self.tag_entry.get().split(",") if t.strip()]
            if not tag_filters:
                tag_filters = None

            # Order By
            order_by = self.order_by_var.get()

            # Order Direction
            order_direction = self.order_direction_var.get()

            # Limit
            limit_str = self.limit_entry.get().strip()
            limit = None
            if limit_str:
                try:
                    limit = int(limit_str)
                    if limit <= 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("Error", "Limit must be a positive integer")
                    return

            # Run search
            results = search_companies(
                financial_filters=financial_filters if financial_filters else None,
                tag_filters=tag_filters,
                order_by=order_by,
                order_direction=order_direction,
                limit=limit
            )

            # Save to Excel
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"company_search_results_{timestamp}.xlsx"
            save_to_excel(results, filename)

        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = CompanySearchGUI(root)
    root.mainloop()
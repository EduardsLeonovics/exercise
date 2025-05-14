import json
import psycopg2
from datetime import datetime

db_params = {
    "dbname": "Sehner",
    "user": "postgres",
    "password": "1023",
    "host": "localhost",
    "port": "8888"
}

# Path to the JSONL file
jsonl_file = r"sehner-code-test-eduards\financials.jsonl"

def calculate_metrics(financials):
    # Sort financials by date to get the most recent first
    financials_sorted = sorted(financials, key=lambda x: x["date"], reverse=True)
    
    earnings = None
    balance = None
    earnings_list = []
    balance_list = []
    
    for report in financials_sorted:
        report_date = datetime.strptime(report["date"], "%Y-%m-%d")
        year = report_date.year
        
        for item in report["items"]:
            if item["id"] == "Earnings": # Get the most recent earnings
                if earnings is None: 
                    earnings = item["value"]
                if year >= 2018:
                    earnings_list.append(item["value"])
            elif item["id"] == "BalanceTotal":
                if balance is None:
                    balance = item["value"]
                if year >= 2018:
                    balance_list.append(item["value"])
    
    # Calculate averages (handle cases with no data from 2018+)
    earnings_avg = sum(earnings_list) / len(earnings_list) if earnings_list else None
    balance_avg = sum(balance_list) / len(balance_list) if balance_list else None
    
    return earnings, earnings_avg, balance, balance_avg

try:
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()
    
    with open(jsonl_file, "r") as file:
        for line in file:
            try:
                data = json.loads(line.strip())
                company_id = data["company_id"]
                financials = data["financials"]
                
                # Calculating metrics
                earnings, earnings_avg, balance, balance_avg = calculate_metrics(financials)
                
                # Inserting data into company_financials table
                cur.execute(
                    """
                    INSERT INTO company_financials (company_id, earnings, earnings_avg, balance, balance_avg)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (company_id) DO UPDATE
                    SET earnings = EXCLUDED.earnings,
                        earnings_avg = EXCLUDED.earnings_avg,
                        balance = EXCLUDED.balance,
                        balance_avg = EXCLUDED.balance_avg;
                    """,
                    (company_id, earnings, earnings_avg, balance, balance_avg)
                )
                
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON line: {e}")
                continue
    
    conn.commit()
    print("Data imported successfully.")
    
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
    
finally:
    if cur:
        cur.close()
    if conn:
        conn.close()
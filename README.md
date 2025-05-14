# Data definition
We have prepared a small dataset of simplified real-world data.

`dump.sql` is a PostgreSQL database dump containing the following information:
- **Companies**: Base company data.
- **Tags**: User-created labels to manage lists of companies.
- **Tag values**: Assignments of tags to companies. A company can have multiple tags, and a tag can be associated with multiple companies.

`financials.jsonl` contains company financial information in the JSON Lines format. 
Each company can have several financial reports from different years, and each financial report can contain values for various financial metrics.

# Assignment
Your objective is to develop backend functionality that allows users to find companies of interest.

## Step 1: Financial data
Company financial data is crucial for users, but it is not yet available in the database. We have found an external data source that provides financial data. This data is available in `financials.jsonl` file.

Your task is to import this financial data into the database to enable users to use it for company search. Users have specified several financial metrics of interest that should be retrieved for each company:
- `earnings`: the most recent `Earnings` value, from the latest report that includes this metric.
- `earnings_avg`: the average `Earnings`  calculated from reports beginning in the year 2018, to avoid using outdated data.
- `balance`: the most recent `BalanceTotal` value from the latest report that includes this metric.
- `balance_avg`: the average `BalanceTotal`, computed in the same manner as `earnings_avg`

An empty table named `company_financials` has been set up in the database for you to populate with the extracted financial data.


## Step 2: Company search
Design a Python function for company search that enables the user to:
- Filter for financial metrics and tags, with the capability to handle multiple filters simultaneously
- Order the results by id, company name, or financials in either ascending or descending order.
- Restrict the number of records returned in the result set.

The function must return a list of companies, each entry consisting of the company id, company name, tag names, and all available financial metrics.

For instance, a user might request to find the top 10 companies with the highest earnings that have an average balance greater than 1M and are associated with `Healthcare` or `Pharmaceuticals` tags.


## Bonus tasks (optional)
Explore potential advancements such as:
- Implement a parser for deriving search parameters from a text string.
- Create a basic user interface that integrates the company search functionality.
- Perform an analysis on the financial data for more in-depth understanding.


# Extra details
- It is highly recommended to use PostgreSQL and Python for implementation.
- The main criteria for evaluation are:
  - Code simplicity
  - Code organization
  - Code style and neatness
  - Production readiness
- Comments with your assumptions and possible improvements to your code are welcome.
- The assignment is designed for ~4 hours, feel free to submit partial work if it takes longer.


# Database setup
To set up the database, use the following command to start a Docker container with PostgreSQL:
```bash
docker run -ti --rm -p 15432:5432 --name sehner-db \
    -e POSTGRES_USER=sehner -e POSTGRES_PASSWORD=sehner \
    -v $PWD/dump.sql:/docker-entrypoint-initdb.d/dump.sql \
    postgres:16
```
It will set up the database with `dump.sql` and make it accessible on local port 15432.
Note that changes within the Docker container are not persistent; stopping the container will remove all data, and restarting it will reset the database.
Alternatively, you can import `dump.sql` into your existing PostgreSQL setup.

To confirm the database is set up correctly, use the following command if you have the psql client installed locally:
```bash
PGPASSWORD=sehner psql -h localhost -p 15432 -U sehner -c 'select * from companies limit 10;'
```

To execute this from the started Docker container (without local psql client), use:
```bash
docker exec -e PGPASSWORD=sehner -it sehner-db psql -U sehner -c 'select * from companies limit 10;'
```

For Python connectivity, use this connection string:
```
postgresql://sehner:sehner@localhost:15432/sehner
```

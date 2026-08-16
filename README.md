# Pet&Market Analytics

## About the project

&emsp;A portfolio project about analytics for an online marketplace of pet goods and services, working in Ukraine and Poland. People register, fill in a pet profile, post listings and book each other's listings. The platform takes no cut of the deal — it earns on paid promotion and a $2.50 booking fee.

&emsp;The project answers what a product analyst is really asked here. How much of the product the tracking covers, and which funnel can be trusted. Where the path from a listing to a deal loses people. How much of the catalog is dead or duplicated. Whether the two markets differ after the expansion, and how much of the revenue is real money rather than fees on bookings that get cancelled.

&emsp;The data is generated, but the problems in it are put there on purpose: a clickstream that stops where the money starts, a duplicate cluster spread over many sellers, a quarter of the catalog inactive, and over half of all bookings cancelled. The point is to find them and to say honestly which numbers mean nothing — section 7 of the report is about that.

## Dataset

&emsp;1 500 users and 3 000 listings over two months from January 2026, generated with a fixed seed, so every run reproduces the numbers in the report.

&emsp;The marketplace part is standard: users, pet profiles, listings with a price and a view counter, paid promotions, bookings and closed deals. The interesting part is the logs. The clickstream keeps three event types and all three are onboarding, so the whole money side of the product is unrecorded. The moderation log covers a tenth of the catalog. The gap between the logs and the deal tables is what the first and the last sections of the report are about.

&emsp;In PostgreSQL this is 11 tables: `cities` and `categories` as reference data, `users`, `user_profiles`, `partner_discounts` for people, `listings`, `listing_promotions`, `view_bookings`, `deals` for the marketplace, and `clickstream_events` with `listing_moderation_logs` as the logs.

## Tools

- Python — data generation and analysis: pandas, NumPy, Matplotlib, Seaborn.
- PostgreSQL and SQLAlchemy — schema with foreign keys, batch load of all 11 tables.
- Statistics — a z-test for two proportions between markets, a bootstrap over 10 000 iterations for GMV per user.

## Files in this repository

&emsp;**`data_gen.py`** builds the dataset in pandas. The shares in it are the assumptions of the model: a quarter of the listings inactive, 400 of 3 000 promoted, 30 % of active listings booked, 65 % of confirmed bookings closed as a deal, every twentieth listing repeating the same title.

&emsp;**`db_load.py`** describes the same 11 tables as SQLAlchemy models, creates them in PostgreSQL and loads the dataframes in batches.

&emsp;**`main.py`** is the analysis. It builds the end-to-end listing → booking → deal table, computes both funnels, cuts them by pet type, promotion and category, compares UA against PL with a z-test and a bootstrap, and counts revenue and take rate. The last block is a set of data quality checks that ends up disproving the data itself.

&emsp;**`report.md`** and **`report_eng.md`** are the report in Ukrainian and English, written for a reader who will not open the code. Charts are in **`report_img/`**.

## Requirements

&emsp;Python 3.13, PostgreSQL 14+.

```bash
pip install pandas numpy matplotlib seaborn sqlalchemy psycopg2-binary python-dotenv
```

&emsp;The connection is read from a `.env` file in the project root, which is not in the repository:

```
DBCON=your_password@localhost:5432
```

&emsp;The user is `postgres` and the database is `marketplace_db`, so it has to exist before the load: `createdb -U postgres marketplace_db`.

## How to run

&emsp;The analysis needs no database — `main.py` imports the dataframes from `data_gen.py` and regenerates the same data in memory:

```bash
python main.py
```

&emsp;It prints both funnels, the segments, the tests and the quality checks, and opens three charts in turn, waiting for each window to be closed.

&emsp;To get the data into PostgreSQL for the SQL part:

```bash
python db_load.py
```

&emsp;It appends rows, so a second run on the same database duplicates the data — recreate it before loading again.

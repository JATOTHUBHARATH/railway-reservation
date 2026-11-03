# Railway Reservation System

A railway ticket booking system built with **only Python and SQL**.
The web pages are made by [Streamlit](https://streamlit.io), so no HTML, CSS or JavaScript is written by hand.

## Features

- **Trains:** view, search, add, update fare, delete
- **Passengers:** view, search, add, update phone, delete (10-digit phone check)
- **Book a ticket:** choose passenger, train, date and seats, with a live fare preview
- **Bookings:** list with passenger and train names (JOIN), cancel a booking and return its seats
- **Report:** bookings and revenue per train (`COUNT`, `SUM`, `GROUP BY`) with a bar chart

## Technologies

| Part | Used |
| --- | --- |
| Language | Python 3 |
| Database | MySQL |
| Database driver | `mysql-connector-python` |
| Website | Streamlit |

## Database

Three tables in the database `railway_db`:

- `trains` (primary key `train_id`)
- `passengers` (primary key `passenger_id`)
- `bookings` (primary key `booking_id`, foreign keys to `trains` and `passengers`)

## Project files

| File | Purpose |
| --- | --- |
| `railway_app.py` | The whole application (database code and all pages) |
| `schema_railway.sql` | Creates the database, the tables and sample data |
| `requirements.txt` | Python packages to install |
| `.env.example` | Template for the database settings |

## How to run

1. Install Python 3 and MySQL.
2. Create the database: run `schema_railway.sql` in MySQL (Workbench or command line).
3. Copy `.env.example` to a new file named `.env` and put your MySQL password in it:
   ```
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your_mysql_password
   DB_NAME=railway_db
   ```
4. Install the packages:
   ```
   pip install -r requirements.txt
   ```
5. Start the website:
   ```
   streamlit run railway_app.py
   ```
6. Open http://localhost:8501 if the browser does not open by itself.

## Key ideas used

- **Primary and foreign keys** keep the data linked: a booking must belong to a real train and passenger.
- **Parameterized queries** (`%s`) prevent SQL injection.
- **Transactions** (`commit` / `rollback`): booking and cancelling change two tables together, so both changes save or neither does.
- **`SELECT ... FOR UPDATE`** locks the train row while booking, so the last seat cannot be sold twice.
- **JOIN** shows names instead of ids in the bookings list.
- **`GROUP BY`** with `COUNT` and `SUM` builds the revenue report.
- **Validation** checks phone numbers, seats, fares and travel dates before saving.

## Author

Your name here

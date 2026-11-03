"""
Railway Reservation System - website made with only Python + SQL.

Streamlit turns this Python file into a web page, so no HTML, CSS or
JavaScript is written by hand. Run it with:   streamlit run railway_app.py

Layout of this file:
  1. Database helpers   (connect, fetch rows, change rows)
  2. Trains page
  3. Passengers page
  4. Book page
  5. Bookings page      (list + cancel)
  6. Report page        (COUNT, SUM, GROUP BY)
  7. Sidebar menu       (chooses which page to show)
"""

import os
from datetime import date, timedelta
from decimal import Decimal

import mysql.connector
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()   # reads DB_PASSWORD etc. from the .env file

st.set_page_config(page_title="Railway Reservation", page_icon="🚆", layout="wide")


# ---------------------------------------------------------------------------
# 1. DATABASE HELPERS
# ---------------------------------------------------------------------------

def get_db():
    """Open a new MySQL connection (we open one per action and close it after)."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "NewPass123"),
        database=os.getenv("DB_NAME", "railway_db"),
    )


def clean(row):
    """Turn MySQL types into normal Python types so tables show them nicely."""
    out = {}
    for key, value in row.items():
        if isinstance(value, Decimal):
            out[key] = float(value)                       # fare: 650.00 -> 650.0
        elif isinstance(value, timedelta):                # TIME columns come as timedelta
            secs = int(value.total_seconds())
            out[key] = f"{secs // 3600:02d}:{(secs % 3600) // 60:02d}"
        else:
            out[key] = value
    return out


def fetch(sql, params=()):
    """Run a SELECT and return the rows as a list of dictionaries."""
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)          # %s placeholders block SQL injection
        return [clean(r) for r in cur.fetchall()]
    finally:
        conn.close()


def change(sql, params=()):
    """Run an INSERT / UPDATE / DELETE, save it, and return rows affected."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.rowcount
    except mysql.connector.Error:
        conn.rollback()                   # undo if something went wrong
        raise
    finally:
        conn.close()


def flash(kind, message):
    """Remember a message so it still shows after the page reloads."""
    st.session_state["flash"] = (kind, message)


def show_flash():
    """Show (and then forget) the remembered message."""
    if "flash" in st.session_state:
        kind, message = st.session_state.pop("flash")
        (st.success if kind == "success" else st.error)(message)


# ---------------------------------------------------------------------------
# 2. TRAINS PAGE
# ---------------------------------------------------------------------------

def trains_page():
    st.title("🚆 Trains")
    show_flash()

    # Search (same query as search_train() in the console version)
    word = st.text_input("Search by train name, source or destination")
    if word.strip():
        like = f"%{word.strip()}%"
        trains = fetch("SELECT * FROM trains WHERE train_name LIKE %s OR source LIKE %s "
                       "OR destination LIKE %s ORDER BY train_id", (like, like, like))
    else:
        trains = fetch("SELECT * FROM trains ORDER BY train_id")

    if trains:
        df = pd.DataFrame(trains).rename(columns={
            "train_id": "ID", "train_name": "Name", "source": "From",
            "destination": "To", "departure_time": "Departs",
            "total_seats": "Total seats", "available_seats": "Seats left",
            "fare": "Fare (Rs)"})
        st.dataframe(df, hide_index=True)
    else:
        st.info("No train found")

    add_tab, fare_tab, delete_tab = st.tabs(["➕ Add train", "✏️ Update fare", "🗑️ Delete train"])

    # ---- Add train
    with add_tab:
        with st.form("add_train", clear_on_submit=True):
            c1, c2 = st.columns(2)
            tid = c1.number_input("Train ID", min_value=1, step=1)
            name = c2.text_input("Train name")
            source = c1.text_input("Source")
            dest = c2.text_input("Destination")
            dep = c1.time_input("Departure time")
            seats = c2.number_input("Total seats", min_value=1, step=1)
            fare = c1.number_input("Fare per seat (Rs)", min_value=1.0, step=10.0)
            if st.form_submit_button("Save train", type="primary"):
                if not name.strip() or not source.strip() or not dest.strip():
                    st.error("Name, source and destination are required")
                else:
                    try:
                        change("INSERT INTO trains VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                               (int(tid), name.strip(), source.strip(), dest.strip(),
                                dep.strftime("%H:%M:%S"), int(seats), int(seats), fare))
                        flash("success", "Train added")
                        st.rerun()
                    except mysql.connector.Error as e:
                        st.error(f"Database error: {e}")

    # ---- Update fare
    with fare_tab:
        if trains:
            with st.form("update_fare"):
                chosen = st.selectbox("Train", trains,
                                      format_func=lambda t: f"{t['train_id']} - {t['train_name']}")
                new_fare = st.number_input("New fare (Rs)", min_value=1.0, step=10.0)
                if st.form_submit_button("Update fare"):
                    try:
                        done = change("UPDATE trains SET fare=%s WHERE train_id=%s",
                                      (new_fare, chosen["train_id"]))
                        flash("success" if done else "error",
                              "Fare updated" if done else "Fare unchanged")
                        st.rerun()
                    except mysql.connector.Error as e:
                        st.error(f"Database error: {e}")

    # ---- Delete train
    with delete_tab:
        if trains:
            with st.form("delete_train"):
                chosen = st.selectbox("Train to delete", trains,
                                      format_func=lambda t: f"{t['train_id']} - {t['train_name']}")
                if st.form_submit_button("Delete train"):
                    try:
                        change("DELETE FROM trains WHERE train_id=%s", (chosen["train_id"],))
                        flash("success", "Train deleted")
                    except mysql.connector.Error:
                        # the foreign key in bookings stops this
                        flash("error", "Cannot delete: this train has bookings")
                    st.rerun()


# ---------------------------------------------------------------------------
# 3. PASSENGERS PAGE
# ---------------------------------------------------------------------------

def phone_ok(phone):
    """Phone must be exactly 10 digits."""
    return len(phone) == 10 and phone.isdigit()


def passengers_page():
    st.title("👤 Passengers")
    show_flash()

    word = st.text_input("Search by name")
    if word.strip():
        people = fetch("SELECT * FROM passengers WHERE passenger_name LIKE %s "
                       "ORDER BY passenger_id", (f"%{word.strip()}%",))
    else:
        people = fetch("SELECT * FROM passengers ORDER BY passenger_id")

    if people:
        df = pd.DataFrame(people).rename(columns={
            "passenger_id": "ID", "passenger_name": "Name", "age": "Age",
            "gender": "Gender", "phone": "Phone"})
        st.dataframe(df, hide_index=True)
    else:
        st.info("No passenger found")

    add_tab, phone_tab, delete_tab = st.tabs(["➕ Add passenger", "📞 Update phone", "🗑️ Delete passenger"])

    # ---- Add passenger
    with add_tab:
        with st.form("add_passenger", clear_on_submit=True):
            c1, c2 = st.columns(2)
            pid = c1.number_input("Passenger ID", min_value=1, step=1)
            name = c2.text_input("Name")
            age = c1.number_input("Age", min_value=1, step=1)
            gender = c2.selectbox("Gender", ["male", "female", "others"])
            phone = c1.text_input("Phone (10 digits)", max_chars=10)
            if st.form_submit_button("Save passenger", type="primary"):
                if not name.strip():
                    st.error("Name is required")
                elif not phone_ok(phone):
                    st.error("Phone must be exactly 10 digits")
                else:
                    try:
                        change("INSERT INTO passengers VALUES (%s,%s,%s,%s,%s)",
                               (int(pid), name.strip(), int(age), gender, phone))
                        flash("success", "Passenger added")
                        st.rerun()
                    except mysql.connector.Error as e:
                        st.error(f"Database error: {e}")

    # ---- Update phone
    with phone_tab:
        if people:
            with st.form("update_phone"):
                chosen = st.selectbox("Passenger", people,
                                      format_func=lambda p: f"{p['passenger_id']} - {p['passenger_name']}")
                phone = st.text_input("New phone (10 digits)", max_chars=10)
                if st.form_submit_button("Update phone"):
                    if not phone_ok(phone):
                        st.error("Phone must be exactly 10 digits")
                    else:
                        try:
                            done = change("UPDATE passengers SET phone=%s WHERE passenger_id=%s",
                                          (phone, chosen["passenger_id"]))
                            flash("success" if done else "error",
                                  "Phone updated" if done else "Phone unchanged")
                            st.rerun()
                        except mysql.connector.Error as e:
                            st.error(f"Database error: {e}")

    # ---- Delete passenger
    with delete_tab:
        if people:
            with st.form("delete_passenger"):
                chosen = st.selectbox("Passenger to delete", people,
                                      format_func=lambda p: f"{p['passenger_id']} - {p['passenger_name']}")
                if st.form_submit_button("Delete passenger"):
                    try:
                        change("DELETE FROM passengers WHERE passenger_id=%s",
                               (chosen["passenger_id"],))
                        flash("success", "Passenger deleted")
                    except mysql.connector.Error:
                        flash("error", "Cannot delete: this passenger has bookings")
                    st.rerun()


# ---------------------------------------------------------------------------
# 4. BOOK PAGE
# ---------------------------------------------------------------------------

def book_ticket(pid, tid, travel, seats):
    """
    Book seats. Returns (ok, message).
    Two changes must happen together (a transaction):
      1. INSERT the booking   2. reduce the train's available seats
    commit() saves both, rollback() undoes both.
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        # FOR UPDATE locks this train row, so two people cannot take the last seat together
        cur.execute("SELECT fare, available_seats FROM trains WHERE train_id=%s FOR UPDATE", (tid,))
        train = cur.fetchone()
        if train is None:
            conn.rollback()
            return False, "Train not found"
        fare, available = train
        if seats > available:
            conn.rollback()
            return False, f"Only {available} seats available"

        total = fare * seats
        cur.execute("INSERT INTO bookings (passenger_id, train_id, travel_date, "
                    "seats_booked, total_fare) VALUES (%s,%s,%s,%s,%s)",
                    (pid, tid, travel, seats, total))
        cur.execute("UPDATE trains SET available_seats = available_seats - %s "
                    "WHERE train_id=%s", (seats, tid))
        conn.commit()                                   # both changes saved together
        return True, f"Booking confirmed. Total fare: Rs {float(total):.2f}"
    except mysql.connector.Error as e:
        conn.rollback()                                 # undo both if something fails
        return False, f"Database error: {e}"
    finally:
        conn.close()


def book_page():
    st.title("🎫 Book a Ticket")
    show_flash()

    people = fetch("SELECT passenger_id, passenger_name FROM passengers ORDER BY passenger_id")
    trains = fetch("SELECT * FROM trains ORDER BY train_id")
    if not people or not trains:
        st.info("Add at least one passenger and one train first.")
        return

    passenger = st.selectbox("Passenger", people,
                             format_func=lambda p: f"{p['passenger_id']} - {p['passenger_name']}")
    train = st.selectbox("Train", trains, format_func=lambda t: (
        f"{t['train_name']} ({t['source']} to {t['destination']}) - {t['available_seats']} seats left"))
    travel = st.date_input("Travel date", min_value=date.today())    # blocks past dates
    seats = st.number_input("Number of seats", min_value=1, step=1)

    # Live fare preview (the real total is calculated again inside book_ticket)
    st.info(f"{int(seats)} x Rs {train['fare']:.2f} = Rs {train['fare'] * int(seats):.2f}")

    if st.button("Confirm booking", type="primary"):
        ok, message = book_ticket(passenger["passenger_id"], train["train_id"],
                                  travel, int(seats))
        flash("success" if ok else "error", message)
        st.rerun()


# ---------------------------------------------------------------------------
# 5. BOOKINGS PAGE
# ---------------------------------------------------------------------------

def cancel_booking(bid):
    """Mark the booking cancelled and give the seats back to the train (one transaction)."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT train_id, seats_booked, status FROM bookings "
                    "WHERE booking_id=%s FOR UPDATE", (bid,))
        b = cur.fetchone()
        if b is None:
            conn.rollback()
            return False, "Booking not found"
        if b[2] == "cancelled":
            conn.rollback()
            return False, "Already cancelled"

        cur.execute("UPDATE bookings SET status='cancelled' WHERE booking_id=%s", (bid,))
        cur.execute("UPDATE trains SET available_seats = available_seats + %s "
                    "WHERE train_id=%s", (b[1], b[0]))
        conn.commit()
        return True, f"Booking cancelled. {b[1]} seat(s) returned"
    except mysql.connector.Error as e:
        conn.rollback()
        return False, f"Database error: {e}"
    finally:
        conn.close()


def bookings_page():
    st.title("📋 Bookings")
    show_flash()

    # JOIN: combine 3 tables so we can show names instead of ids
    bookings = fetch("""SELECT b.booking_id, p.passenger_name, t.train_name,
                               t.source, t.destination, b.travel_date,
                               b.seats_booked, b.total_fare, b.status
                        FROM bookings b
                        JOIN passengers p ON b.passenger_id = p.passenger_id
                        JOIN trains t ON b.train_id = t.train_id
                        ORDER BY b.booking_id""")
    if not bookings:
        st.info("No bookings yet")
        return

    df = pd.DataFrame(bookings).rename(columns={
        "booking_id": "ID", "passenger_name": "Passenger", "train_name": "Train",
        "source": "From", "destination": "To", "travel_date": "Date",
        "seats_booked": "Seats", "total_fare": "Total (Rs)", "status": "Status"})
    st.dataframe(df, hide_index=True)

    st.subheader("Cancel a booking")
    active = [b for b in bookings if b["status"] == "confirmed"]
    if not active:
        st.info("No confirmed bookings to cancel")
        return
    with st.form("cancel_form"):
        chosen = st.selectbox("Confirmed booking", active, format_func=lambda b: (
            f"#{b['booking_id']} - {b['passenger_name']} - {b['train_name']} "
            f"({b['seats_booked']} seats)"))
        if st.form_submit_button("Cancel booking"):
            ok, message = cancel_booking(chosen["booking_id"])
            flash("success" if ok else "error", message)
            st.rerun()


# ---------------------------------------------------------------------------
# 6. REPORT PAGE
# ---------------------------------------------------------------------------

def report_page():
    st.title("📊 Revenue Report")

    # COUNT + SUM + GROUP BY: bookings and revenue per train (confirmed only)
    rows = fetch("""SELECT t.train_name, COUNT(b.booking_id) AS bookings,
                           SUM(b.total_fare) AS revenue
                    FROM bookings b
                    JOIN trains t ON b.train_id = t.train_id
                    WHERE b.status = 'confirmed'
                    GROUP BY t.train_name
                    ORDER BY SUM(b.total_fare) DESC""")
    if not rows:
        st.info("No confirmed bookings yet")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Total revenue", f"Rs {sum(r['revenue'] for r in rows):.2f}")
    c2.metric("Confirmed bookings", sum(r["bookings"] for r in rows))
    c3.metric("Top train", rows[0]["train_name"].title())

    df = pd.DataFrame(rows).rename(columns={
        "train_name": "Train", "bookings": "Bookings", "revenue": "Revenue (Rs)"})
    st.subheader("Revenue per train")
    st.bar_chart(df.set_index("Train")["Revenue (Rs)"])
    st.dataframe(df, hide_index=True)


# ---------------------------------------------------------------------------
# 7. SIDEBAR MENU
# ---------------------------------------------------------------------------

PAGES = {
    "Trains": trains_page,
    "Passengers": passengers_page,
    "Book a Ticket": book_page,
    "Bookings": bookings_page,
    "Report": report_page,
}

st.sidebar.title("🚆 Railway Reservation")
choice = st.sidebar.radio("Go to", list(PAGES))

try:
    PAGES[choice]()                    # run the page the user picked
except mysql.connector.Error as e:
    st.error(f"Cannot reach the database. Check MySQL is running and the password "
             f"in .env is correct.\n\nDetails: {e}")

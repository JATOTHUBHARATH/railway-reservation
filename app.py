import os
from datetime import date, datetime, timedelta
from decimal import Decimal

import mysql.connector
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

load_dotenv()

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)


def get_db():
    """Open a new connection for every request (safe for a web server)."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "NewPass123"),
        database=os.getenv("DB_NAME", "railway_db"),
    )


def clean(row):
    """Make MySQL types JSON-friendly (Decimal -> float, TIME -> 'HH:MM:SS')."""
    out = {}
    for key, value in row.items():
        if isinstance(value, Decimal):
            out[key] = float(value)
        elif isinstance(value, timedelta):
            total = int(value.total_seconds())
            out[key] = f"{total // 3600:02d}:{(total % 3600) // 60:02d}:{total % 60:02d}"
        else:
            out[key] = value
    return out


@app.route("/")
def home():
    return send_from_directory(app.static_folder, "trains.html")


#TRAINS

@app.route("/api/trains", methods=["GET"])
def list_trains():
    q = request.args.get("q", "").strip()
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        if q:
            word = f"%{q}%"
            cur.execute(
                "SELECT * FROM trains WHERE train_name LIKE %s OR source LIKE %s "
                "OR destination LIKE %s ORDER BY train_id",
                (word, word, word),
            )
        else:
            cur.execute("SELECT * FROM trains ORDER BY train_id")
        return jsonify([clean(r) for r in cur.fetchall()])
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/trains", methods=["POST"])
def add_train():
    d = request.get_json(silent=True) or {}
    try:
        tid = int(d["train_id"])
        name = str(d["train_name"]).strip()
        source = str(d["source"]).strip()
        dest = str(d["destination"]).strip()
        dep = str(d["departure_time"]).strip()
        seats = int(d["total_seats"])
        fare = float(d["fare"])
    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "Fill all fields with valid values"}), 400

    if not name or not source or not dest:
        return jsonify({"error": "Name, source and destination are required"}), 400
    if seats <= 0 or fare <= 0:
        return jsonify({"error": "Seats and fare must be greater than 0"}), 400
    if len(dep) == 5:          # browser time input gives HH:MM
        dep += ":00"

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO trains VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (tid, name, source, dest, dep, seats, seats, fare),
        )
        conn.commit()
        return jsonify({"message": "Train added"}), 201
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()


@app.route("/api/trains/<int:tid>", methods=["PUT"])
def update_fare(tid):
    d = request.get_json(silent=True) or {}
    try:
        fare = float(d["fare"])
    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "Enter a valid fare"}), 400
    if fare <= 0:
        return jsonify({"error": "Fare must be greater than 0"}), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE trains SET fare=%s WHERE train_id=%s", (fare, tid))
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({"error": "Train not found (or fare unchanged)"}), 404
        return jsonify({"message": "Fare updated"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()


@app.route("/api/trains/<int:tid>", methods=["DELETE"])
def delete_train(tid):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM trains WHERE train_id=%s", (tid,))
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({"error": "Train not found"}), 404
        return jsonify({"message": "Train deleted"})
    except mysql.connector.Error:
        conn.rollback()
        return jsonify({"error": "Cannot delete: this train has bookings"}), 400
    finally:
        conn.close()


#PASSENGERS

@app.route("/api/passengers", methods=["GET"])
def list_passengers():
    q = request.args.get("q", "").strip()
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        if q:
            cur.execute("SELECT * FROM passengers WHERE passenger_name LIKE %s "
                        "ORDER BY passenger_id", (f"%{q}%",))
        else:
            cur.execute("SELECT * FROM passengers ORDER BY passenger_id")
        return jsonify([clean(r) for r in cur.fetchall()])
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/passengers", methods=["POST"])
def add_passenger():
    d = request.get_json(silent=True) or {}
    try:
        pid = int(d["passenger_id"])
        name = str(d["passenger_name"]).strip()
        age = int(d["age"])
        gender = str(d["gender"]).strip().lower()
        phone = str(d["phone"]).strip()
    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "Fill all fields with valid values"}), 400

    if not name:
        return jsonify({"error": "Name is required"}), 400
    if age <= 0:
        return jsonify({"error": "Age must be greater than 0"}), 400
    if gender not in ("male", "female", "others"):
        return jsonify({"error": "Choose a valid gender"}), 400
    if len(phone) != 10 or not phone.isdigit():
        return jsonify({"error": "Phone must be exactly 10 digits"}), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO passengers VALUES (%s,%s,%s,%s,%s)",
                    (pid, name, age, gender, phone))
        conn.commit()
        return jsonify({"message": "Passenger added"}), 201
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()


@app.route("/api/passengers/<int:pid>", methods=["PUT"])
def update_phone(pid):
    d = request.get_json(silent=True) or {}
    phone = str(d.get("phone", "")).strip()
    if len(phone) != 10 or not phone.isdigit():
        return jsonify({"error": "Phone must be exactly 10 digits"}), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE passengers SET phone=%s WHERE passenger_id=%s", (phone, pid))
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({"error": "Passenger not found (or phone unchanged)"}), 404
        return jsonify({"message": "Phone updated"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()


@app.route("/api/passengers/<int:pid>", methods=["DELETE"])
def delete_passenger(pid):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM passengers WHERE passenger_id=%s", (pid,))
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({"error": "Passenger not found"}), 404
        return jsonify({"message": "Passenger deleted"})
    except mysql.connector.Error:
        conn.rollback()
        return jsonify({"error": "Cannot delete: this passenger has bookings"}), 400
    finally:
        conn.close()


#BOOKINGS

@app.route("/api/bookings", methods=["GET"])
def list_bookings():
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""SELECT b.booking_id, p.passenger_name, t.train_name,
                              t.source, t.destination,
                              b.travel_date, b.seats_booked, b.total_fare, b.status
                       FROM bookings b
                       JOIN passengers p ON b.passenger_id = p.passenger_id
                       JOIN trains t ON b.train_id = t.train_id
                       ORDER BY b.booking_id""")
        rows = []
        for r in cur.fetchall():
            r = clean(r)
            r["travel_date"] = str(r["travel_date"])
            rows.append(r)
        return jsonify(rows)
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/bookings", methods=["POST"])
def book_ticket():
    d = request.get_json(silent=True) or {}
    try:
        pid = int(d["passenger_id"])
        tid = int(d["train_id"])
        seats = int(d["seats_booked"])
        travel = datetime.strptime(str(d["travel_date"]), "%Y-%m-%d").date()
    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "Choose passenger, train, a valid date and seats"}), 400

    if seats <= 0:
        return jsonify({"error": "Seats must be greater than 0"}), 400
    if travel < date.today():
        return jsonify({"error": "Travel date cannot be in the past"}), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM passengers WHERE passenger_id=%s", (pid,))
        if cur.fetchone() is None:
            return jsonify({"error": "Passenger not found"}), 404

        # FOR UPDATE locks the train row so two people can't take the last seat
        cur.execute("SELECT fare, available_seats FROM trains "
                    "WHERE train_id=%s FOR UPDATE", (tid,))
        train = cur.fetchone()
        if train is None:
            conn.rollback()
            return jsonify({"error": "Train not found"}), 404
        if seats > train[1]:
            conn.rollback()
            return jsonify({"error": f"Only {train[1]} seats available"}), 400

        total = train[0] * seats
        cur.execute("INSERT INTO bookings (passenger_id, train_id, travel_date, "
                    "seats_booked, total_fare) VALUES (%s,%s,%s,%s,%s)",
                    (pid, tid, travel, seats, total))
        cur.execute("UPDATE trains SET available_seats = available_seats - %s "
                    "WHERE train_id=%s", (seats, tid))
        conn.commit()
        return jsonify({"message": f"Booking confirmed. Total fare: ₹{float(total):.2f}"}), 201
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()


@app.route("/api/bookings/<int:bid>/cancel", methods=["PUT"])
def cancel_booking(bid):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT train_id, seats_booked, status FROM bookings "
                    "WHERE booking_id=%s FOR UPDATE", (bid,))
        b = cur.fetchone()
        if b is None:
            conn.rollback()
            return jsonify({"error": "Booking not found"}), 404
        if b[2] == "cancelled":
            conn.rollback()
            return jsonify({"error": "Already cancelled"}), 400

        cur.execute("UPDATE bookings SET status='cancelled' WHERE booking_id=%s", (bid,))
        cur.execute("UPDATE trains SET available_seats = available_seats + %s "
                    "WHERE train_id=%s", (b[1], b[0]))
        conn.commit()
        return jsonify({"message": f"Booking cancelled. {b[1]} seat(s) returned"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()


# REPORT

@app.route("/api/report/revenue", methods=["GET"])
def revenue_report():
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""SELECT t.train_name, COUNT(b.booking_id) AS bookings,
                              SUM(b.total_fare) AS revenue
                       FROM bookings b
                       JOIN trains t ON b.train_id = t.train_id
                       WHERE b.status = 'confirmed'
                       GROUP BY t.train_name
                       ORDER BY SUM(b.total_fare) DESC""")
        return jsonify([clean(r) for r in cur.fetchall()])
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


if __name__ == "__main__":
    app.run(debug=True, port=5000)

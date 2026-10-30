import mysql.connector
from datetime import datetime

DB_PASSWORD = "NewPass123"

# Connect to the database
conn = mysql.connector.connect(host="localhost", user="root",
                               password=DB_PASSWORD, database="railway_db")
cursor = conn.cursor()


#TRAINS 

def add_train():
    try:
        tid = int(input("Train id: "))
        name = input("Train name: ")
        source = input("Source: ")
        dest = input("Destination: ")
        dep = input("Departure time (HH:MM:SS): ")
        seats = int(input("Total seats: "))
        fare = float(input("Fare per seat: "))
        if seats <= 0 or fare <= 0:
            print("Seats and fare must be greater than 0")
            return
        cursor.execute("INSERT INTO trains VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                       (tid, name, source, dest, dep, seats, seats, fare))
        conn.commit()
        print("Train added")
    except ValueError:
        print("Enter numbers for id, seats and fare")
    except mysql.connector.Error as e:
        print("Database error:", e)


def show_trains():
    try:
        cursor.execute("SELECT * FROM trains ORDER BY train_id")
        for row in cursor.fetchall():
            print("ID:", row[0], "| Name:", row[1], "| From:", row[2], "| To:", row[3],
                  "| Departs:", str(row[4]), "| Seats left:", row[6], "/", row[5],
                  "| Fare:", row[7])
    except mysql.connector.Error as e:
        print("Database error:", e)


def search_train():
    try:
        word = "%" + input("Enter train name, source or destination: ") + "%"
        cursor.execute("SELECT * FROM trains WHERE train_name LIKE %s OR source LIKE %s "
                       "OR destination LIKE %s", (word, word, word))
        rows = cursor.fetchall()
        print(rows if rows else "No train found")
    except mysql.connector.Error as e:
        print("Database error:", e)


def update_train():
    try:
        tid = int(input("Train id: "))
        fare = float(input("New fare: "))
        cursor.execute("UPDATE trains SET fare=%s WHERE train_id=%s", (fare, tid))
        conn.commit()
        print("Updated" if cursor.rowcount else "Not found")
    except ValueError:
        print("Enter numbers only")
    except mysql.connector.Error as e:
        print("Database error:", e)


def delete_train():
    try:
        tid = int(input("Train id: "))
        cursor.execute("DELETE FROM trains WHERE train_id=%s", (tid,))
        conn.commit()
        print("Deleted" if cursor.rowcount else "Not found")
    except ValueError:
        print("Enter a number")
    except mysql.connector.Error as e:
        print("Cannot delete, train has bookings:", e)


# PASSENGERS

def add_passenger():
    try:
        pid = int(input("Passenger id: "))
        name = input("Name: ")
        age = int(input("Age: "))
        gender = input("Gender (male/female/others): ")
        phone = input("Phone (10 digits): ")
        if age <= 0:
            print("Age must be greater than 0")
            return
        if len(phone) != 10 or not phone.isdigit():
            print("Phone must be exactly 10 digits")
            return
        cursor.execute("INSERT INTO passengers VALUES (%s,%s,%s,%s,%s)",
                       (pid, name, age, gender, phone))
        conn.commit()
        print("Passenger added")
    except ValueError:
        print("Enter numbers for id and age")
    except mysql.connector.Error as e:
        print("Database error:", e)


def show_passengers():
    try:
        cursor.execute("SELECT * FROM passengers ORDER BY passenger_id")
        for row in cursor.fetchall():
            print(row)
    except mysql.connector.Error as e:
        print("Database error:", e)


def search_passenger():
    try:
        word = "%" + input("Enter name or part of name: ") + "%"
        cursor.execute("SELECT * FROM passengers WHERE passenger_name LIKE %s", (word,))
        rows = cursor.fetchall()
        print(rows if rows else "No passenger found")
    except mysql.connector.Error as e:
        print("Database error:", e)


def update_passenger():
    try:
        pid = int(input("Passenger id: "))
        phone = input("New phone (10 digits): ")
        if len(phone) != 10 or not phone.isdigit():
            print("Phone must be exactly 10 digits")
            return
        cursor.execute("UPDATE passengers SET phone=%s WHERE passenger_id=%s", (phone, pid))
        conn.commit()
        print("Updated" if cursor.rowcount else "Not found")
    except ValueError:
        print("Enter a number for the id")
    except mysql.connector.Error as e:
        print("Database error:", e)


def delete_passenger():
    try:
        pid = int(input("Passenger id: "))
        cursor.execute("DELETE FROM passengers WHERE passenger_id=%s", (pid,))
        conn.commit()
        print("Deleted" if cursor.rowcount else "Not found")
    except ValueError:
        print("Enter a number")
    except mysql.connector.Error as e:
        print("Cannot delete, passenger has bookings:", e)


#BOOKINGS 

def book_ticket():
    try:
        pid = int(input("Passenger id: "))
        tid = int(input("Train id: "))
        travel = input("Travel date (YYYY-MM-DD): ")
        datetime.strptime(travel, "%Y-%m-%d")
        seats = int(input("Number of seats: "))
        if seats <= 0:
            print("Seats must be greater than 0")
            return

        cursor.execute("SELECT fare, available_seats FROM trains WHERE train_id=%s", (tid,))
        train = cursor.fetchone()
        if train is None:
            print("Train not found")
            return
        if seats > train[1]:
            print("Only", train[1], "seats available")
            return

        total = train[0] * seats
        cursor.execute("INSERT INTO bookings (passenger_id, train_id, travel_date, "
                       "seats_booked, total_fare) VALUES (%s,%s,%s,%s,%s)",
                       (pid, tid, travel, seats, total))
        cursor.execute("UPDATE trains SET available_seats = available_seats - %s "
                       "WHERE train_id=%s", (seats, tid))
        conn.commit()        # both changes saved together
        print("Booking confirmed. Total fare:", total)
    except ValueError:
        print("Enter numbers for ids and seats, and a valid date")
    except mysql.connector.Error as e:
        conn.rollback()      # undo both if something fails
        print("Database error:", e)


# Show bookings with names, using a JOIN
def show_bookings():
    try:
        cursor.execute("""SELECT b.booking_id, p.passenger_name, t.train_name,
                                 b.travel_date, b.seats_booked, b.total_fare, b.status
                          FROM bookings b
                          JOIN passengers p ON b.passenger_id = p.passenger_id
                          JOIN trains t ON b.train_id = t.train_id
                          ORDER BY b.booking_id""")
        for row in cursor.fetchall():
            print(row)
    except mysql.connector.Error as e:
        print("Database error:", e)


# Cancel a booking and return the seats to the train
def cancel_booking():
    try:
        bid = int(input("Booking id to cancel: "))
        cursor.execute("SELECT train_id, seats_booked, status FROM bookings "
                       "WHERE booking_id=%s", (bid,))
        b = cursor.fetchone()
        if b is None:
            print("Booking not found")
        elif b[2] == "cancelled":
            print("Already cancelled")
        else:
            cursor.execute("UPDATE bookings SET status='cancelled' WHERE booking_id=%s", (bid,))
            cursor.execute("UPDATE trains SET available_seats = available_seats + %s "
                           "WHERE train_id=%s", (b[1], b[0]))
            conn.commit()
            print("Booking cancelled. Seats returned:", b[1])
    except ValueError:
        print("Enter a number")
    except mysql.connector.Error as e:
        conn.rollback()
        print("Database error:", e)


# Report: bookings and revenue per train (COUNT, SUM, GROUP BY)
def revenue_report():
    try:
        cursor.execute("""SELECT t.train_name, COUNT(b.booking_id), SUM(b.total_fare)
                          FROM bookings b
                          JOIN trains t ON b.train_id = t.train_id
                          WHERE b.status = 'confirmed'
                          GROUP BY t.train_name
                          ORDER BY SUM(b.total_fare) DESC""")
        for row in cursor.fetchall():
            print("Train:", row[0], "| Bookings:", row[1], "| Revenue:", row[2])
    except mysql.connector.Error as e:
        print("Database error:", e)



def train_menu():
    while True:
        print("\n--- Train Menu ---")
        print("1. Add  2. Show  3. Search  4. Update fare  5. Delete  6. Back")
        option = input("Enter your choice: ")
        if option == "1":
            add_train()
        elif option == "2":
            show_trains()
        elif option == "3":
            search_train()
        elif option == "4":
            update_train()
        elif option == "5":
            delete_train()
        elif option == "6":
            break
        else:
            print("Invalid choice")


def passenger_menu():
    while True:
        print("\n--- Passenger Menu ---")
        print("1. Add  2. Show  3. Search  4. Update phone  5. Delete  6. Back")
        option = input("Enter your choice: ")
        if option == "1":
            add_passenger()
        elif option == "2":
            show_passengers()
        elif option == "3":
            search_passenger()
        elif option == "4":
            update_passenger()
        elif option == "5":
            delete_passenger()
        elif option == "6":
            break
        else:
            print("Invalid choice")


def booking_menu():
    while True:
        print("\n--- Booking Menu ---")
        print("1. Book  2. Show  3. Cancel  4. Report  5. Back")
        option = input("Enter your choice: ")
        if option == "1":
            book_ticket()
        elif option == "2":
            show_bookings()
        elif option == "3":
            cancel_booking()
        elif option == "4":
            revenue_report()
        elif option == "5":
            break
        else:
            print("Invalid choice")



menu = {"1": train_menu, "2": passenger_menu, "3": booking_menu}

while True:
    print("\n=== Railway Reservation System ===")
    print("1. Trains  2. Passengers  3. Bookings  4. Exit")
    choice = input("Enter your choice: ")
    if choice in menu:
        menu[choice]()
    elif choice == "4":
        print("Goodbye")
        break
    else:
        print("Invalid choice, try again")

conn.close()
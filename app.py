from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3, uuid, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cloud-bus-pass-demo-secret")
DB = os.path.join(os.path.dirname(__file__), "bus_pass.db")

BUSES = [
    {"id": 1, "name": "Pune → Mumbai Express", "from": "Pune", "to": "Mumbai", "time": "06:30 AM", "price": 450, "seats": 40},
    {"id": 2, "name": "Pune → Nashik Express", "from": "Pune", "to": "Nashik", "time": "08:00 AM", "price": 350, "seats": 40},
    {"id": 3, "name": "Pune → Junnar", "from": "Pune", "to": "Junnar", "time": "09:30 AM", "price": 180, "seats": 50},
    {"id": 4, "name": "Mumbai → Pune Express", "from": "Mumbai", "to": "Pune", "time": "05:30 PM", "price": 450, "seats": 40},
]

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.execute("""CREATE TABLE IF NOT EXISTS bookings(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id TEXT UNIQUE NOT NULL,
        passenger TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        bus_id INTEGER NOT NULL,
        journey_date TEXT NOT NULL,
        seat_no INTEGER NOT NULL,
        price REAL NOT NULL,
        status TEXT DEFAULT 'CONFIRMED',
        created_at TEXT NOT NULL,
        UNIQUE(bus_id, journey_date, seat_no)
    )""")
    conn.commit()
    conn.close()

def bus_by_id(bus_id):
    return next((b for b in BUSES if b["id"] == bus_id), None)

def booked_seats(bus_id, journey_date):
    conn = db()
    rows = conn.execute(
        "SELECT seat_no FROM bookings WHERE bus_id=? AND journey_date=? AND status='CONFIRMED'",
        (bus_id, journey_date)
    ).fetchall()
    conn.close()
    return {r["seat_no"] for r in rows}

@app.route("/")
def index():
    return render_template("index.html", buses=BUSES)

@app.route("/book/<int:bus_id>", methods=["GET", "POST"])
def book(bus_id):
    bus = bus_by_id(bus_id)
    if not bus:
        return "Bus not found", 404

    journey_date = request.args.get("date", "") if request.method == "GET" else request.form.get("journey_date", "")
    selected_seat = request.form.get("seat_no", "")
    occupied = booked_seats(bus_id, journey_date) if journey_date else set()

    if request.method == "POST":
        passenger = request.form.get("passenger", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        try:
            seat = int(selected_seat)
        except ValueError:
            seat = 0

        if not passenger or not email or not phone or not journey_date:
            flash("Please fill all required details.", "error")
        elif seat < 1 or seat > bus["seats"]:
            flash("Invalid seat number.", "error")
        elif journey_date < datetime.now().strftime("%Y-%m-%d"):
            flash("Journey date cannot be in the past.", "error")
        else:
            # Server-side pricing prevents client-side price tampering.
            server_price = bus["price"]
            booking_id = "BP-" + uuid.uuid4().hex[:10].upper()
            conn = db()
            try:
                conn.execute("""INSERT INTO bookings
                    (booking_id, passenger, email, phone, bus_id, journey_date, seat_no, price, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (booking_id, passenger, email, phone, bus_id, journey_date, seat, server_price,
                     datetime.now().isoformat(timespec="seconds")))
                conn.commit()
                conn.close()
                return redirect(url_for("ticket", booking_id=booking_id))
            except sqlite3.IntegrityError:
                conn.close()
                flash("That seat is already booked. Please choose another seat.", "error")
            occupied = booked_seats(bus_id, journey_date)

    return render_template("book.html", bus=bus, occupied=occupied, journey_date=journey_date)

@app.route("/ticket/<booking_id>")
def ticket(booking_id):
    conn = db()
    row = conn.execute("SELECT * FROM bookings WHERE booking_id=?", (booking_id,)).fetchone()
    conn.close()
    if not row:
        return "Ticket not found", 404
    bus = bus_by_id(row["bus_id"])
    return render_template("ticket.html", booking=row, bus=bus)

@app.route("/verify", methods=["GET", "POST"])
def verify():
    booking = None
    bus = None
    if request.method == "POST":
        booking_id = request.form.get("booking_id", "").strip().upper()
        conn = db()
        booking = conn.execute("SELECT * FROM bookings WHERE booking_id=?", (booking_id,)).fetchone()
        conn.close()
        if booking:
            bus = bus_by_id(booking["bus_id"])
        else:
            flash("No valid ticket found for this booking ID.", "error")
    return render_template("verify.html", booking=booking, bus=bus)

@app.route("/admin")
def admin():
    conn = db()
    bookings = conn.execute("SELECT * FROM bookings ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin.html", bookings=bookings, bus_by_id=bus_by_id)

@app.route("/health")
def health():
    return {"status": "ok", "service": "Cloud-Based Bus Pass System"}

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)

# Cloud-Based Bus Pass System

A ready-to-deploy Flask web application for online bus ticket/pass booking.

## Features
- Online bus search and booking
- Server-side price validation to prevent incorrect pricing
- Seat-locking through a database UNIQUE constraint
- Unique booking ID for every confirmed ticket
- Ticket verification page
- Admin booking dashboard
- Health-check endpoint for cloud deployment
- Render/Gunicorn deployment configuration
- Responsive UI

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Open: http://127.0.0.1:5000

## Deploy on Render

1. Create a GitHub repository.
2. Upload all files from this project.
3. On Render, create a new Web Service and connect the GitHub repository.
4. Render can use:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
5. Deploy and open the generated `.onrender.com` URL.

## Project objective mapping

- Ticket loss/theft prevention: unique booking IDs + database records + verification.
- Incorrect pricing prevention: price is calculated on the server, not accepted from the browser.
- Duplicate booking prevention: database UNIQUE(bus_id, journey_date, seat_no).
- Scalability: stateless Flask web layer + Gunicorn makes the application suitable for cloud scaling.
- Reliability: health endpoint, persistent booking database design, and validation.

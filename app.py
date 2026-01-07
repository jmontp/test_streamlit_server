"""
Tennis Court Scheduling System
A simple write-only (or password-protected mutable) booking system for a neighborhood tennis court.
"""

import streamlit as st
import sqlite3
from datetime import datetime, timedelta
from hashlib import sha256
from contextlib import contextmanager

# Configuration
DB_PATH = "tennis_schedule.db"
COURT_NAME = "Neighborhood Tennis Court"
TIME_SLOTS = [
    "06:00", "07:00", "08:00", "09:00", "10:00", "11:00",
    "12:00", "13:00", "14:00", "15:00", "16:00", "17:00",
    "18:00", "19:00", "20:00", "21:00"
]
DAYS_AHEAD = 7  # Show schedule for next 7 days


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize the database with the reservations table."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time_slot TEXT NOT NULL,
                player_name TEXT NOT NULL,
                phone TEXT,
                password_hash TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(date, time_slot)
            )
        """)
        conn.commit()


def hash_password(password: str) -> str:
    """Hash a password for storage."""
    return sha256(password.encode()).hexdigest()


def get_reservations(date: str) -> dict:
    """Get all reservations for a given date."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM reservations WHERE date = ?", (date,)
        ).fetchall()
        return {row["time_slot"]: dict(row) for row in rows}


def get_all_reservations_in_range(start_date: str, end_date: str) -> dict:
    """Get all reservations in a date range."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM reservations WHERE date >= ? AND date <= ?",
            (start_date, end_date)
        ).fetchall()
        result = {}
        for row in rows:
            date = row["date"]
            if date not in result:
                result[date] = {}
            result[date][row["time_slot"]] = dict(row)
        return result


def create_reservation(date: str, time_slot: str, player_name: str,
                       phone: str = "", password: str = "") -> tuple[bool, str]:
    """Create a new reservation. Returns (success, message)."""
    password_hash = hash_password(password) if password else None

    try:
        with get_db() as conn:
            conn.execute(
                """INSERT INTO reservations (date, time_slot, player_name, phone, password_hash, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (date, time_slot, player_name, phone, password_hash, datetime.now().isoformat())
            )
            conn.commit()
        return True, "Reservation created successfully!"
    except sqlite3.IntegrityError:
        return False, "This time slot is already booked."


def cancel_reservation(date: str, time_slot: str, password: str = "") -> tuple[bool, str]:
    """Cancel a reservation. Returns (success, message)."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM reservations WHERE date = ? AND time_slot = ?",
            (date, time_slot)
        ).fetchone()

        if not row:
            return False, "No reservation found for this time slot."

        # Check password if one was set
        if row["password_hash"]:
            if not password:
                return False, "This reservation is password protected. Please enter the password."
            if hash_password(password) != row["password_hash"]:
                return False, "Incorrect password."

        conn.execute(
            "DELETE FROM reservations WHERE date = ? AND time_slot = ?",
            (date, time_slot)
        )
        conn.commit()
        return True, "Reservation cancelled successfully!"


def main():
    st.set_page_config(
        page_title="Tennis Court Scheduler",
        page_icon="🎾",
        layout="wide"
    )

    # Initialize database
    init_db()

    st.title(f"🎾 {COURT_NAME} Scheduler")
    st.markdown("---")

    # Get date range for display
    today = datetime.now().date()
    dates = [(today + timedelta(days=i)) for i in range(DAYS_AHEAD)]
    date_strings = [d.strftime("%Y-%m-%d") for d in dates]

    # Fetch all reservations in range
    all_reservations = get_all_reservations_in_range(date_strings[0], date_strings[-1])

    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["📅 View Schedule", "➕ Book a Slot", "❌ Cancel Booking"])

    # Tab 1: View Schedule
    with tab1:
        st.subheader("Weekly Schedule")

        # Create schedule grid
        cols = st.columns(len(dates))

        for col_idx, (date, date_str) in enumerate(zip(dates, date_strings)):
            with cols[col_idx]:
                day_name = date.strftime("%a")
                st.markdown(f"**{day_name}**<br>{date.strftime('%m/%d')}", unsafe_allow_html=True)

                day_reservations = all_reservations.get(date_str, {})

                for time_slot in TIME_SLOTS:
                    if time_slot in day_reservations:
                        res = day_reservations[time_slot]
                        locked = "🔒" if res["password_hash"] else ""
                        st.markdown(
                            f"<div style='background-color: #ffcccb; padding: 4px; margin: 2px; border-radius: 4px; font-size: 12px;'>"
                            f"<b>{time_slot}</b> {locked}<br>{res['player_name']}</div>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f"<div style='background-color: #90EE90; padding: 4px; margin: 2px; border-radius: 4px; font-size: 12px;'>"
                            f"<b>{time_slot}</b><br>Available</div>",
                            unsafe_allow_html=True
                        )

    # Tab 2: Book a Slot
    with tab2:
        st.subheader("Book a Time Slot")

        with st.form("booking_form"):
            col1, col2 = st.columns(2)

            with col1:
                selected_date = st.selectbox(
                    "Select Date",
                    options=date_strings,
                    format_func=lambda x: datetime.strptime(x, "%Y-%m-%d").strftime("%A, %B %d")
                )

                # Show only available slots
                day_reservations = all_reservations.get(selected_date, {})
                available_slots = [t for t in TIME_SLOTS if t not in day_reservations]

                if available_slots:
                    selected_time = st.selectbox("Select Time", options=available_slots)
                else:
                    st.warning("No available slots for this date.")
                    selected_time = None

            with col2:
                player_name = st.text_input("Your Name *", max_chars=50)
                phone = st.text_input("Phone Number (optional)", max_chars=20)
                password = st.text_input(
                    "Password (optional - for cancellation)",
                    type="password",
                    help="Set a password if you want to be able to cancel this reservation later."
                )

            submitted = st.form_submit_button("Book Slot", use_container_width=True)

            if submitted:
                if not player_name:
                    st.error("Please enter your name.")
                elif not selected_time:
                    st.error("Please select an available time slot.")
                else:
                    success, message = create_reservation(
                        selected_date, selected_time, player_name, phone, password
                    )
                    if success:
                        st.success(message)
                        if password:
                            st.info("Remember your password to cancel this reservation.")
                        st.rerun()
                    else:
                        st.error(message)

    # Tab 3: Cancel Booking
    with tab3:
        st.subheader("Cancel a Reservation")

        with st.form("cancel_form"):
            col1, col2 = st.columns(2)

            with col1:
                cancel_date = st.selectbox(
                    "Select Date",
                    options=date_strings,
                    format_func=lambda x: datetime.strptime(x, "%Y-%m-%d").strftime("%A, %B %d"),
                    key="cancel_date"
                )

                # Show only booked slots
                day_reservations = all_reservations.get(cancel_date, {})
                booked_slots = list(day_reservations.keys())

                if booked_slots:
                    cancel_time = st.selectbox(
                        "Select Time",
                        options=booked_slots,
                        format_func=lambda x: f"{x} - {day_reservations[x]['player_name']}" +
                                            (" 🔒" if day_reservations[x]['password_hash'] else ""),
                        key="cancel_time"
                    )
                else:
                    st.info("No reservations to cancel for this date.")
                    cancel_time = None

            with col2:
                cancel_password = st.text_input(
                    "Password (if required)",
                    type="password",
                    help="Enter the password if this reservation is protected.",
                    key="cancel_password"
                )

            cancel_submitted = st.form_submit_button("Cancel Reservation", use_container_width=True)

            if cancel_submitted:
                if not cancel_time:
                    st.error("Please select a reservation to cancel.")
                else:
                    success, message = cancel_reservation(cancel_date, cancel_time, cancel_password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray; font-size: 12px;'>"
        "Tennis Court Scheduler - A neighborhood scheduling system"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

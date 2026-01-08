"""
Tennis Court Scheduling System
Caparra Hills Tennis Club - Guaynabo, Puerto Rico
"""

import streamlit as st
import sqlite3
from datetime import datetime, timedelta
from hashlib import sha256
from contextlib import contextmanager

# Configuration
DB_PATH = "tennis_schedule.db"
COURT_NAME = "Caparra Hills Tennis Club"
LOCATION = "Guaynabo, Puerto Rico"
TIME_SLOTS = [
    "06:00", "07:00", "08:00", "09:00", "10:00", "11:00",
    "12:00", "13:00", "14:00", "15:00", "16:00", "17:00",
    "18:00", "19:00", "20:00", "21:00"
]
DAYS_AHEAD = 7  # Show schedule for next 7 days

# Caparra Hills color palette - tropical elegance
COLORS = {
    "primary_green": "#1B4D3E",      # Deep forest green
    "light_green": "#2D6A4F",        # Tropical green
    "accent_gold": "#D4A853",        # Warm gold
    "cream": "#F5F1E6",              # Elegant cream
    "terracotta": "#C67B5C",         # Warm terracotta
    "available": "#E8F5E9",          # Soft mint green
    "available_border": "#4CAF50",   # Fresh green
    "booked": "#FFEBEE",             # Soft coral
    "booked_border": "#C67B5C",      # Terracotta
}


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
        page_title=f"{COURT_NAME} - {LOCATION}",
        page_icon="🌴",
        layout="wide"
    )

    # Custom CSS for Caparra Hills tropical elegance theme
    st.markdown(f"""
        <style>
        /* Main header styling */
        .main-header {{
            background: linear-gradient(135deg, {COLORS["primary_green"]} 0%, {COLORS["light_green"]} 100%);
            padding: 1.5rem 2rem;
            border-radius: 12px;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .main-header h1 {{
            color: {COLORS["cream"]};
            margin: 0;
            font-size: 2rem;
            font-weight: 600;
        }}
        .main-header .location {{
            color: {COLORS["accent_gold"]};
            font-size: 1.1rem;
            margin-top: 0.25rem;
        }}

        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
            background-color: {COLORS["cream"]};
            padding: 0.5rem;
            border-radius: 10px;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: white;
            border-radius: 8px;
            color: {COLORS["primary_green"]};
            font-weight: 500;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {COLORS["primary_green"]} !important;
            color: {COLORS["cream"]} !important;
        }}

        /* Button styling */
        .stButton > button {{
            background: linear-gradient(135deg, {COLORS["primary_green"]} 0%, {COLORS["light_green"]} 100%);
            color: {COLORS["cream"]};
            border: none;
            font-weight: 500;
            transition: all 0.3s ease;
        }}
        .stButton > button:hover {{
            background: linear-gradient(135deg, {COLORS["light_green"]} 0%, {COLORS["primary_green"]} 100%);
            box-shadow: 0 4px 12px rgba(27, 77, 62, 0.3);
        }}

        /* Footer styling */
        .footer {{
            background: linear-gradient(135deg, {COLORS["primary_green"]} 0%, {COLORS["light_green"]} 100%);
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            margin-top: 2rem;
        }}
        .footer p {{
            color: {COLORS["cream"]};
            margin: 0;
            font-size: 0.9rem;
        }}
        .footer .gold {{
            color: {COLORS["accent_gold"]};
        }}
        </style>
    """, unsafe_allow_html=True)

    # Initialize database
    init_db()

    # Elegant header
    st.markdown(f"""
        <div class="main-header">
            <h1>🌴 {COURT_NAME}</h1>
            <div class="location">📍 {LOCATION}</div>
        </div>
    """, unsafe_allow_html=True)

    # Get date range for display
    today = datetime.now().date()
    dates = [(today + timedelta(days=i)) for i in range(DAYS_AHEAD)]
    date_strings = [d.strftime("%Y-%m-%d") for d in dates]

    # Fetch all reservations in range
    all_reservations = get_all_reservations_in_range(date_strings[0], date_strings[-1])

    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["📅 Horario", "🎾 Reservar", "🗑️ Cancelar"])

    # Tab 1: View Schedule
    with tab1:
        st.subheader("Horario Semanal")

        # Create schedule grid
        cols = st.columns(len(dates))

        # Spanish day abbreviations
        dias = {0: "Lun", 1: "Mar", 2: "Mié", 3: "Jue", 4: "Vie", 5: "Sáb", 6: "Dom"}

        for col_idx, (date, date_str) in enumerate(zip(dates, date_strings)):
            with cols[col_idx]:
                day_name = dias[date.weekday()]
                st.markdown(
                    f"<div style='background-color: {COLORS['primary_green']}; color: {COLORS['cream']}; "
                    f"padding: 8px; border-radius: 8px; text-align: center; margin-bottom: 8px;'>"
                    f"<b>{day_name}</b><br><span style='color: {COLORS['accent_gold']};'>{date.strftime('%d/%m')}</span></div>",
                    unsafe_allow_html=True
                )

                day_reservations = all_reservations.get(date_str, {})

                for time_slot in TIME_SLOTS:
                    if time_slot in day_reservations:
                        res = day_reservations[time_slot]
                        locked = "🔒" if res["password_hash"] else ""
                        st.markdown(
                            f"<div style='background-color: {COLORS['booked']}; "
                            f"border-left: 3px solid {COLORS['booked_border']}; "
                            f"padding: 6px 8px; margin: 3px 0; border-radius: 6px; font-size: 12px; "
                            f"box-shadow: 0 1px 3px rgba(0,0,0,0.08);'>"
                            f"<b style='color: {COLORS['terracotta']};'>{time_slot}</b> {locked}<br>"
                            f"<span style='color: #555;'>{res['player_name']}</span></div>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f"<div style='background-color: {COLORS['available']}; "
                            f"border-left: 3px solid {COLORS['available_border']}; "
                            f"padding: 6px 8px; margin: 3px 0; border-radius: 6px; font-size: 12px; "
                            f"box-shadow: 0 1px 3px rgba(0,0,0,0.08);'>"
                            f"<b style='color: {COLORS['primary_green']};'>{time_slot}</b><br>"
                            f"<span style='color: {COLORS['light_green']};'>Disponible</span></div>",
                            unsafe_allow_html=True
                        )

    # Tab 2: Book a Slot
    with tab2:
        st.subheader("Reservar Cancha")

        with st.form("booking_form"):
            col1, col2 = st.columns(2)

            with col1:
                selected_date = st.selectbox(
                    "Seleccionar Fecha",
                    options=date_strings,
                    format_func=lambda x: datetime.strptime(x, "%Y-%m-%d").strftime("%A, %d de %B")
                )

                # Show only available slots
                day_reservations = all_reservations.get(selected_date, {})
                available_slots = [t for t in TIME_SLOTS if t not in day_reservations]

                if available_slots:
                    selected_time = st.selectbox("Seleccionar Hora", options=available_slots)
                else:
                    st.warning("No hay horarios disponibles para esta fecha.")
                    selected_time = None

            with col2:
                player_name = st.text_input("Tu Nombre *", max_chars=50)
                phone = st.text_input("Teléfono (opcional)", max_chars=20)
                password = st.text_input(
                    "Contraseña (opcional - para cancelar)",
                    type="password",
                    help="Establece una contraseña si deseas poder cancelar esta reservación."
                )

            submitted = st.form_submit_button("Reservar", use_container_width=True)

            if submitted:
                if not player_name:
                    st.error("Por favor ingresa tu nombre.")
                elif not selected_time:
                    st.error("Por favor selecciona un horario disponible.")
                else:
                    success, message = create_reservation(
                        selected_date, selected_time, player_name, phone, password
                    )
                    if success:
                        st.success("¡Reservación creada exitosamente!")
                        if password:
                            st.info("Recuerda tu contraseña para cancelar esta reservación.")
                        st.rerun()
                    else:
                        st.error("Este horario ya está reservado.")

    # Tab 3: Cancel Booking
    with tab3:
        st.subheader("Cancelar Reservación")

        with st.form("cancel_form"):
            col1, col2 = st.columns(2)

            with col1:
                cancel_date = st.selectbox(
                    "Seleccionar Fecha",
                    options=date_strings,
                    format_func=lambda x: datetime.strptime(x, "%Y-%m-%d").strftime("%A, %d de %B"),
                    key="cancel_date"
                )

                # Show only booked slots
                day_reservations = all_reservations.get(cancel_date, {})
                booked_slots = list(day_reservations.keys())

                if booked_slots:
                    cancel_time = st.selectbox(
                        "Seleccionar Hora",
                        options=booked_slots,
                        format_func=lambda x: f"{x} - {day_reservations[x]['player_name']}" +
                                            (" 🔒" if day_reservations[x]['password_hash'] else ""),
                        key="cancel_time"
                    )
                else:
                    st.info("No hay reservaciones para cancelar en esta fecha.")
                    cancel_time = None

            with col2:
                cancel_password = st.text_input(
                    "Contraseña (si aplica)",
                    type="password",
                    help="Ingresa la contraseña si la reservación está protegida.",
                    key="cancel_password"
                )

            cancel_submitted = st.form_submit_button("Cancelar Reservación", use_container_width=True)

            if cancel_submitted:
                if not cancel_time:
                    st.error("Por favor selecciona una reservación para cancelar.")
                else:
                    success, message = cancel_reservation(cancel_date, cancel_time, cancel_password)
                    if success:
                        st.success("¡Reservación cancelada exitosamente!")
                        st.rerun()
                    else:
                        if "password" in message.lower():
                            st.error("Esta reservación está protegida. Por favor ingresa la contraseña correcta.")
                        elif "No reservation" in message:
                            st.error("No se encontró reservación para este horario.")
                        else:
                            st.error("Contraseña incorrecta.")

    # Footer
    st.markdown(f"""
        <div class="footer">
            <p>🌴 <span class="gold">{COURT_NAME}</span> 🌴</p>
            <p style="font-size: 0.8rem; margin-top: 0.5rem;">📍 {LOCATION} | Sistema de Reservaciones</p>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

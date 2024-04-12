import os
import urllib.parse as up
import sqlite3
from datetime import datetime
from services.mail import send_mail
from services.get_geolocation import get_geolocation
import psycopg2


def get_db_connection():
    up.uses_netloc.append("postgres")
    url = up.urlparse(os.environ["DATABASE_URL"])
    conn = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port,
    )
    return conn


def create_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS  users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL UNIQUE,
    password TEXT NOT NULL,
    send_notifications BOOLEAN NOT NULL DEFAULT false
    )
    """
    )

    conn.commit()
    cur.close()
    conn.close()


def add_to_database(name, email, user_id, password, send_notifications, user_ip):
    conn = get_db_connection()
    cursor = conn.cursor()
    already_exists = False
    isDataUpdated = True
    try:
        cursor.execute("SELECT * FROM users WHERE user_id=%s", (user_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            old_mail = existing_user[2]
            cursor.execute(
                """
                UPDATE users SET name=%s, email=%s, password=%s, send_notifications=%s
                WHERE id=%s
            """,
                (name, email, password, send_notifications, existing_user[0]),
            )
            already_exists = True

        else:
            cursor.execute(
                "INSERT INTO users (name, email, user_id, password, send_notifications) VALUES (%s, %s, %s, %s, %s)",
                (name, email, user_id, password, send_notifications),
            )

        conn.commit()
        print("User added/updated successfully")

    except sqlite3.Error as e:
        isDataUpdated = False
        conn.rollback()
    finally:
        conn.close()
        print(isDataUpdated, " ", already_exists)
        if isDataUpdated and already_exists == False:
            msg_subject = "New User Registered"
            msg_body = f"""
            Hi {name},

            Your details have been successfully registered! Here's a summary:

            - Name: {name}
            - Email: {email}
            - User ID: {user_id}
            - Send Notifications: {send_notifications}

            To update your details in the future, please fill out the registration form again.

            If you have any questions or concerns, feel free to contact us.

            Regards,
            Library Reissue Bot
            """
            send_mail(email, msg_subject, msg_body)

        elif isDataUpdated and already_exists == True:
            msg_subject = "User Details Updated"
            msg_body = f"""
            Hi {name},

            Your details have been successfully updated! Here's a summary:

            - Name: {name}
            - Email: {email}
            - User ID: {user_id}
            - Send Notifications: {send_notifications}

            The details were updated by IP: {user_ip} at {datetime.now()} {get_geolocation(user_ip)}.
            If you have any questions or concerns, feel free to contact us.

            Regards,
            Library Reissue Bot
            """
            send_mail(email, msg_subject, msg_body)


def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    return users

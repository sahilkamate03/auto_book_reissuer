import sqlite3
import os
from services.mail import send_mail

DATABASE = "./db/site.db"

def create_table():
    connection = sqlite3.connect(DATABASE)
    with open('./db/schema.sql') as f:
        connection.executescript(f.read())

def add_to_database(name, email, user_id, password, send_notifications, user_ip):
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()
    already_exists = False
    isDataUpdated = True
    try:
        cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            old_mail =existing_user[2]
            cursor.execute("""
                UPDATE users SET name=?, email=?, password=?, send_notifications=?
                WHERE id=?
            """, (name, email, password, send_notifications, existing_user[0]))
            already_exists = True

        else:
            cursor.execute("INSERT INTO users (name, email, user_id, password, send_notifications) VALUES (?, ?, ?, ?, ?)", (name, email, user_id, password, send_notifications))

        connection.commit()
        print("User added/updated successfully")

    except sqlite3.Error as e:
        isDataUpdated = False
        connection.rollback()
    finally:
        connection.close()
        print(isDataUpdated, " ", already_exists) 
        if (isDataUpdated and already_exists == False):
            msg_subject = "New User Registered"
            msg_body =  f"""
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

        elif (isDataUpdated and already_exists == True and old_mail != email):
            msg_subject = "User Details Updated"
            msg_body =  f"""
            Hi {name},

            Your details have been successfully updated! Here's a summary:

            - Name: {name}
            - Email: {email}
            - User ID: {user_id}
            - Send Notifications: {send_notifications}

            If you have any questions or concerns, feel free to contact us.

            Regards,
            Library Reissue Bot
            """
            # send_mail(email, msg_subject, msg_body)

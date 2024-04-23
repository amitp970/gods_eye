import tkinter as tk
from tkinter import messagebox
import json
from src.camera_server import CameraServer
import socket  


def submit_login_details():
    # Extracting the entries from the input fields
    username = username_entry.get()
    password = password_entry.get()
    location = location_entry.get()
    frame_rate = frame_rate_entry.get()
    
    # Simple validation example
    if not username or not password or not location or not frame_rate:
        messagebox.showerror("Error", "All fields are required!")
        return
    if not frame_rate.isdigit():
        messagebox.showerror("Error", "Frame rate must be a numeric value!")
        return
    
    # Close the window after successful submission
    root.destroy()

    CameraServer(location=location, frame_rate=frame_rate).start_server()

# Setting up the main window
root = tk.Tk()
root.title("Login Form")

# Labels and entries for the login form
tk.Label(root, text="Username:").grid(row=0, column=0)
username_entry = tk.Entry(root)
username_entry.grid(row=0, column=1)

tk.Label(root, text="Password:").grid(row=1, column=0)
password_entry = tk.Entry(root, show="*")
password_entry.grid(row=1, column=1)

tk.Label(root, text="Location:").grid(row=2, column=0)
location_entry = tk.Entry(root)
location_entry.grid(row=2, column=1)

tk.Label(root, text="Frame Rate (FPS):").grid(row=3, column=0)
frame_rate_entry = tk.Entry(root)
frame_rate_entry.grid(row=3, column=1)

# Button to submit the form
submit_button = tk.Button(root, text="Submit", command=submit_login_details)
submit_button.grid(row=4, column=1)

# Starting the GUI event loop
root.mainloop()

# Ensure the function and GUI event loop are commented out when not in direct execution mode
# submit_login_details()
# root.mainloop()

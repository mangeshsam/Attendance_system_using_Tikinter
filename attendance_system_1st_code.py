import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime
import os
import csv
from pymongo import MongoClient


# Sample student data
students = [
    {"id": 1, "name": "Anshul Nandanwar"},
    {"id": 2, "name": "Mangesh Sambare"},
    {"id": 3, "name": "Rashmit Barde"},
    {"id": 4, "name": "Bob Brown"}
]

# In-memory attendance records
attendance_records = []

def get_current_datetime():
    return datetime.now().strftime("%I:%M %p")  # 12-hour format with AM/PM

# Function to get today's date
def get_current_date():
    return datetime.now().strftime("%Y-%m-%d")

# Function to check if attendance is already recorded
def is_attendance_recorded(student_name, date):
    for record in attendance_records:
        if record['name'] == student_name and record['date'] == date:
            return True
    return False

# Function to mark attendance
def mark_attendance(student_id, student_name):
    date = get_current_date()
    time = get_current_datetime() 
    
    # Check if attendance is already marked
    if is_attendance_recorded(student_name, date):
        messagebox.showinfo("Attendance", f"Attendance for {student_name} already marked.")
        return

    # Add attendance record to the list
    attendance_records.append({"id": student_id, "name": student_name, "date": date,"time": time})
    messagebox.showinfo("Attendance", f"Attendance marked for {student_name} at {time}.")
    print(f"Attendance for {student_name} recorded in memory list at {time}.")


# Function to refresh the student list
def refresh_student_list():
    for widget in frame.winfo_children():
        widget.destroy()

    for student in students:
        student_frame = tk.Frame(frame,bg='#333333')
        student_frame.pack(fill="x", pady=5)

        name_label = tk.Label(student_frame, text=student["name"], font=("Arial", 12), width=20, anchor="w",fg='white',bg='#333333')
        name_label.pack(side="left")

        mark_button = tk.Button(student_frame, text="Mark Attendance", command=lambda s=student: mark_attendance(s["id"], s["name"]),fg='white',bg='#333333')
        mark_button.pack(side="right")

# Function to add a new student
def add_new_student():
    try:
        new_id = simpledialog.askinteger("Input", "Enter Student ID")
        new_name = simpledialog.askstring("Input", "Enter Student Name")

        if new_id and new_name:
            if any(student['id'] == new_id for student in students):
                messagebox.showerror("Error", "Student ID already exists!",fg='white',bg='#333333')
            else:
                students.append({"id": new_id, "name": new_name})
                refresh_student_list()
        else:
            messagebox.showwarning("Input Error", "Please provide valid Student ID and Name.",fg='white',bg='#333333')
    except Exception as e:
        messagebox.showerror("Error", f"Could not add new student: {e}")

# Tkinter application

root = tk.Tk()
root.title("Student Attendance System")
root.geometry("400x400")
root.configure(bg='#333333')

date_label = tk.Label(root, text=f"Date: {get_current_date()}", font=("Arial", 14),fg='white',bg='#333333')
date_label.pack(pady=19)

frame = tk.Frame(root,bg="#333333")
frame.pack(pady=10)

add_student_button = tk.Button(root, text="Add New Student", command=add_new_student,fg='white',bg='#333333')
add_student_button.pack(pady=10)

refresh_student_list()

# MongoDB initialization (place before the Tkinter mainloop or where appropriate)
uri = "mongodb+srv://mangeshsambare1:mangeshsambare123@cluster0.cw3cocl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
database = client['Attendance_sheet']
coll = database['Daily_Attendance']
# Start the Tkinter main loop
root.mainloop()

# After the Tkinter window closes, save the attendance records to MongoDB
if attendance_records:
    coll.insert_many(attendance_records)
    print("Attendance records saved to MongoDB.")
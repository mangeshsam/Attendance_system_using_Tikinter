import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from datetime import datetime
import os
import csv
import psycopg2

hostname = '127.0.0.1'
database = "postgres"
username = "postgres"
pwd = "admin123"
port = 5432
connection = None
cur = None

# Sample student data
students = []
# In-memory attendance records
attendance_records = []

csv_file_path = 'attendance_records.csv'

def get_db_connection():
    global connection, cur  # Declare as global so that we modify the global variables

    try:
        # Establishing the connection
        connection = psycopg2.connect(
            host=hostname,
            database=database,
            user=username,
            password=pwd,
            port=port
        )
        cur = connection.cursor()
        print("Connection to the PostgreSQL database established successfully.")

        # Create the students table
        cur.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id_student SERIAL PRIMARY KEY,  -- Use SERIAL for auto-increment
            name TEXT NOT NULL,
            batch TEXT NOT NULL
        );
        ''')

        # Create the attendance table
        cur.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id_student INTEGER,
            name TEXT,
            date DATE,  -- Use DATE type for date
            time TIME,  -- Use TIME type for time
            batch TEXT,
            status TEXT,
            FOREIGN KEY (id_student) REFERENCES students (id_student)
        );
        ''')
        
        connection.commit()
        print("Tables created successfully.")
        
    except Exception as e:
        print(f"An error occurred while connecting to the database: {e}")

def get_db_connection():
    global connection  # Ensure connection is available globally
    try:
        # Establish the connection if not already connected
        if connection is None:
            connection = psycopg2.connect(
                host=hostname,
                database=database,
                user=username,
                password=pwd,
                port=port
            )
            print("Connection to the PostgreSQL database established successfully.")
        return connection
    except Exception as e:
        print(f"An error occurred while connecting to the database: {e}")
        return None
    
def student_exists(student_id):
    """Check if the student exists in the students table."""
    conn = get_db_connection()
    try:
        if conn is not None:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM students WHERE id_student = %s", (student_id,))
                return cur.fetchone() is not None  # Returns True if student exists
        return False
    except Exception as e:
        print(f"An error occurred while checking student existence: {e}")
        if connection is not None:
            connection.rollback() 
        return False

def save_attendance_to_db(attendance_record):
    """Save attendance record to the PostgreSQL database."""
    try:
        # Ensure all fields are present
        required_keys = ['id_student', 'name', 'date', 'time', 'batch', 'status']
        if not all(key in attendance_record for key in required_keys):
            print(f"Error: Missing keys in attendance_record. Provided: {attendance_record}")
            return

        # Check if the student exists before saving attendance
        if not student_exists(attendance_record['id_student']):
            print(f"Error: Student with id {attendance_record['id_student']} does not exist in the students table.")
            return

        # Get the connection
        conn = get_db_connection()
        if conn is not None:
            with conn.cursor() as cur:
                # Validate and format the time if it's not empty
                time_value = None
                if attendance_record['time']:
                    try:
                        # Parse and validate time format 'HH:MM AM/PM'
                        parsed_time = datetime.strptime(attendance_record['time'], '%H:%M:%S')
                        # Convert to a 24-hour format for PostgreSQL TIME field
                        time_value = parsed_time.strftime('%H:%M:%S')
                    except ValueError:
                        print(f"Error: Invalid time format for {attendance_record['time']}. Expected format is 'HH:MM AM/PM'.")
                        return

                sql_query = """ 
                    INSERT INTO attendance (id_student, name, date, time, batch, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cur.execute(sql_query, (
                    attendance_record['id_student'], 
                    attendance_record['name'], 
                    attendance_record['date'],
                    time_value,  # Store the 12-hour time format in the database
                    attendance_record['batch'], 
                    attendance_record['status']
                ))

                conn.commit()
                print(f"Attendance for {attendance_record['name']} saved to the database.")
        
        else:
            print("Error: Database connection is not established.")
    except Exception as e:
        print(f"An error occurred while saving to the database: {e}")
        if connection is not None:
            connection.rollback() 


def save_attendance_to_db_for_student(new_id, new_name, batch):
    """Save student record to the PostgreSQL database."""
    try:
        if connection is not None:
            with connection.cursor() as cur:
                cur.execute("""
                    INSERT INTO students (id_student, name, batch)
                    VALUES (%s, %s, %s)
                """, (new_id, new_name, batch))
                
                connection.commit()
                print(f"Student {new_name} with ID {new_id} saved to the database.")
        else:
            print("Error: Database connection is not established.")
    except Exception as e:
        print(f"An error occurred while saving the student to the database: {e}")

# Initialize the database connection
get_db_connection()


def get_current_datetime():
    return datetime.now().strftime('%H:%M:%S')  # 12-hour format with AM/PM

def get_current_date():
    return datetime.now().strftime("%Y-%m-%d")

def is_attendance_recorded(student_name, date, batch):
    """Check if attendance has been marked for the student on a particular date and batch."""
    for record in attendance_records:
        if record['name'] == student_name and record['date'] == date and record['batch'] == batch:
            return True
    return False

def is_attendance_recorded_in_csv(student_name, date, batch):
    """Check if attendance has been marked in the CSV file for a student on a particular date and batch."""
    if os.path.exists(csv_file_path):
        with open(csv_file_path, mode="r", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['name'] == student_name and row['date'] == date and row['batch'] == batch:
                    return True
    return False

def save_attendance_to_csv(attendance_record):
    """Save attendance record to CSV file."""
    file_exists = os.path.exists(csv_file_path)
    with open(csv_file_path, mode='a', newline='') as file:
        fieldnames = ['id_student', 'name', 'date', 'time', 'batch', 'status']  # Updated here
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(attendance_record)

def load_students_from_csv():
    """Load student records from the CSV file."""
    if os.path.exists(csv_file_path):
        with open(csv_file_path, mode="r", newline="") as file:
            reader = csv.DictReader(file)
            loaded_students = set()  # Avoid duplicate names
            for row in reader:
                if row['name'] not in loaded_students:
                    students.append({"id_student": row['id_student'], "name": row['name'], "batch": row['batch']})  # Updated here
                    loaded_students.add(row['name'])

def add_student_to_csv(student_id, student_name, batch):
    """Add a new student to the CSV file."""
    file_exists = os.path.exists(csv_file_path)
    with open(csv_file_path, mode='a', newline='') as file:
        fieldnames = ['id_student', 'name', 'date', 'time', 'batch', 'status']  # Updated here
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({"id_student": student_id, "name": student_name, "date": "", "time": "", "batch": batch, "status": ""})  # Updated here

def mark_attendance(student_id, student_name, batch):
    """Mark attendance as 'Present' for a student."""
    date = get_current_date()
    time = get_current_datetime()

    if is_attendance_recorded(student_name, date, batch) or is_attendance_recorded_in_csv(student_name, date, batch):
        messagebox.showinfo("Attendance", f"Attendance for {student_name} already marked.")
        return

    attendance_record = {"id_student": student_id, "name": student_name, "date": date, "time": time, "batch": batch, "status": "Present"}  # Updated here
    attendance_records.append(attendance_record)

    save_attendance_to_csv(attendance_record)
    save_attendance_to_db(attendance_record)

    messagebox.showinfo("Attendance", f"Attendance marked as 'Present' for {student_name} at {time}.")
    print(f"Attendance for {student_name} recorded as Present at {time}.")

def mark_absent_students(batch):
    """Mark students as 'Absent' for the selected batch if attendance was not marked."""
    date = get_current_date()
    time = get_current_datetime()
    for student in students:
        if student['batch'] == batch:  # Mark only students in the selected batch
            if not is_attendance_recorded(student['name'], date, batch) and not is_attendance_recorded_in_csv(student['name'], date, batch):
                # Mark as absent
                attendance_record = {"id_student": student['id_student'], "name": student['name'], "date": date, "time":time, "batch": batch, "status": "Absent"}  # Updated here
                attendance_records.append(attendance_record)
                save_attendance_to_csv(attendance_record)
                save_attendance_to_db(attendance_record)
                print(f"Attendance for {student['name']} recorded as Absent.")

# Remaining code...
def refresh_student_list(batch, window):
    """Refresh the list of students for the selected batch."""
    # Clear current window widgets
    for widget in window.winfo_children():
        widget.destroy()

    # Create a canvas widget and scrollbar
    canvas = tk.Canvas(window, bg='#ffffb3')
    scrollbar = tk.Scrollbar(window, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg='#ffffb3')

    # Configure the scrollable frame to expand as needed
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    # Create a window inside the canvas
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    # Configure canvas scrolling
    canvas.configure(yscrollcommand=scrollbar.set)

    # Place the canvas and scrollbar in the window
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def right_click_menu(event, student):
        """Handle right-click event to mark attendance."""
        menu = tk.Menu(root, tearoff=0)
        menu.add_command(label="Mark Attendance", command=lambda: mark_attendance(student['id_student'], student['name'], student['batch']))
        menu.tk_popup(event.x_root, event.y_root)

    # Display list of students for the selected batch in the scrollable frame
    for student in students:
        if student["batch"] == batch:
            student_frame = tk.Frame(scrollable_frame, bg='#ffffb3')
            student_frame.pack(fill="x", pady=5)

            name_label = tk.Label(student_frame, text=student["name"], font=("Times New Roman", 12), width=20, anchor="w", fg='purple', bg='#ffffb3')
            name_label.pack(side="left", padx=15)

            # Bind right-click to the label
            name_label.bind("<Button-3>", lambda event, s=student: right_click_menu(event, s))

            # Check if attendance already marked and disable the button accordingly
            is_present = is_attendance_recorded(student["name"], get_current_date(), batch) or is_attendance_recorded_in_csv(student["name"], get_current_date(), batch)
            mark_button = tk.Button(student_frame, 
                                    text="Mark Attendance", 
                                    state="disabled" if is_present else "normal", 
                                    command=lambda s=student: mark_attendance(s["id_student"], s["name"], s["batch"]), font=("Times New Roman", 12), fg='white', bg='purple')  # Updated here
            mark_button.pack(side="right", padx=15)

    # Keep the "Add New Student" button at the bottom
    add_student_button = tk.Button(scrollable_frame, text="Add New Student", command=lambda: add_new_student_in_batch(batch, window), font=("Times New Roman", 12), fg='white', bg='purple')
    add_student_button.pack(pady=10)

def open_student_list_window(batch):
    """Open a new window to display students in the selected batch."""
    student_window = tk.Toplevel(root)
    student_window.title(f"{batch} Student List")
    student_window.geometry("400x450")
    student_window.configure(bg='#ffffb3')

    tk.Label(student_window, text=f"Students in {batch} Batch", font=("Times New Roman", 12), fg='white',bg="#ffffb3").pack(pady=10)

    refresh_student_list(batch, student_window)

    # Hide the main window until the second window is closed
    root.withdraw()

    # Bind close event of the student window to show main window again
    student_window.protocol("WM_DELETE_WINDOW", lambda: on_close_student_window(student_window,batch))

def on_close_student_window(student_window,batch):
    """Handle closing of the student window and return to the main window."""
    messagebox.showinfo("Attendance Status", f"The following students from batch {batch} have been marked 'Absent' as they were not marked 'Present'.")
    mark_absent_students(batch)

  # Show a message indicating absent students have been marked    root.deiconify()

    root.deiconify()
    student_window.destroy()

def add_new_student_in_batch(batch, window):
    input_window = tk.Toplevel(root)
    input_window.title("Add New Student")
    input_window.geometry("300x300")
    input_window.configure(bg='#ffffb3')

    name_label = tk.Label(input_window, text="Enter Student Name:", font=("Times New Roman", 12), bg='#ffffb3')
    name_label.pack(pady=10)

    name_entry = tk.Entry(input_window, font=("Times New Roman", 12))
    name_entry.pack(pady=5)

    id_label = tk.Label(input_window, text="Enter Student ID:", font=("Times New Roman", 12), bg='#ffffb3')
    id_label.pack(pady=10)

    id_entry = tk.Entry(input_window, font=("Times New Roman", 12))
    id_entry.pack(pady=5)

    def submit_student():
        try:
            new_id = int(id_entry.get())  # Get and convert student ID from entry
            new_name = name_entry.get().strip()  # Get student name from entry

            if new_id and new_name:
                if any(student['id_student'] == new_id for student in students):
                    messagebox.showerror("Error", "Student ID already exists in memory!")
                    return

                if os.path.exists(csv_file_path):
                    with open(csv_file_path, mode="r", newline="") as file:
                        reader = csv.DictReader(file)
                        for row in reader:
                            if int(row['id_student']) == new_id:
                                messagebox.showerror("Error", "Student ID already exists in CSV file!")
                                return

                students.append({"id_student": new_id, "name": new_name, "batch": batch})
                add_student_to_csv(new_id, new_name, batch)
                save_attendance_to_db_for_student(new_id, new_name, batch)
                refresh_student_list(batch, window)
                input_window.destroy()
            else:
                messagebox.showwarning("Input Error", "Please provide valid Student ID and Name.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not add new student: {e}")

    submit_button = tk.Button(input_window, text="Submit", command=submit_student, font=("Times New Roman", 12), fg='white', bg='purple')
    submit_button.pack(pady=20)

def change_batch(selected_batch):
    """Change to the selected batch and open the corresponding student list window."""
    batch_var.set(selected_batch)
    open_student_list_window(selected_batch)

def on_close_main_window():
    """Function to close the entire program when the main window is closed."""
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        # Mark absent students for the selected batch before closing
        selected_batch = batch_var.get()
        mark_absent_students(selected_batch)
        print("Attendance records saved to CSV file.")
        print("Attendance records saved to PostgreSQL file.")

        root.quit()  # Terminate the mainloop and close the program

def on_closing():
    """Handle closing the main window."""
    if connection:
        connection.close()  # Close the database connection
    root.destroy()


# Tkinter application
root = tk.Tk()
root.title("Student Attendance System (Affordable.Ai)")
root.geometry("444x600")
root.configure(background='#ffffb3')
label = tk.Label(root, text='Affordable.Ai',font=("Times New Roman", 26), fg='purple',bg='#ffffb3')
label.pack(pady=20)


# Bind the close event of the main window to the `on_close_main_window` function
root.protocol("WM_DELETE_WINDOW", on_close_main_window)

date_label = tk.Label(root, text=f"Date: {get_current_date()}", font=("Times New Roman", 14), fg='purple', bg='#ffffb3')
date_label.pack()

batch_var = tk.StringVar()
Date_label2 = tk.Label(root, text=f"SELECT BATCH", font=("Times New Roman", 12), fg='purple', bg='#ffffb3')
Date_label2.pack()

button_frame = tk.Frame(root, bg='#ffffb3')
button_frame.pack(pady=10)

morning_button = tk.Button(button_frame, text="Morning Batch", command=lambda: change_batch("Morning"), font=("Times New Roman", 12),width=18, height=1, fg='white', bg='purple')
morning_button.pack(padx=10, pady=8)

afternoon_button = tk.Button(button_frame, text="Afternoon Batch", command=lambda: change_batch("Afternoon"), font=("Times New Roman", 12) ,width=18, height=1,fg='white', bg='purple')
afternoon_button.pack(padx=10, pady=8)

evening_button = tk.Button(button_frame, text="Evening Batch", command=lambda: change_batch("Evening"), font=("Times New Roman", 12) ,width=18, height=1, fg='white', bg='purple')
evening_button.pack(padx=10, pady=8)

interview_button = tk.Button(button_frame, text="Interview Batch", command=lambda: change_batch("Interview"), font=("Times New Roman", 12) ,width=18, height=1,fg='white', bg='purple')
interview_button.pack(padx=10, pady=8)

group_discussion_button = tk.Button(button_frame, text="Group Discussion Batch", command=lambda: change_batch("Group Discussion"), font=("Times New Roman", 12) ,width=18, height=1, fg='white', bg='purple')
group_discussion_button.pack(padx=10, pady=8)

frame = tk.Frame(root, bg="purple")
frame.pack(pady=10)



load_students_from_csv()

connection = get_db_connection()

# Tkinter main loop
root.mainloop()

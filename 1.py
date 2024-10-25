import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from datetime import datetime
import os
import csv
import psycopg2

hostname = 'localhost'
database = "postgres"
username = "postgres"
port = 5432
pwd = "mangesh123"
connection = None
cur = None

# Sample student data
students = []
# In-memory attendance records
attendance_records = []

csv_file_path = 'attendance_records.csv'
fieldnames = ['id_student', 'name', 'batch', 'college_name', 'mobile_no', 'email_id', 'address', 'date', 'time', 'status']  # Updated here

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
        batch TEXT NOT NULL,
        college_name TEXT,
        mobile_no TEXT,
        email_id TEXT,
        address TEXT
        );
        ''')

        # Create the attendance table
        cur.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id_student INTEGER,
            name TEXT,
            batch TEXT,
            college_name TEXT,
            mobile_no TEXT,
            email_id TEXT,
            address TEXT,
            date DATE,  -- Use DATE type for date
            time TIME,  -- Use TIME type for time
            status TEXT,
            FOREIGN KEY (id_student) REFERENCES students (id_student)
        );
        ''')
        
        connection.commit()
        print("Tables created successfully.")
        
    except Exception as e:
        print(f"An error occurred while connecting to the database: {e}")


get_db_connection()
#create_tables()  # Create the tables if they don't exist

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
        required_keys = ['id_student', 'name', 'batch', 'college_name', 'mobile_no', 'email_id', 'address', 'date', 'time', 'status']
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
                    INSERT INTO attendance (id_student,name, batch, college_name, mobile_no, email_id, address, date, time, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cur.execute(sql_query, (
                    attendance_record['id_student'], 
                    attendance_record['name'],
                    attendance_record['batch'],
                    attendance_record['college_name'],
                    attendance_record['mobile_no'],
                    attendance_record['email_id'],
                    attendance_record['address'], 
                    attendance_record['date'],
                    time_value,  # Store the 12-hour time format in the database 
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


def save_attendance_to_db_for_student(id_student,name, batch, college_name, mobile_no, email_id, address):
    """Save student record to the PostgreSQL database."""
    try:
        if connection is not None:
            with connection.cursor() as cur:
                cur.execute("""
                    INSERT INTO students (id_student,name, batch, college_name, mobile_no, email_id, address)
                    VALUES (%s, %s, %s,%s, %s, %s,%s)
                """, (id_student,name, batch, college_name, mobile_no, email_id, address))
                
                connection.commit()
                print(f"Student {name} with ID {id_student} saved to the database.")
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
        fieldnames = ['id_student', 'name', 'batch', 'college_name', 'mobile_no', 'email_id', 'address', 'date', 'time', 'status']  # Updated here
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
                    students.append({"id_student": row['id_student'], "name": row['name'], "batch": row['batch'],"college_name":row["college_name"],"mobile_no":row['mobile_no'],'email_id':row['email_id'],'address':row['address']})  # Updated here
                    loaded_students.add(row['name'])

def add_student_to_csv(student_id, student_name, batch, college_name, mobile_no, email_id, address):
    """Add a new student to the CSV file."""
    file_exists = os.path.exists(csv_file_path)
    with open(csv_file_path, mode='a', newline='') as file:
        fieldnames = ['id_student', 'name', 'batch', 'college_name', 'mobile_no', 'email_id', 'address', 'date', 'time', 'status']  # Updated here
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        writer.writerow({"id_student": student_id, "name": student_name,"college_name":college_name,"mobile_no":mobile_no,"email_id":email_id,"address":address, "date": "", "time": "", "batch": batch, "status": ""})  # Updated here
def show_auto_close_message(title, message, duration=2000):
    """Create a custom message window that closes automatically after a duration."""
    # Create a new Toplevel window
    message_window = tk.Toplevel(root)
    message_window.title(title)
    message_window.configure(bg='#ffffb3')

    # Set a fixed size for the window
    window_width = 300  # You can adjust this value as needed
    window_height = 100  # You can adjust this value as needed
    message_window.geometry(f"{window_width}x{window_height}")

    # Create a frame for the label
    frame = tk.Frame(message_window, bg='#ffffb3')
    frame.pack(padx=10, pady=10)

    # Create a label to display the message
    label = tk.Label(frame, text=message, font=("Times New Roman", 14), bg='#ffffb3', fg='purple', wraplength=window_width - 40)
    label.pack()

    # Center the window on the screen
    screen_width = message_window.winfo_screenwidth()
    screen_height = message_window.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    message_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Close the window after the specified duration
    message_window.after(duration, message_window.destroy)

def mark_attendance(student_id, student_name, batch,college_name, mobile_no, email_id, address):
    """Mark attendance as 'Present' for a student."""
    date = get_current_date()
    time = get_current_datetime()

    if is_attendance_recorded(student_name, date, batch) or is_attendance_recorded_in_csv(student_name, date, batch):
        messagebox=f"  Attendance for {student_name} already marked.  "
        show_auto_close_message("Attendance", messagebox)

        return

    attendance_record = {"id_student": student_id, "name": student_name, "batch": batch, "college_name": college_name, "mobile_no": mobile_no, "email_id": email_id, "address": address, "date": date, "time": time, "status": "Present"}
    attendance_records.append(attendance_record)

    save_attendance_to_csv(attendance_record)
    save_attendance_to_db(attendance_record)

    message1 = f"  Attendance marked as 'Present' for {student_name} at {time}.  "
    show_auto_close_message("Attendance", message1)

    print(f"Attendance for {student_name} recorded as Present at {time}.")

def mark_absent_students(batch):
    """Mark students as 'Absent' for the selected batch if attendance was not marked."""
    date = get_current_date()
    time = get_current_datetime()
    for student in students:
        if student['batch'] == batch:  # Mark only students in the selected batch
            if not is_attendance_recorded(student['name'], date, batch) and not is_attendance_recorded_in_csv(student['name'], date, batch):
                attendance_record = {"id_student": student['id_student'], "name": student['name'], "batch": student['batch'], "college_name": student["college_name"], "mobile_no": student['mobile_no'], "email_id": student['email_id'], "address": student['address'], "date": date, "time": time, "status": "Absent"}
                attendance_records.append(attendance_record)

                save_attendance_to_csv(attendance_record)
                save_attendance_to_db(attendance_record)

                print(f"Attendance for {student['name']} recorded as Absent.")
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
            student_frame.pack(fill="x", pady=5, padx=10, expand=True)

            name_label = tk.Label(student_frame, text=student["name"], font=("Times New Roman", 15), width=20, anchor="w", fg='purple', bg='#ffffb3')
            name_label.pack(side="left", padx=15, pady=11)

            # Bind right-click to the label
            name_label.bind("<Button-3>", lambda event, s=student: right_click_menu(event, s))

            # Check if attendance already marked and disable the button accordingly
            is_present = is_attendance_recorded(student["name"], get_current_date(), batch) or is_attendance_recorded_in_csv(student["name"], get_current_date(), batch)
            mark_button = tk.Button(student_frame, 
                                    text="Mark Attendance", 
                                    state="disabled" if is_present else "normal", 
                                    command=lambda s=student: mark_attendance(s["id_student"], s["name"], s["batch"],s["college_name"],s["mobile_no"],s["email_id"],s["address"]), font=("Times New Roman", 14),width=16, height=1, fg='white', bg='purple')
            mark_button.pack(side="right", padx=8, pady=9)

            # Add Update button for changing attendance if marked incorrectly
            update_button = tk.Button(student_frame, 
                                      text="Update Attendance", 
                                      command=lambda s=student: update_attendance(s), 
                                      font=("Times New Roman", 14),width=16, height=1, fg='white', bg='purple')
            update_button.pack(side="right",padx=8, pady=9)

    # Keep the "Add New Student" button at the bottom
    add_student_button = tk.Button(scrollable_frame, text="Add New Student", command=lambda: add_new_student_in_batch(batch, window), font=("Times New Roman", 14),width=18, height=1, fg='white', bg='purple')
    add_student_button.pack(pady=10)

def update_attendance(student):
    """Toggle attendance between 'Present' and 'Absent'."""
    date = get_current_date()
    time = get_current_datetime()
    batch = student['batch']
    
    # Check if the student's attendance record exists for today
    attendance_found = False
    for record in attendance_records:
        if record['id_student'] == student['id_student'] and record['date'] == date and record['batch'] == batch:
            # Toggle the status
            new_status = 'Absent' if record['status'] == 'Present' else 'Present'
            record['status'] = new_status
            record['time'] = time  # Update time for the current attendance change
            
            # Save updated record to CSV and DB
            save_attendance_to_csv(record)
            save_attendance_to_db(record)
            messagebox=f"  Attendance for {student['name']} updated to '{new_status}'.  "
            show_auto_close_message("Attendance Update", messagebox)

            attendance_found = True
            return

    # If no existing record was found, create a new one
    if not attendance_found:
        new_record = {
            "id_student": student['id_student'],
            "name": student['name'],
            "batch": student['batch'],
            "college_name": student['college_name'],
            "mobile_no": student['mobile_no'],
            "email_id": student['email_id'],
            "address": student['address'],
            "date": date,
            "time": time,
            "status": "Present"  # Default to 'Present' when creating a new record
        }
        
        attendance_records.append(new_record)  # Add new record to the list
        save_attendance_to_csv(new_record)     # Save to CSV
        save_attendance_to_db(new_record)       # Save to DB
        message2= f"  Attendance for {student['name']} marked as 'Present'.  "
        show_auto_close_message("Attendance Update", message2)


def open_student_list_window(batch):
    """Open a new window to display students in the selected batch."""
    student_window = tk.Toplevel(root)
    student_window.title(f"{batch} Student List")
    student_window.geometry("670x750")
    student_window.configure(bg='#ffffb3')

    tk.Label(student_window, text=f"Students in {batch} Batch", font=("Times New Roman", 24), fg='purple',bg="#ffffb3").pack(padx=10, pady=14)

    refresh_student_list(batch, student_window)

    # Hide the main window until the second window is closed
    root.withdraw()

    # Bind close event of the student window to show main window again
    student_window.protocol("WM_DELETE_WINDOW", lambda: on_close_student_window(student_window,batch))

def on_close_student_window(student_window,batch):
    """Handle closing of the student window and return to the main window."""
    messagebox.showinfo("Attendance Status", f"Students in batch {batch} not marking attendance are 'Absent'.")
    mark_absent_students(batch)

  # Show a message indicating absent students have been marked    root.deiconify()

    root.deiconify()
    student_window.destroy()

def add_new_student_in_batch(batch, window):
    input_window = tk.Toplevel(root)
    input_window.title("Add New Student")
    input_window.geometry("450x600")
    input_window.configure(bg='#ffffb3')

    id_label = tk.Label(input_window, text="Enter Student ID:", font=("Times New Roman", 16), bg='#ffffb3')
    id_label.pack(pady=10)

    id_entry = tk.Entry(input_window, font=("Times New Roman", 16))
    id_entry.pack(pady=5)

    name_label = tk.Label(input_window, text="Enter Student Name:", font=("Times New Roman", 16), bg='#ffffb3')
    name_label.pack(pady=10)

    name_entry = tk.Entry(input_window, font=("Times New Roman", 16))
    name_entry.pack(pady=5)

    college_label = tk.Label(input_window, text="Enter College Name:", font=("Times New Roman", 16), bg='#ffffb3')
    college_label.pack(pady=10)

    college_entry = tk.Entry(input_window, font=("Times New Roman", 16))
    college_entry.pack(pady=5)

    email_label = tk.Label(input_window, text="Enter Email ID:", font=("Times New Roman", 16), bg='#ffffb3')
    email_label.pack(pady=10)

    email_entry = tk.Entry(input_window, font=("Times New Roman", 16))
    email_entry.pack(pady=5)

    mobile_label = tk.Label(input_window, text="Enter Mobile Number:", font=("Times New Roman", 16), bg='#ffffb3')
    mobile_label.pack(pady=10)

    mobile_entry = tk.Entry(input_window, font=("Times New Roman", 16))
    mobile_entry.pack(pady=5)

    address_label = tk.Label(input_window, text="Enter Address:", font=("Times New Roman", 16), bg='#ffffb3')
    address_label.pack(pady=10)

    address_entry = tk.Entry(input_window, font=("Times New Roman", 16))
    address_entry.pack(pady=5)

    def submit_student():
        try:
            new_id = int(id_entry.get())  # Get and convert student ID from entry
            new_name = name_entry.get().strip()  # Get student name from entry
            college_name = college_entry.get().strip()  # Get college name from entry
            email_id = email_entry.get().strip()  # Get email ID from entry
            mobile_no = mobile_entry.get().strip()  # Get mobile number from entry
            address = address_entry.get().strip()  # Get address from entry

            if new_id and new_name and college_name and email_id and mobile_no and address:
                # Check if student ID already exists in memory or in the CSV
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

                # Add new student to in-memory list and save to CSV and database
                students.append({
                    "id_student": new_id, 
                    "name": new_name, 
                    "batch": batch, 
                    "college_name": college_name,
                    "mobile_no": mobile_no,
                    "email_id": email_id,
                    "address": address
                })

                add_student_to_csv(new_id, new_name, batch, college_name, mobile_no, email_id, address)
                save_attendance_to_db_for_student(new_id, new_name, batch, college_name, mobile_no, email_id, address)
                refresh_student_list(batch, window)
                input_window.destroy()
            else:
                messagebox.showwarning("Input Error", "Please provide valid inputs for all fields.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not add new student: {e}")

    submit_button = tk.Button(input_window, text="Submit", command=submit_student, font=("Times New Roman", 18),width=20, height=1, fg='white', bg='purple')
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
root.geometry("600x800")
root.configure(background='#ffffb3')
label = tk.Label(root, text='Affordable.Ai',font=("Times New Roman", 38), fg='purple',bg='#ffffb3')
label.pack(pady=22)


# Bind the close event of the main window to the `on_close_main_window` function
root.protocol("WM_DELETE_WINDOW", on_close_main_window)

date_label = tk.Label(root, text=f"Date: {get_current_date()}", font=("Times New Roman", 20), fg='purple', bg='#ffffb3')
date_label.pack(pady=10)

batch_var = tk.StringVar()
Date_label2 = tk.Label(root, text=f"SELECT BATCH", font=("Times New Roman", 18), fg='purple', bg='#ffffb3')
Date_label2.pack(pady=8)

button_frame = tk.Frame(root, bg='#ffffb3')
button_frame.pack(pady=10)

morning_button = tk.Button(button_frame, text="Morning Batch", command=lambda: change_batch("Morning"), font=("Times New Roman", 16),width=20, height=1, fg='white', bg='purple')
morning_button.pack(padx=10, pady=14)

afternoon_button = tk.Button(button_frame, text="Afternoon Batch", command=lambda: change_batch("Afternoon"), font=("Times New Roman", 16) ,width=20, height=1,fg='white', bg='purple')
afternoon_button.pack(padx=10, pady=14)

evening_button = tk.Button(button_frame, text="Evening Batch", command=lambda: change_batch("Evening"), font=("Times New Roman", 16) ,width=20, height=1, fg='white', bg='purple')
evening_button.pack(padx=10, pady=14)

interview_button = tk.Button(button_frame, text="Interview Batch", command=lambda: change_batch("Interview"), font=("Times New Roman", 16) ,width=20, height=1,fg='white', bg='purple')
interview_button.pack(padx=10, pady=14)

group_discussion_button = tk.Button(button_frame, text="Group Discussion Batch", command=lambda: change_batch("Group Discussion"), font=("Times New Roman", 16) ,width=20, height=1, fg='white', bg='purple')
group_discussion_button.pack(padx=10, pady=14)

frame = tk.Frame(root, bg="purple")
frame.pack(pady=10)



load_students_from_csv()

connection = get_db_connection()

# Tkinter main loop
root.mainloop()
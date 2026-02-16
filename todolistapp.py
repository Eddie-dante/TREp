import tkinter as tk
from tkinter import messagebox

# Create main window
root = tk.Tk()
root.title("Simple To-Do List")
root.geometry("350x400")

# Function to add task
def add_task():
    task = task_entry.get()
    if task.strip() == "":
        messagebox.showwarning("Warning", "Please enter a task!")
        return
    task_listbox.insert(tk.END, task)
    task_entry.delete(0, tk.END)

# Function to delete selected task
def delete_task():
    try:
        selected_task = task_listbox.curselection()
        task_listbox.delete(selected_task)
    except:
        messagebox.showwarning("Warning", "Please select a task to delete!")

# Title Label
title_label = tk.Label(root, text="To-Do List", font=("Arial", 18))
title_label.pack(pady=10)

# Entry field
task_entry = tk.Entry(root, width=25, font=("Arial", 14))
task_entry.pack(pady=10)

# Add Button
add_button = tk.Button(root, text="Add Task", width=15, command=add_task)
add_button.pack(pady=5)

# Delete Button
delete_button = tk.Button(root, text="Delete Task", width=15, command=delete_task)
delete_button.pack(pady=5)

# Listbox
task_listbox = tk.Listbox(root, width=30, height=10, font=("Arial", 12))
task_listbox.pack(pady=20)

# Run the app
root.mainloop()

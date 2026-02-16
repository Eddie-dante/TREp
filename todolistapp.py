import streamlit as st

st.title("📝 To-Do List App")

# Initialize session state
if "tasks" not in st.session_state:
    st.session_state.tasks = []

# Add task
new_task = st.text_input("Enter a task")

if st.button("Add Task"):
    if new_task.strip() != "":
        st.session_state.tasks.append(new_task)
    else:
        st.warning("Please enter a task!")

# Display tasks
st.subheader("Your Tasks")

for i, task in enumerate(st.session_state.tasks):
    col1, col2 = st.columns([4, 1])
    col1.write(task)
    if col2.button("Delete", key=i):
        st.session_state.tasks.pop(i)
        st.rerun()

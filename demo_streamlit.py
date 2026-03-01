import streamlit as st

# Runs EVERY time user submits a message
print("Script is running...")  

if "count" not in st.session_state:
    st.session_state.count = 0

if "messages" not in st.session_state:
    st.session_state.messages = []

st.session_state.count += 1
st.write(f"Script has run {st.session_state.count} times")



user_input = st.chat_input("Say something")

if user_input:
    st.session_state.messages.append(f"You said: {user_input}")
   
# Render all past messages on every rerun
for msg in st.session_state.messages:
    st.write(msg)
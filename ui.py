import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.title("💬 Memory Chat API")

# --- Thread Management ---
st.subheader("Thread Management")

thread_id = st.text_input("Thread ID", placeholder="e.g. thread1")

col1, col2 = st.columns(2)

with col1:
    if st.button("Create Thread"):
        if thread_id:
            res = requests.post(f"{API_URL}/threads/{thread_id}")
            if res.status_code == 200:
                st.success(f"Thread '{thread_id}' created!")
            else:
                st.error(res.json().get("detail", "Something went wrong"))
        else:
            st.warning("Please enter a thread ID first")

with col2:
    if st.button("Get Thread"):
        if thread_id:
            res = requests.get(f"{API_URL}/threads/{thread_id}")
            if res.status_code == 200:
                st.session_state.active_thread = thread_id
                st.session_state.messages = res.json().get("messages", [])
                st.success(f"Loaded thread '{thread_id}'!")
            else:
                st.error(res.json().get("detail", "Thread not found"))
        else:
            st.warning("Please enter a thread ID first")

st.divider()

# --- Active thread indicator ---
if "active_thread" in st.session_state:
    st.info(f"📂 Active thread: **{st.session_state.active_thread}**")

    # --- Show conversation history ---
    st.subheader("Conversation History")
    if st.session_state.messages:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"**🧑 You:** {msg['content']}")
            else:
                st.markdown(f"**🤖 AI:** {msg['content']}")
    else:
        st.info("No messages yet in this thread")

    st.divider()

    # --- Chat section ---
    st.subheader("Send a Message")
    user_message = st.text_input("Your message", placeholder="Type something...")

    if st.button("Send"):
        if user_message:
            res = requests.post(
                f"{API_URL}/threads/{st.session_state.active_thread}/messages",
                json={"message": user_message}
            )
            if res.status_code == 200:
                data = res.json()
                # update conversation in session
                st.session_state.messages.append({"role": "user", "content": user_message})
                st.session_state.messages.append({"role": "assistant", "content": data["reply"]})
                st.rerun()
            else:
                st.error(res.json().get("detail", "Something went wrong"))
        else:
            st.warning("Please type a message first")

else:
    st.info("👆 Create a new thread or enter an existing thread ID and click Get Thread to start chatting!")
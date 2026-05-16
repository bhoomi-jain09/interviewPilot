import streamlit as st
from langgraph.errors import GraphInterrupt
from backend import workflow
import uuid
from langgraph.types import Command

st.title("AI Interview Assistant 🎤")
st.header("Best of Luck")

# --- session init (use only nested 'state' dict for shared workflow state) ---
if "state" not in st.session_state:
    st.session_state.state = {}
if "started" not in st.session_state:
    st.session_state.started = False
if "thread_id" not in st.session_state:
    st.session_state.thread_id=str(uuid.uuid4())
if "input_key" not in st.session_state:
    st.session_state.input_key = 0

# UI controls
role = st.selectbox("Select your role", ["Ai engineer", "Data Analyst", "Python Developer", "Frontend developer", "Backend developer", "Full stack developer"])
difficulty = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"])
number = st.selectbox("How many questions do you want to generate", [10, 15, 20, 25])

if st.button("Start interview"):
    st.session_state.started = True
    # initialize nested state; feedback starts as None
    st.session_state.state = {
        "role": role,
        "difficulty": difficulty,
        "number": number,
        "step": 0,
        "question": "",
        "answer": "",
        "feedback": None,
    }
    try:
        result = workflow.invoke(st.session_state.state, config={"configurable": {"thread_id":st.session_state.thread_id}})
        st.session_state.state.update(result)
        if "question" in result:
            st.session_state.state["question"] = result["question"]
    except GraphInterrupt as e:
            interrupt_data = e.args[0]

            st.session_state.state.update(interrupt_data)

            if "question" in interrupt_data:
                st.session_state.question = interrupt_data["question"]
    st.rerun()

if st.session_state.started:
    st.subheader(f"Question: {st.session_state.state.get('step', 0)} of {st.session_state.state.get('number', number)}")
    st.write(st.session_state.state.get("question", ""))  # full nested state for debugging
    feedback_val = st.session_state.state.get("feedback")
    if feedback_val is not None:
        st.success(str(feedback_val))
    with st.form("answer_form"):
        answer = st.text_area(
            "Your Answer",
            key=f"answer_input_{st.session_state.input_key}" 
        )
        submitted = st.form_submit_button("Submit")

        if submitted:
            # write answer to nested state, reset feedback to None before invoking
            st.session_state.state["answer"] = answer
            if not answer.strip():
                st.warning("Please write an answer before submitting.")
            else:
                st.session_state.input_key += 1
            st.session_state.state["feedback"] = None
          

            try:
                result = workflow.invoke(Command(resume=answer), config={"configurable": {"thread_id": st.session_state.thread_id}})
                st.write("RAW RESULT FROM WORKFLOW →", result)
                st.session_state.state.update(result)
                # make sure feedback is present if returned
                if "feedback" in result:
                    st.session_state.state["feedback"] = result["feedback"]
            except GraphInterrupt as e:
                interrupt_data = e.args[0]

                st.session_state.state.update(interrupt_data)

                if "question" in interrupt_data:
                    st.session_state.question = interrupt_data["question"]
                graph_state = workflow.get_state(
                    config={"configurable": {"thread_id": st.session_state.thread_id}}
                )
                st.session_state.state["feedback"] = graph_state.values.get("feedback", "")
 
            # remove transient top-level answer key if set, then rerun to refresh UI
            st.rerun()
st.success("your interview is completed successfully /n May you have a great future.")
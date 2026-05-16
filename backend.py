from langgraph.graph import StateGraph,START,END
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from typing import TypedDict
import streamlit as st
from langgraph.types import interrupt
from langgraph.errors import GraphInterrupt
from langgraph.checkpoint.memory import InMemorySaver
load_dotenv()
model=ChatGroq(model="llama-3.1-8b-instant")

class chatschema(TypedDict):
    role:str
    difficulty:str
    number:int
    question:str
    answer:str
    feedback:str
    step:int


def generate_questions(state:chatschema):
    prompt = f"""
    You are a technical interviewer.
    Ask ONE interview question.

    Role: {state['role']}
    Difficulty: {state['difficulty']}
    Question number: {state['step']} of {state['number']}

    Only output the question text.
    """
    res=model.invoke(prompt).content
    return({
    "question": res,
    "step":state['step']+1
})

def wait_for_answer(state: chatschema):
    answer = interrupt({
        "question": state["question"]
    })
    return {"answer": answer}


def feedback(state: chatschema):
    # First give feedback on previous answer (if not first question)
    if state.get("answer"):
        feedback_prompt = f"""
        Question: {state['question']}
        User answer: {state['answer']}
        Give short constructive feedback.
        """
        feedback_response = model.invoke(feedback_prompt)
        feedback_text = feedback_response.content
    else:
        feedback_text = None
    return {
        "feedback": feedback_text}

def should_continue(state:chatschema):
    if state["step"]>=state["number"]:
        return "END"
    return "continue"

#user_answer = st.text_input("Your Answer")

checkpointer=InMemorySaver()
graph=StateGraph(chatschema)
graph.add_node("generate_questions",generate_questions)
graph.add_node("user_answer",wait_for_answer)
graph.add_node("feedback",feedback)
graph.add_edge(START,"generate_questions")
graph.add_edge("generate_questions","user_answer")
graph.add_edge("user_answer","feedback")
graph.add_conditional_edges("feedback",should_continue,{"continue":"generate_questions","END":END})
workflow=graph.compile(checkpointer=checkpointer)

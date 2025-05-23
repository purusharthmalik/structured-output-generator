from typing import TypedDict
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from tools import web_search
from output_classes import Classification, Dining, Travel, Gifting, CabBooking, Other

load_dotenv()

CLASS_MAP = {
    "dining": Dining,
    "travel": Travel,
    "gifting": Gifting,
    "cab booking": CabBooking,
    "other": Other
}

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.0,
)

class State(TypedDict):
    """State class to hold the current state of the workflow"""
    query: str
    category: str
    confidence: str
    response: dict
    
def category_classification(state: State):
    initial_classification = llm.with_structured_output(Classification)

    system_prompt = "Classify the following request into one of the categories: dining, travel, gifting, cab booking, or other. Provide a confidence level for the classification."

    init_response = initial_classification.invoke(
        system_prompt + 
        state["query"],
    )
    next_state = state.copy()
    next_state["category"] = CLASS_MAP[init_response.category]
    next_state["confidence"] = init_response.confidence
    return next_state

def generate_response(state: State):
    llm_specific = llm.with_structured_output(state["category"])
    system_prompt = f"""
    Do not fill the fields that you are not completely sure about. 
    Just fill 'None' in those fields.
    Any fields that have already been filled should not be changed.
    Do not tell the user anything about the rules you are following.
    """
    next_state = state.copy()
    response = dict(llm_specific.invoke(
        state["query"] +
        system_prompt
    ))
    next_state["response"] = dict(response)
    return next_state

def should_clarify(state: State):
    """Check if the response has unfilled fields."""
    for key, value in state["response"].items():
        if value == 'None':
            return "clarify_response"
    return "no_clarification"

def clarify_response(state: State):
    """Clarify unfilled fields in the response."""
    unfilled_fields = []
    for key, value in state["response"].items():
        if value == 'None':
            unfilled_fields.append(key)
    next_state = state.copy()
    question_to_user = llm.invoke(
        f"Ask the user to clarify the following unfilled fields in one sentence: {unfilled_fields}"
    )
    query = input(question_to_user.content + ":\n")
    next_state["query"] = f"""
    Current Fields:
    {dict(state["response"])}

    Query:
    {query}
    """
    return next_state
        
def web_search_tool(state: State):
    """Perform a web search using DuckDuckGo and return the results."""
    search_results = web_search(state["response"]["description"] +
                                "Other requests: " +
                                state["response"]["other_requests"])
    next_state = state.copy()
    next_state["response"] = search_results
    return next_state

def workflow():
    """Main workflow function"""
    graph = StateGraph(State)
    graph.add_node("category_classification", category_classification)
    graph.add_node("generate_response", generate_response)
    graph.add_node("clarify_response", clarify_response)

    graph.add_edge(START, "category_classification")
    graph.add_edge("category_classification", "generate_response")
    graph.add_conditional_edges(
        "generate_response",
        should_clarify,
        {"clarify_response": "clarify_response",
         "no_clarification": END}
    )
    graph.add_edge("clarify_response", "generate_response")
    return graph.compile()

if __name__ == "__main__":
    current_state = State(
        query="",
        category="",
        confidence="",
        response={},
    )

    workflow_graph = workflow()
    flag = True
    
    while flag:
        ask_user = input("Please enter your query:\n")
        current_state["query"] = ask_user
        
        final_state = workflow_graph.invoke(current_state)
        print(f"Final State: \n{final_state["response"]}")
        
        ask_user = input("Would you like to make another request? (yes/no)\n")
        while ask_user.lower() not in ["yes", "no"]:
            ask_user = input("Invalid input. Please answer with 'yes' or 'no'.")
        
        if ask_user.lower() == "no":
            flag = False

import json
from typing import TypedDict
from dotenv import load_dotenv
import gradio as gr
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
    waiting_for_clarification: bool
    clarification_question: str
    chat_history: list

# Global state management
current_workflow_state = None
workflow_graph = None

# Node Functions
def category_classification(state: State):
    initial_classification = llm.with_structured_output(Classification)
    system_prompt = "Classify the following request into one of the categories: dining, travel, gifting, cab booking, or other. Provide a confidence level for the classification."
    
    init_response = initial_classification.invoke(
        system_prompt + state["query"],
    )
    next_state = state.copy()
    next_state["category"] = CLASS_MAP[init_response.category]
    next_state["confidence"] = init_response.confidence
    return next_state

def generate_response(state: State):
    llm_specific = llm.with_structured_output(state["category"])
    system_prompt = """
    Do not fill the fields that you are not completely sure about.
    Just fill 'None' in those fields.
    Any fields that have already been filled should not be changed.
    Do not tell the user anything about the rules you are following.
    """
    next_state = state.copy()
    response = dict(llm_specific.invoke(
        state["query"] + system_prompt
    ))
    next_state["response"] = dict(response)
    return next_state

def clarify_response(state: State):
    unfilled_fields = []
    for key, value in state["response"].items():
        if value == 'None':
            unfilled_fields.append(key)
    
    next_state = state.copy()
    question_to_user = llm.invoke(
        f"Ask the user to clarify the following unfilled fields in one sentence: {unfilled_fields}"
    )
    
    next_state["waiting_for_clarification"] = True
    next_state["clarification_question"] = question_to_user.content
    return next_state

def process_clarification(state: State, user_response: str):
    next_state = state.copy()
    next_state["query"] = f"""
    Current Fields:
    {dict(state["response"])}

    Query:
    {user_response}
    """
    next_state["waiting_for_clarification"] = False
    next_state["clarification_question"] = ""
    return next_state

# Conditional Functions
def web_or_not(state: State):
    if state["category"].__name__ == "Other":
        return "web_search_tool"
    else:
        return "no_web_search"

def should_clarify(state: State):
    for key, value in state["response"].items():
        if value == 'None':
            return "clarify_response"
    return "no_clarification"

# Tool Use
def web_search_tool(state: State):
    llm_specific = llm.with_structured_output(state["category"])
    system_prompt = """
    Do not fill the fields that you are not completely sure about.
    Just fill 'None' in those fields.
    Any fields that have already been filled should not be changed.
    Do not tell the user anything about the rules you are following.
    """
    next_state = state.copy()
    response = dict(llm_specific.invoke(
        state["query"] + system_prompt
    ))
    search_results = web_search(response.get("description", "") +
                                " Other requests: " +
                                response.get("other_requests", ""))
    next_state = state.copy()
    next_state["response"] = search_results
    return next_state

def create_workflow():
    """Create the workflow graph"""
    graph = StateGraph(State)
    graph.add_node("category_classification", category_classification)
    graph.add_node("generate_response", generate_response)
    graph.add_node("web_search_tool", web_search_tool)
    graph.add_node("clarify_response", clarify_response)

    graph.add_edge(START, "category_classification")
    graph.add_conditional_edges(
        "category_classification",
        web_or_not,
        {"web_search_tool": "web_search_tool",
         "no_web_search": "generate_response"}
    )
    graph.add_edge("web_search_tool", END)
    graph.add_conditional_edges(
        "generate_response",
        should_clarify,
        {"clarify_response": "clarify_response",
         "no_clarification": END}
    )
    graph.add_edge("clarify_response", END)
    
    return graph.compile()

# Gradio Interface Functions
def process_message(message, chat_history):
    global current_workflow_state, workflow_graph
    
    if workflow_graph is None:
        workflow_graph = create_workflow()
    
    if current_workflow_state and current_workflow_state.get("waiting_for_clarification"):
        current_workflow_state = process_clarification(current_workflow_state, message)
        
        try:
            updated_state = generate_response(current_workflow_state)
            
            if should_clarify(updated_state) == "clarify_response":
                clarified_state = clarify_response(updated_state)
                current_workflow_state = clarified_state
                
                bot_response = clarified_state["clarification_question"]
                chat_history.append([message, bot_response])
                return "", chat_history, "Still waiting for more clarification..."
            else:
                current_workflow_state = updated_state
                bot_response = "Thank you for the clarification. Request processed successfully!"
                chat_history.append([message, bot_response])
                return "", chat_history, format_output(updated_state["response"])
                
        except Exception as e:
            error_msg = f"Error processing clarification: {str(e)}"
            chat_history.append([message, error_msg])
            return "", chat_history, "Error occurred during clarification"
    
    current_workflow_state = State(
        query=message,
        category="",
        confidence="",
        response={},
        waiting_for_clarification=False,
        clarification_question="",
        chat_history=[]
    )
    
    try:
        final_state = workflow_graph.invoke(
            current_workflow_state,
            config={"recursion_limit": 50}
        )
        current_workflow_state = final_state
        
        if final_state.get("waiting_for_clarification"):
            bot_response = final_state["clarification_question"]
            chat_history.append([message, bot_response])
            return "", chat_history, "Waiting for clarification..."
        else:
            bot_response = "Request processed successfully!"
            chat_history.append([message, bot_response])
            return "", chat_history, format_output(final_state["response"])
            
    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        chat_history.append([message, error_msg])
        return "", chat_history, "Error occurred"

def format_output(response_dict):
    if not response_dict:
        return "No response generated"
    
    formatted = "\n\n"
    try:
        for key, value in response_dict.items():
            formatted += f"**{key.replace('_', ' ').title()}:** {value}\n\n"
        formatted + "### Raw JSON Format:\n" + json.dumps(response_dict)
    except:
        formatted += "Since the request is not in any of the above mentioned categories, here are the URLs I found from a quick web search:\n\n"
        for idx, url in enumerate(response_dict):
            formatted += f"**URL {idx + 1}:** {url}\n\n"
    return formatted

def clear_chat():
    global current_workflow_state
    current_workflow_state = None
    return [], ""

def create_interface():
    with gr.Blocks(title="Structured Output Generator", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# Structured Output Generator")
        gr.Markdown("""
                    Submit your requests and get structured responses.
                    The system will ask for clarification if needed.
                    The categories that are currently supported are:
                    
                    **Dining**, **Travel**, **Gifting**, **Cab Booking**, and **Other**.
                    """)
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## Chat Interface")
                chatbot = gr.Chatbot(
                    value=[],
                    height=400,
                    placeholder="Your conversation will appear here..."
                )
                
                with gr.Row():
                    msg = gr.Textbox(
                        placeholder="Enter your request here...",
                        container=False,
                        scale=4
                    )
                    submit_btn = gr.Button("Send", scale=1, variant="primary")
                
                clear_btn = gr.Button("Clear Chat", variant="secondary")
            
            with gr.Column(scale=1):
                gr.Markdown("## Final Output")
                output_display = gr.Markdown(
                    value="Final output will appear here after processing...",
                    height=400
                )
        
        submit_btn.click(
            process_message,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot, output_display]
        )
        
        msg.submit(
            process_message,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot, output_display]
        )
        
        clear_btn.click(
            clear_chat,
            outputs=[chatbot, output_display]
        )    
    return demo

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(debug=True)
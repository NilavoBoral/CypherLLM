import streamlit as st
from streamlit_chat import message
from neo4j import GraphDatabase
import openai

openai.api_key = "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"

custom_button_style = """
<style>
.stButton>button {
    background-color: #88a8e3;
    color: white;
}
</style>
"""

# Page 1: Choose Dataset and Connect to Neo4j
def page_choose_dataset():
    st.title("Connect to Database", anchor ='center')
    # dataset_choice = st.selectbox("Select Dataset", ["Movies Dataset", "Train-Station Dataset"])
    neo4j_uri = st.text_input("URI")
    neo4j_username = st.text_input("Username")
    neo4j_password = st.text_input("Password", type="password")
    # try:
    #     selected_dataset = st.session_state['selected_dataset']
    # except:
    #     pass

    st.markdown(custom_button_style, unsafe_allow_html=True)
    
    col3 = st.columns(3)
    if col3[1].button("Connect to Database", key="b5"):
        # Connect to Neo4j and store connection details
        driver = connect_to_neo4j(neo4j_uri, neo4j_username, neo4j_password)
        if driver is not None:
            # Save dataset choice and Neo4j driver to session state
            # st.session_state['selected_dataset'] = dataset_choice
            st.session_state['neo4j_driver'] = driver
            # Switch to Page 2: Dataset Description and Chatbot
            st.experimental_rerun()
        else:
            # st.markdown(f'<h1 style="color:#ed0707;font-size:24px;">{"Invalid Database credentials. Please check your URI, username, and password."}</h1>', unsafe_allow_html=True)
            st.error("Invalid Database credentials. Please check your URI, username, and password.")
            # st.write("Invalid Neo4j credentials. Please check your Neo4j URI, username, and password.")

# Neo4j connection function
def connect_to_neo4j(uri, username, password):
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        # Attempt to connect to Neo4j to validate the password
        with driver.session() as session:
            session.run("RETURN 1")
        return driver
    except:
        return None




# Page 2: Dataset Description and Chatbot
def page_dataset_description():
    st.title("Dataset Description")

    # Retrieve selected dataset and Neo4j driver from session state
    # selected_dataset = st.session_state['selected_dataset']
    neo4j_driver = st.session_state['neo4j_driver']

    # Display dataset description
    # st.subheader("Selected Dataset:", selected_dataset)

    # Define the summarized dataset description
    summarized_description = "We have a graph-based dataset. Which consists of "

    # Define the detailed dataset description
    detailed_description = "We have a graph-based dataset. Which consists of:\n\n"

    # Open a session and execute Cypher queries to retrieve dataset information
    with neo4j_driver.session() as session:
        # Retrieve node types
        node_types_result = session.run("CALL db.labels() YIELD label RETURN label")
        node_types = [record["label"] for record in node_types_result]

        if node_types:
            summarized_description += f"{len(node_types)} types of nodes: "

            detailed_description += "**Unique node-types and their properties:**\n\n"
            # for node_type in node_types:
            #     detailed_description += f"- **{node_type}**: Represents {node_type} in the graph dataset.\n"
            # detailed_description += "\n"

        # Node Properties
        for node in node_types:
            node_properties = session.run("MATCH (n:"+node+") WITH DISTINCT keys(n) AS keys UNWIND keys AS keyslisting WITH DISTINCT keyslisting AS allfields RETURN allfields;")
            node_prop = [record["allfields"] for record in node_properties]
            if node_properties:
                summarized_description += f"{node} (Properties: {', '.join(node_prop)}), "
                detailed_description += f"- **{node}**: (Properties: {', '.join(node_prop)})\n"
            else:
                summarized_description += f"{node}, "
                detailed_description += f"- **{node}**\n"
            detailed_description += "\n"

        # Retrieve relationship types
        relationship_types_result = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType")
        relationship_types = [record["relationshipType"] for record in relationship_types_result]

        if relationship_types:
            # summarized_description += f" and {len(relationship_types)} types of relationships: ({', '.join(relationship_types)})."
            summarized_description += f" and {len(relationship_types)} types of relationships: "

            detailed_description += "**Unique relationship-types:**\n\n"
            # for relationship_type in relationship_types:
            #     detailed_description += f"- **{relationship_type}**\n"
            # detailed_description += "\n"
        
        # Relationship Properties
        for node1 in node_types:
            for relation_idx in range(0, len(relationship_types)):
                for node2 in node_types:
                    try:
                        relation_properties = session.run("MATCH (:" + node1 + ") <-[r:" + relationship_types[relation_idx] + "]- (:" + node2 + ") RETURN keys(r) as relation_types LIMIT(1)")
                        relation_prop = [record["relation_types"] for record in relation_properties][0]
                        # st.write(relation_prop)
                        if relation_prop:
                            summarized_description += f"{relationship_types[relation_idx]} (Properties: {', '.join(relation_prop)}), "
                            detailed_description += f"- **{relationship_types[relation_idx]}**: (Properties: {', '.join(relation_prop)})\n"
                            detailed_description += "\n"
                        else:
                            summarized_description += f"{relationship_types[relation_idx]}, "
                            detailed_description += f"- **{relationship_types[relation_idx]}**\n"
                            detailed_description += "\n"
                        # After storing relation details change that retaion-name from relationship list (to ignore repeatation of relation)
                        relationship_types[relation_idx] = "fake_relation_420"
                    except:
                        pass
        # Remove the last comma & space 
        # and add fullstop
        summarized_description = summarized_description[:-2] + "."

        # Retrieve cardinality of nodes and relationships
        node_count_result = session.run("MATCH (n) RETURN count(n) AS node_count")
        node_count = node_count_result.single()["node_count"]

        relationship_count_result = session.run("MATCH ()-[r]-() RETURN count(r) AS relationship_count")
        relationship_count = relationship_count_result.single()["relationship_count"]

        if node_count is not None or relationship_count is not None:
            detailed_description += "**Cardinality:**\n"
            if node_count is not None:
                detailed_description += f"- Number of nodes: {node_count}\n"
            if relationship_count is not None:
                detailed_description += f"- Number of relationships: {relationship_count}\n"

    st.write(detailed_description)
    st.write(summarized_description)
    st.session_state['summarized_description'] = summarized_description


    # Chatbot section
    st.title("Chat with your data bot")
    # user_query = st.text_input("Enter your query")
    # ask_button = st.button("Ask")

    # if ask_button:
    #     try:
    #         # Process user text and generate query using OpenAI
    #         generated_query = generate_cypher_query(user_query)

    #         # Process generated query using the selected dataset and Neo4j
    #         process_query(neo4j_driver, generated_query)
    #     except:
    #         st.write("Sorry, I don't understand what you're asking.")



    # message("Hi I am your DB assistant. Tell me how can I help")

    # if "message_history" not in st.session_state:
    #     st.session_state.message_history = []

    # for message_ in st.session_state.message_history:
    #     message(message_, is_user=True) # display all the previous message

    # placeholder = st.empty() # placeholder for latest message
    # input_ = st.text_input("you")

    # if input_ != "":
    #     st.session_state.message_history.append(input_)

    #     # Process user text and generate query using OpenAI
    #     generated_query = generate_cypher_query(input_)
    #     # Process generated query using the selected dataset and Neo4j
    #     process_query(neo4j_driver, generated_query)

    #     input_ = ""
    #     # mycursor.execute(str(input_+";"))
    #     # myresult = mycursor.fetchall()
    #     # for x in myresult:
    #     #     message(x)

    # with placeholder.container():
    #     if len(st.session_state["message_history"]) > 0:
    #         message(st.session_state.message_history[-1], is_user=True) # display the latest message


    # Initialise session state variables
    if 'generated' not in st.session_state:
        st.session_state['generated'] = []
    if 'past' not in st.session_state:
        st.session_state['past'] = []
    if 'messages' not in st.session_state:
        st.session_state['messages'] = [
            {"role": "system", "content": "demo message"}]

    # container for chat history
    response_container = st.container()
    # container for text box
    container = st.container()

    with container:
        with st.form(key='my_form', clear_on_submit=True):
            user_input = st.text_area("You:", key='input', height=25)
            submit_button = st.form_submit_button(label='Send')

        if submit_button and user_input:
            try:
                # Process user text and generate query using OpenAI
                summarized_description = st.session_state['summarized_description']
                prompt = summarized_description + ". Generate query for this graph database from the given sentences."

                generated_query = generate_cypher_query(prompt, user_input)

                # Process generated query using the selected dataset and Neo4j
                output = process_query(neo4j_driver, generated_query)

                if output == "":
                    # Change relationship direction and generate the querry again
                    modified_prompt = generated_query + "\n Just change the direction of the relationship, don't change anything else."
                    modified_query = generate_cypher_query(modified_prompt, generated_query)

                    # Process generated query using the selected dataset and Neo4j
                    output = process_query(neo4j_driver, modified_query)

                    if output == "":
                        output = "Please break down your question to help me understand it better."
            except:
                output = "Sorry, We don't have that information."

            # output = generate_response(user_input)
            st.session_state['past'].append(user_input)
            st.session_state['generated'].append(generated_query + "\n\n" + 
                                                 output)
            # st.write(generated_query)

    if st.session_state['generated']:
        with response_container:
            for i in range(len(st.session_state['generated'])):
                message(st.session_state["past"][i], is_user=True, key=str(i) + '_user')
                message(st.session_state["generated"][i], key=str(i))



    # Button to go back and load another dataset
    st.markdown(custom_button_style, unsafe_allow_html=True)

    col3 = st.columns(3)
    if col3[1].button("Load Another Dataset", key="b5"):
    # if st.button("Load Another Dataset"):
        # Clear session state and switch to Page 1: Choose Dataset
        # st.session_state.pop('selected_dataset')
        # st.session_state.pop('neo4j_driver')
        st.session_state.clear()
        st.experimental_rerun()


# Generate query using OpenAI
def generate_cypher_query(prompt, text_query):

    # summarized_description = st.session_state['summarized_description']
    response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=[
        {
          "role": "system",
          "content": prompt
        #   summarized_description + ". Generate query for this graph database from the given sentences."
        },
        {
          "role": "user",
          "content": text_query
        }
      ],
      temperature=0,
      max_tokens=64,
      top_p=1.0,
      frequency_penalty=0.0,
      presence_penalty=0.0
    )
    generated_query = response.choices[0].message.content.strip().replace("\n", " ")
    return generated_query

# Function to process user query
def process_query(neo4j_driver, query):
    with neo4j_driver.session() as session:
        result = session.run(query)
        records = [dict(record) for record in result]
        names = [str(next(iter(d.values()))) for d in records]
        # st.write(names)
        # message(str(names))
        # join list strings
        joined_names = ", ".join(names)
        return joined_names

# Main program
def main():
    st.set_page_config(page_title="Streamlit Dataset Explorer")

    # Check if Neo4j driver is present in session state
    if 'neo4j_driver' not in st.session_state:
        page_choose_dataset()
    else:
        page_dataset_description()

if __name__ == '__main__':
    main()

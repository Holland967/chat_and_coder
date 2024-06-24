from openai import OpenAI
import streamlit as st
import json
import os

def chatCompletion(model, messages, max_tokens, temperature, top_p):
    if model == "qwen2-72b-instruct":
        api_key = os.environ.get("INFI_API_KEY")
        base_url = os.environ.get("INFI_BASE_URL")
    elif model == "deepseek-ai/DeepSeek-Coder-V2-Instruct":
        api_key = os.environ.get("SILI_API_KEY")
        base_url = os.environ.get("SILI_BASE_URL")
    client = OpenAI(api_key=api_key, base_url=base_url)
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=None,
            stream=True
        )
        result = st.write_stream(chunk.choices[0].delta.content for chunk in stream if chunk.choices[0].delta.content)
    return result

if "login_state" not in st.session_state:
    st.session_state.login_state = False

def login():
    USERNAME = os.environ.get("USERNAME")
    PASSWORD = os.environ.get("PASSWORD")
    if not st.session_state.login_state:
        username = st.text_input("Username", key="username", type="default")
        password = st.text_input("Password", key="password", type="password")
        login_button = st.button("Login", key="login_button", type="primary")
        if username == USERNAME and password == PASSWORD:
            st.session_state.login_state = True
        if login_button:
            st.rerun()
    else:
        main()

def main():
    MODEL = ["qwen2-72b-instruct", "deepseek-ai/DeepSeek-Coder-V2-Instruct"]
    PARAM = {
        "qwen2-72b-instruct": {"temperature": 0.70, "top_p": 0.80},
        "deepseek-ai/DeepSeek-Coder-V2-Instruct": {"temperature": 0.80, "top_p": 0.70}
    }

    chatlog_file = "chatlog.json"

    def getData(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                json_data = json.load(file)
            return json_data
        except:
            return []
    
    def saveData(file_path, chatlog_data):
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(chatlog_data, file, indent=4)
    
    def getOptions(file_path, model):
        chatlog_data = getData(file_path)
        existed_item = [item for item in chatlog_data if item["model"] == model]
        if not chatlog_data or (chatlog_data and not existed_item):
            chatlog_options = []
        else:
            chatlog_options = []
            for item in chatlog_data:
                if item["model"] == model:
                    chatlog_options.append(f"{item["index"]}: {item["message"][0]["content"][:10]}")
        return chatlog_options
    
    def getIndex(file_path, model):
        chatlog_data = getData(file_path)
        existed_item = [item for item in chatlog_data if item["model"] == model]
        if not existed_item:
            index = 1
        else:
            index = len(existed_item) + 1
        return index

    if "index" not in st.session_state:
        st.session_state.index = 1

    if "general_system" not in st.session_state:
        st.session_state.general_system = "You are a helpful assistant."
    if "coder_system" not in st.session_state:
        st.session_state.coder_system = "You are an professional and experienced programming expert."
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    def resetState(model):
        if model == "qwen2-72b-instruct":
            st.session_state.general_system = "You are a helpful assistant."
        elif model == "deepseek-ai/DeepSeek-Coder-V2-Instruct":
            st.session_state.coder_system = "You are an professional and experienced programming expert."
        st.session_state.messages = []
        st.rerun()
    
    def newChat(file_path, model, chatlog_cache):
        chatlog_data = getData(file_path)
        existed_message = [item["message"] for item in chatlog_data if item["model"] == model]
        if st.session_state.messages and st.session_state.messages not in existed_message:
            chatlog_data.append(chatlog_cache)
            saveData(file_path, chatlog_data)
            resetState(model)
        elif st.session_state.messages and st.session_state.messages in existed_message:
            resetState(model)
        elif not st.session_state.messages:
            st.info("已经是新的对话！")
    
    def submitChat(file_path, model, chatlog_selector):
        chatlog_data = getData(file_path)
        existed_message = [item["message"] for item in chatlog_data if item["model"] == model]
        if (st.session_state.messages and st.session_state.messages in existed_message) or not st.session_state.messages:
            if model == "qwen2-72b-instruct":
                st.session_state.general_system = [item for item in chatlog_data if f"{item["index"]}: {item["message"][0]["content"][:10]}" == chatlog_selector][0]["system"]
            elif model == "deepseek-ai/DeepSeek-Coder-V2-Instruct":
                st.session_state.coder_system = [item for item in chatlog_data if f"{item["index"]}: {item["message"][0]["content"][:10]}" == chatlog_selector][0]["system"]
            st.session_state.messages = [item for item in chatlog_data if f"{item["index"]}: {item["message"][0]["content"][:10]}" == chatlog_selector][0]["message"]
            st.rerun()
        elif st.session_state.messages and st.session_state.messages not in existed_message:
            st.warning("请先保存或重置当前对话！")
    
    def deleteChatlog(file_path, model):
        chatlog_data = getData(file_path)
        existed_item = [item for item in chatlog_data if item["model"] == model]
        deleted_message = [item for item in chatlog_data if f"{item["index"]}: {item["message"][0]["content"][:10]}" == chatlog_selector][0]["message"]
        if st.session_state.messages and st.session_state.messages == deleted_message:
            new_chatlog_data = [item for item in chatlog_data if item["model"] != model]
            left_item = [item for item in existed_item if f"{item["index"]}: {item["message"][0]["content"][:10]}" != chatlog_selector]
            for item, i in zip(left_item, range(len(left_item))):
                item["index"] = i + 1
            new_chatlog_data += left_item
            saveData(file_path, new_chatlog_data)
            resetState(model)
        else:
            new_chatlog_data = [item for item in chatlog_data if f"{item["index"]}: {item["message"][0]["content"][:10]}" != chatlog_selector]
            for item, i in zip(new_chatlog_data, range(len(new_chatlog_data))):
                item["index"] = i + 1
            saveData(file_path, new_chatlog_data)
            st.rerun()
    
    def deleteChatlogs(file_path, model):
        chatlog_data = getData(file_path)
        existed_message = [item["message"] for item in chatlog_data if item["model"] == model]
        if st.session_state.messages and st.session_state.messages in existed_message:
            new_chatlog_data = [item for item in chatlog_data if item["model"] != model]
            saveData(file_path, new_chatlog_data)
            resetState(model)
        elif (st.session_state.messages and st.session_state.messages not in existed_message) or not st.session_state.messages:
            new_chatlog_data = [item for item in chatlog_data if item["model"] != model]
            saveData(file_path, new_chatlog_data)
            st.rerun()

    logout_button = st.sidebar.button("Logout", key="logout_button")

    if st.session_state.messages:
        model = st.sidebar.selectbox("Model", options=MODEL, index=0, key="model", disabled=True)
    elif not st.session_state.messages:
        model = st.sidebar.selectbox("Model", options=MODEL, index=0, key="model", disabled=False)

    newchat_button = st.sidebar.button("New Chat", key="newchat_button", type="primary", use_container_width=True)

    if model == "qwen2-72b-instruct":
        system_prompt = st.sidebar.text_area("System Prompt", value=st.session_state.general_system, key="system_prompt")
        st.session_state.general_system = system_prompt
    elif model == "deepseek-ai/DeepSeek-Coder-V2-Instruct":
        system_prompt = st.sidebar.text_area("System Prompt", value=st.session_state.coder_system, key="system_prompt")
        st.session_state.coder_system = system_prompt
    
    chatlog_options = getOptions(chatlog_file, model)
    chatlog_selector = st.sidebar.selectbox("Conversation History", chatlog_options, index=None, key="chatlog_selector")

    submit_button = st.sidebar.button("Submit", key="submit_button", type="primary", use_container_width=True)
    col1, col2 = st.sidebar.columns(2)
    with col1:
        delete_one_button = st.button("Delete", key="delete_one", use_container_width=True)
    with col2:
        delete_all_button = st.button("Delete All", key="delete_all", use_container_width=True)
    reset_button = st.sidebar.button("Reset", key="reset_button", use_container_width=True)

    max_tokens = st.sidebar.slider("Max Tokens", 1, 4096, 4096, step=1, key="max_tokens")
    temperature = st.sidebar.slider("Temperature", 0.10, 2.00, PARAM[model]["temperature"], step=0.10, key="temperature")
    top_p = st.sidebar.slider("Top P", 0.10, 1.00, PARAM[model]["top_p"], step=0.10, key="top_p")

    if model == "qwen2-72b-instruct":
        st.title("General Chat", anchor=False)
    elif model == "deepseek-ai/DeepSeek-Coder-V2-Instruct":
        st.title("DeepSeek Coder", anchor=False)
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)
    
    if query := st.chat_input("Say something..."):
        with st.chat_message("user"):
            st.markdown(query, unsafe_allow_html=True)
        
        st.session_state.messages.append({"role": "user", "content": query})
        messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages
        result = chatCompletion(model, messages, max_tokens, temperature, top_p)
        st.session_state.messages.append({"role": "assistant", "content": result})

        st.rerun()
    
    st.session_state.index = getIndex(chatlog_file, model)
    if model == "qwen2-72b-instruct":
        chatlog_cache = {
            "model": model,
            "index": st.session_state.index,
            "system": st.session_state.general_system,
            "message": st.session_state.messages
        }
    elif model == "deepseek-ai/DeepSeek-Coder-V2-Instruct":
        chatlog_cache = {
            "model": model,
            "index": st.session_state.index,
            "system": st.session_state.coder_system,
            "message": st.session_state.messages
        }
    
    if newchat_button:
        newChat(chatlog_file, model, chatlog_cache)
    if chatlog_selector and submit_button:
        submitChat(chatlog_file, model, chatlog_selector)
    if chatlog_selector and delete_one_button:
        deleteChatlog(chatlog_file, model)
    if delete_all_button:
        deleteChatlogs(chatlog_file, model)
    if reset_button:
        resetState(model)

    if logout_button:
        st.session_state.login_state = False
        st.rerun()

if __name__ == "__main__":
    login()

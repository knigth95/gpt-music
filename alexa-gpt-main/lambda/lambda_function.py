import logging
import ask_sdk_core.utils as ask_utils
import openai
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

# Set OpenAI API key
openai.api_key = ""

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Chat G.P.T. mode activated"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class GptQueryIntentHandler(AbstractRequestHandler):
    """Handler for Gpt Query Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("GptQueryIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        query = handler_input.request_envelope.request.intent.slots["query"].value
        response = generate_gpt_response(query)

        return (
                handler_input.response_builder
                    .speak(response)
                    .ask("Any other questions?")
                    .response
            )
        
class GptQueryIntentHandler(AbstractRequestHandler):
    """Handler for Gpt Query Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("GptQueryIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        query = handler_input.request_envelope.request.intent.slots["query"].value
        
        #从会话属性中提取以前的上下文
        previous_context = handler_input.attributes_manager.session_attributes.get("context")
        
        response = generate_gpt_response(query, previous_context)
        
        #使用当前上下文更新会话属性
        current_context = [{"role": "user", "content": query}, {"role": "assistant", "content": response}]
        handler_input.attributes_manager.session_attributes["context"] = current_context

        return (
            handler_input.response_builder
                .speak(response)
                .ask("Any other questions?")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors."""
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Leaving Chat G.P.T. mode"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )
        
#压缩上下文
def compress_context(context):
    compressed_context = []
    user_messages = [message['content'] for message in context if message['role'] == 'user']
    assistant_messages = [message['content'] for message in context if message['role'] == 'assistant']
    
    if user_messages:
        compressed_context.append({"role": "user", "content": " ".join(user_messages)})
    
    if assistant_messages:
        compressed_context.append({"role": "assistant", "content": " ".join(assistant_messages)})
    
    return compressed_context

def generate_gpt_response(query, context=None):
    try:
        compressed_context = compress_context(context) if context else None
        
        user_messages = [message['content'] for message in compressed_context if message['role'] == 'user']
        assistant_messages = [message['content'] for message in compressed_context if message['role'] == 'assistant']

        # 构建 prompt
        prompt = "You are a helpful assistant.\n"
        if user_messages:
            prompt += 'User: ' + ' '.join(user_messages) + '\n'
        if assistant_messages:
            prompt += 'Assistant: ' + ' '.join(assistant_messages) + '\n'
        prompt += 'User: ' + query
        
        
        response = openai.Completion.create(
            engine="gpt-3.5-turbo",
            prompt=prompt,
            max_tokens=512,  # 控制响应的最大长度
            n=1,
            stop=None,
            temperature=0.5
        )
        
        return response['choices'][0]['text'].strip(), user_messages, assistant_messages
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return f"Error generating response: {str(e)}", None, None
    

#角色切换
def handle_user_query(query, user_messages, assistant_messages):
    if "change role to assistant" in query.lower():
        user_messages = []
        assistant_messages = []
        response = "You are now the helpful assistant."
    elif "change role to user" in query.lower():
        user_messages = []
        assistant_messages = []
        response = "You are now the user."
    else:
        user_messages.append(query)
        response, _, _ = generate_gpt_response(query, [
            {'role': 'user', 'content': msg} for msg in user_messages] +
            [{'role': 'assistant', 'content': msg} for msg in assistant_messages])
        assistant_messages.append(response)

    return response, user_messages, assistant_messages

# 在主程序中的用户查询处理部分调用handle_user_query函数

# 初始化上下文
user_messages = []
assistant_messages = []

while True:
    query = input("User: ")

    response, user_messages, assistant_messages = handle_user_query(query, user_messages, assistant_messages)

    print("Assistant:", response)


sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(GptQueryIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
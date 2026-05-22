import asyncio
import grpc
import os
from pathlib import Path
from openai import OpenAI
from steeleagle_sdk.api.vehicle import Vehicle


def load_dotenv(path: str = ".env") -> None:
    # Load local secrets
    env_path = Path(path)
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv()
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

async def create_vehicle() -> Vehicle:
    # Expose gRPC API over local Unix socket
    channel = grpc.aio.insecure_channel('unix:///tmp/test1-kernel.sock')
    return Vehicle(channel, None)

async def call_takeoff():
    vehicle = await create_vehicle()
    responses = []
    # take_off status updates
    async for response in vehicle.take_off(10.0):
        responses.append(response)
    last = responses[-1]
    if last.status == 2:
        return "Drone has taken off successfully to 10m."
    else:
        return f"Takeoff failed with status: {last.status}"

async def call_land():
    vehicle = await create_vehicle()
    responses = []
    # land streams status updates
    async for response in vehicle.land():
        responses.append(response)
    last = responses[-1]
    if last.status == 2:
        return "Drone has landed successfully."
    else:
        return f"Landing failed with status: {last.status}"

tools = [
    {
        "type": "function",
        "function": {
            "name": "takeoff",
            "description": "Command the simulated drone to take off to 10 meters altitude",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "land",
            "description": "Command the simulated drone to land",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]

async def chat():
    print("Welcome to the SteelEagle Drone Controller!")
    print("Type your instructions:")
    print("Type 'quit' to exit\n")
    
    messages = []
    
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "quit":
            break
        
        messages.append({"role": "user", "content": user_input})
        
        # Ask the LLM model whether the new message should trigger a tool call
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        if message.tool_calls:
            for tool_call in message.tool_calls:
                if tool_call.function.name == "takeoff":
                    # Execute the real command only after the LLM model selects the tool
                    print("ChatGPT: Executing takeoff command...")
                    result = await call_takeoff()
                    print(f"Success: {result}")
                    messages.append({"role": "assistant", "content": f"Takeoff executed: {result}"})
                elif tool_call.function.name == "land":
                    # Execute the real command only after the LLM model selects the tool
                    print("ChatGPT: Executing land command...")
                    result = await call_land()
                    print(f"Success: {result}")
                    messages.append({"role": "assistant", "content": f"Landing executed: {result}"})
        else:
            print(f"ChatGPT: {message.content}")
            messages.append({"role": "assistant", "content": message.content})

if __name__ == "__main__":
    asyncio.run(chat())
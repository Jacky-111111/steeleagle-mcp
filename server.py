import asyncio
import grpc
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from steeleagle_sdk.api.vehicle import Vehicle

app = Server("drone-controller")

async def create_vehicle() -> Vehicle:
    # Connect to the simulator kernel over the local Unix domain socket
    channel = grpc.aio.insecure_channel('unix:///tmp/test1-kernel.sock')
    return Vehicle(channel, None)

async def call_takeoff(vehicle: Vehicle):
    responses = []
    # take_off status updates
    async for response in vehicle.take_off(10.0):
        responses.append(response)
    return responses[-1]

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    # Expose available MCP tools to all clients
    return [
        types.Tool(
            name="takeoff",
            description="Command the simulated drone to take off to 10 meters altitude",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "takeoff":
        # Create a fresh vehicle client per call
        vehicle = await create_vehicle()
        response = await call_takeoff(vehicle)
        if response.status == 2:
            return [types.TextContent(type="text", text="Drone has taken off successfully to 10 meters!")]
        else:
            return [types.TextContent(type="text", text=f"Takeoff failed with status: {response.status}")]
    raise ValueError(f"Unknown tool: {name}")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
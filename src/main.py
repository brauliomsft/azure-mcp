from vm_operations import mcp
from dotenv import load_dotenv
load_dotenv('src/.env')


if __name__ == "__main__":
    mcp.run(transport='stdio')

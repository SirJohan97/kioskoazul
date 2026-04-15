import os
from dotenv import load_dotenv
load_dotenv('.env')

from backend import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)
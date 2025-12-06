# c:\Users\doug\Trae Projects\NeoX\monitoring-service\run_app.py
import asyncio
import sys
import uvicorn

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=9000, reload=True, log_level="debug")

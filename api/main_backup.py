from fastapi import FastAPI, HTTPException
import subprocess

app = FastAPI()

# Temporary in-memory store for testing
function_store = {
    1: {"id": 1, "name": "HelloPython", "language": "python", "code": 'print("Hello from Python!")', "timeout": 5},
    2: {"id": 2, "name": "InfiniteLoop", "language": "python", "code": 'while True: pass', "timeout": 3},
    # If you create a JS Docker image:
    # 3: {"id": 3, "name": "HelloJS", "language": "javascript", "code": 'console.log("Hello from JS")', "timeout": 5}
}

@app.post("/execute/{function_id}")
def execute_function(function_id: int):
    if function_id not in function_store:
        raise HTTPException(status_code=404, detail="Function not found")

    fn = function_store[function_id]
    lang = fn["language"]
    code = fn["code"]
    timeout_sec = fn["timeout"]

    # Route to correct Docker image
    if lang == "python":
        image = "lambda-py"
    elif lang == "javascript":
        image = "lambda-js"
    else:
        raise HTTPException(status_code=400, detail="Unsupported language")

    # Execute in Docker
    try:
        result = subprocess.run(
            ["timeout", f"{timeout_sec}s", "docker", "run", "-i", image],
            input=code.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_sec + 2  # extra buffer
        )
        return {
            "status": "success" if result.returncode == 0 else "error",
            "output": result.stdout.decode(),
            "error": result.stderr.decode()
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "output": "",
            "error": "Execution timed out"
        }
    except Exception as e:
        return {
            "status": "error",
            "output": "",
            "error": str(e)
        }
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Lambda API running"}

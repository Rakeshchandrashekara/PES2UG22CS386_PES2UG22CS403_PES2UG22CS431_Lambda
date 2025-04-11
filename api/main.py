from fastapi import FastAPI, HTTPException
import subprocess
import subprocess
import random

import subprocess
import time

import subprocess
import time

def run_with_docker(code: str, timeout: int = 5):
    try:
        start = time.time()
        result = subprocess.run(
            ["timeout", f"{timeout}s", "docker", "run", "-i", "lambda-py"],
            input=code.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout + 2
        )
        end = time.time()
        return {
            "status": "success" if result.returncode == 0 else "error",
            "output": result.stdout.decode(),
            "error": result.stderr.decode(),
            "duration": round(end - start, 3)
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "output": "",
            "error": "Execution timed out",
            "duration": timeout
        }
    except Exception as e:
        return {
            "status": "error",
            "output": "",
            "error": str(e),
            "duration": 0
        }

function_store = {
    1: {
        "id": 1,
        "name": "hello",
        "language": "python",
        "code": 'print("Hello from Python!")',
        "timeout": 5
    }
}

def run_with_gvisor(code: str, timeout: int = 5):
    try:
        start = time.time()
        result = subprocess.run(
            ["timeout", f"{timeout}s", "docker", "run", "--runtime=runsc", "-i", "lambda-py"],
            input=code.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout + 2
        )
        end = time.time()
        return {
            "status": "success" if result.returncode == 0 else "error",
            "output": result.stdout.decode(),
            "error": result.stderr.decode(),
            "runtime": "gvisor",
            "duration": round(end - start, 3)
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "output": "", "error": "Execution timed out", "runtime": "gvisor"}
    except Exception as e:
        return {"status": "error", "output": "", "error": str(e), "runtime": "gvisor"}

pooled_containers = ["lambda_pool_py1", "lambda_pool_py2"]

def exec_in_pooled_container(container_name, code):
    try:
        result = subprocess.run(
            ["docker", "exec", "-i", container_name, "python", "-c", code],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        return {
            "status": "success" if result.returncode == 0 else "error",
            "output": result.stdout.decode(),
            "error": result.stderr.decode()
        }
    except Exception as e:
        return {"status": "error", "output": "", "error": str(e)}


def warm_up_function(image):
    try:
        subprocess.Popen(
            ["docker", "run", "--rm", "-d", image, "sleep", "10"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return {"status": "warmed"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


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
@app.post("/functions/{function_id}/warmup")
def warmup_function(function_id: int):
    fn = function_store.get(function_id)
    if not fn:
        raise HTTPException(status_code=404, detail="Function not found")

    image = "lambda-py" if fn["language"] == "python" else "lambda-js"
    return warm_up_function(image)

@app.post("/execute-pooled/{function_id}")
def execute_pooled(function_id: int):
    fn = function_store.get(function_id)
    if not fn:
        raise HTTPException(status_code=404, detail="Function not found")

    container = random.choice(pooled_containers)
    return exec_in_pooled_container(container, fn["code"])

@app.post("/execute/{function_id}")
def execute_function(function_id: int, runtime: str = "docker"):
    fn = function_store.get(function_id)
    if not fn:
        raise HTTPException(status_code=404, detail="Function not found")

    code = fn["code"]
    timeout = fn["timeout"]

    if runtime == "gvisor":
        return run_with_gvisor(code, timeout)
    else:
        return run_with_docker(code, timeout)  # Your existing docker function

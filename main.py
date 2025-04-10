from fastapi import FastAPI, HTTPException
import subprocess

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "FastAPI is working!"}

function_store = {
    1: {
        "id": 1,
        "name": "hello",
        "language": "python",
        "code": 'print("Hello from Python!")',
        "timeout": 5
    }
}

@app.post("/execute/{function_id}")
def execute_function(function_id: int):
    if function_id not in function_store:
        raise HTTPException(status_code=404, detail="Function not found")

    fn = function_store[function_id]
    code = fn["code"]
    timeout = fn["timeout"]

    try:
        result = subprocess.run(
            ["timeout", f"{timeout}s", "docker", "run", "-i", "lambda-py"],
            input=code.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout + 2
        )
        return {
            "status": "success" if result.returncode == 0 else "error",
            "output": result.stdout.decode(),
            "error": result.stderr.decode()
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "output": "", "error": "Execution timed out"}
    except Exception as e:
        return {"status": "error", "output": "", "error": str(e)}

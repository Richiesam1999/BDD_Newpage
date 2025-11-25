#sample

from fastapi import FastAPI, BackgroundTasks

app = FastAPI()

@app.post("/analyze")
async def analyze_url(url: str, background_tasks: BackgroundTasks):
    """Trigger analysis for a URL"""
    task_id = generate_task_id()
    background_tasks.add_task(run_analysis, url, task_id)
    return {"task_id": task_id}

@app.get("/results/{task_id}")
async def get_results(task_id: str):
    """Get generated Gherkin file"""
    return FileResponse(f"output/features/{task_id}.feature")
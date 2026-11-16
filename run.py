import uvicorn

if __name__ == "__main__":
    print("Starting Metricore.in FastAPI server on http://127.0.0.1:8000")
    print("Open http://127.0.0.1:8000 in your browser to view the directory.")
    print("API documentation is available at http://127.0.0.1:8000/docs")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)


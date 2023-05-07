import uvicorn
import firebase_admin
import requests
import json
 
from firebase_admin import credentials, firestore
from fastapi import FastAPI, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from typing import Optional
from pydantic import BaseModel

# DISCLAIMER: This code cannot be run on normal circumstances since service account keys are meant to be private and only accessible by the admin
cred = credentials.Certificate('NOTFORPUBLIC/to-do-service-account-keys.json')
firebase = firebase_admin.initialize_app(cred)
db = firestore.client()
app = FastAPI()
allow_all = ['*']
app.add_middleware(
   CORSMiddleware,
   allow_origins=allow_all,
   allow_credentials=True,
   allow_methods=allow_all,
   allow_headers=allow_all
)

def sign_in_with_email_and_password(email, password, return_secure_token=True):
    payload = json.dumps({"email":email, "password":password, "return_secure_token":return_secure_token})
    FIREBASE_WEB_API_KEY = "" # DISCLAIMER: This code cannot be run on normal circumstances since web API keys are meant to be private and only accessible by the admin
    rest_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"


    r = requests.post(rest_api_url,
                  params={"key": FIREBASE_WEB_API_KEY},
                  data=payload)

    return r.json()
 
# login endpoint
@app.get("/login", include_in_schema=False)
async def login(email: str, password: str):
    try:
        user = sign_in_with_email_and_password(email, password)
        jwt = user['idToken']
        print("hello?")
        return JSONResponse(content={'token': jwt}, status_code=200)
    except:
        return HTTPException(detail={'message': 'There was an error logging in'}, status_code=400)
    

# Define base models Task and TaskUpdate for request body format
class Task(BaseModel):
    title : str
    description : str
    completed : bool

class TaskUpdate(BaseModel):
    title : Optional[str] = None
    description : Optional[str] = None
    completed : Optional[bool] = None


@app.get("/")
def default():
    return {"Welcome": "Your first request starts here"}


# GET task (by title)
@app.get("/get-by-title/{title}")
def get_by_title(title: str):
    coll_ref = db.collection("tasks")
    coll_query = coll_ref.where("title","==",title)
    result = dict()
    for doc in coll_query.stream():
        result[doc.id] = doc.to_dict()
    if result:
        return result
    else:
        return {"error": f"No task with title {title}"}


# GET task (by id)
@app.get("/get/{id}")
def get(id: str):
    doc_ref = db.collection('tasks').document(id)
    # result = dict()
    # result[doc_ref.id] = doc_ref.to_dict()

    if doc_ref:
        return doc_ref.get().to_dict()
    else:
        return {"error": f"No task with id {id}"}
    

# POST task
@app.post("/post")
async def post(task: Task):
    coll_ref = db.collection("tasks")
    # Adds document to collection with "title", "description", "created" (left blank), and "completed" attributes,
    # As well as initializing "create_time" and "doc_ref" variables,
    # At the same time
    create_time, doc_ref= coll_ref.add(
        {
            "title": task.title,
            "description": task.description,
            "created": None,
            "completed": task.completed,
        }
    )
    # Second update to document in order to add "create_time" variable
    doc_ref.update({"created": create_time})
    return task


# PUT task (Modify task title and/or description)
@app.put("/update/{id}")
async def update(id: str, task: TaskUpdate):
    doc_ref = db.collection('tasks').document(id)
    doc_ref.update(
        {
            "title": task.title,
            "description": task.description
        }
    )
    return task


# PUT task status (Toggle on and off task status whether it is complete or not)
@app.put("/toggle-status/{id}")
async def toggle_status(id: str, task: TaskUpdate):
    doc_ref = db.collection('tasks').document(id)
    print(doc_ref.get().to_dict()["completed"])
    toggleUpdate = not doc_ref.get().to_dict()["completed"]
    doc_ref.update(
        {
            "completed": toggleUpdate
        }
    )
    return task


# DELETE task
@app.delete("/delete/{id}")
async def delete(id: str, task: TaskUpdate):
    doc_ref = db.collection('tasks').document(id)
    doc_ref.delete()


 
if __name__ == "__main__":
   uvicorn.run("main:app")



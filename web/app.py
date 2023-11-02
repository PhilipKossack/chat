from src.llm import build_llm
import requests
import json
print("start")
llm = build_llm()


from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any
import pickle
import os
from uuid import uuid4

import threading
import queue

class jobStatus():

    def __init__(self):
        self.jobsByToken = {}

    def addJob(self,token,uuid,prompt): #question, translate
        if token in self.jobsByToken:
            self.jobsByToken[token][uuid] = {'status':'queued','prompt':prompt} #'question':question 'translate':translate
        else:
            self.jobsByToken[token] = {uuid:{'status':'queued','prompt':prompt}} #'question':question, 'translate':translate
        
    def removeJob(self,token,uuid):
        if token in self.jobsByToken:
            if uuid in self.jobsByToken[token]:
                del self.jobsByToken[token][uuid]
                return True
        return False
    
    def addAnswer(self,token,uuid,answer):
        if token in self.jobsByToken:
            if uuid in self.jobsByToken[token]:
                self.jobsByToken[token][uuid]['answer'] = answer
                return True
        return False
    
    def updateStatus(self,token,uuid,status):
        if token in self.jobsByToken:
            if uuid in self.jobsByToken[token]:
                self.jobsByToken[token][uuid]['status'] = status
                return True
        return False
    
    def getJobStatus(self,token,uuid):
        if token in self.jobsByToken:
            if uuid in self.jobsByToken[token]:
                status = self.jobsByToken[token][uuid]
                status['uuid'] = uuid
                return self.jobsByToken[token][uuid]
        return {'uuid':'unknown','status':'unknown','prompt':'unknown','answer':'unknown'} #'question':'unknown' ,'translate':'unknown'
    
    def getAllJobsForToken(self,token):
        if token in self.jobsByToken:
            return self.jobsByToken[token]
        return {'unknown':{'status':'unknown','prompt':'unknown','answer':'unknown'}} #'question':'unknown' ,'translate':'unknown'

    def getAllStatus(self):
        return self.jobsByToken
            
  
class MainProcessor (threading.Thread):
    def __init__(self,taskLock,taskQueue):
        super().__init__(target="MainProcessor")
       
        self.taskLock = taskLock
        self.taskQueue = taskQueue
        
    '''
    def translate(self,inLang,outLang,text):
        req = {'from':inLang,'to':outLang,'source':text.strip()}
        print(text)
        print(text.strip())
        resp = requests.post('http://translate/api/translate',json=req)
        try:
            resp = json.loads(resp.text)
            if 'translation' in resp:
                return resp['translation']
            else:
                return False
        except:
            return False
    '''

    def run(self):
        while True:
            job = self.taskQueue.get(block=True)
            jobStat.updateStatus(job['token'],job['uuid'],"processing")
            item = jobStat.getJobStatus(job['token'],job['uuid'])
            #tPrompt=False
            #tQuestion=False
            #tAnswer=False
            '''
            if item['translate']:
                tPrompt = self.translate('de','en',item['prompt'])
                #tQuestion = self.translate('de','en',item['question'])
            '''
            instruction = item['prompt']
            prompt = f"Du bist ein hilfreicher Assistent. USER: {instruction} ASSISTANT:"

            '''
            if tPrompt: #and tQuestion:
                answer = None 
            else: '''

            answer = llm(prompt, temperature = 0.7, max_tokens = 1024, top_k=20, top_p=0.9,repeat_penalty=1.15)
            res = answer['choices'][0]['text'].strip()
            jobStat.addAnswer(job['token'],job['uuid'],res)
            
            jobStat.updateStatus(job['token'],job['uuid'],"finished")





def dumpTokens(tokens):
    pickle.dump(tokens, open("/config/tokens.pickle", "wb"))

try:
    tokens = pickle.load(open("/config/tokens.pickle", "rb"))
except (OSError, IOError) as e:
    tokens = {}
    dumpTokens(tokens)

def generate_token(quota,description = ""):
    token = uuid4().hex
    tokens[token]={'quota':quota,'description':description}
    dumpTokens(tokens)
    return token

def revoke_token(token):
    if token in tokens:
        del(tokens[token])
        dumpTokens(tokens)
        return "OK"
    else:
        return "Token tot found"

def check_token(token):
    if token in tokens:
        if tokens[token]['quota'] == -1:
            return True
        if tokens[token]['quota'] > 0:
            tokens[token]['quota'] -= 1
            return True    
    return False

def token_details(token):
    if token in tokens:
        return tokens[token]
    return {'quota':0,'description':'Not existent'}

supertoken = os.getenv('SUPERTOKEN')



jobStat = jobStatus()

taskLock = threading.Lock()
taskQueue = queue.Queue(1000)

thread = MainProcessor(taskLock,taskQueue)
thread.start()






app = FastAPI()

class Item(BaseModel):
    prompt: str
    #question: str
    token: str
    #translate: bool | None = False

class TokenCreation(BaseModel):
    supertoken: str
    quota: int | None = 100
    description: str | None = "unknown" 

class TokenRevoke(BaseModel):
    supertoken: str
    token: str

class Status(BaseModel):
    token: str
    uuid: str | None = "All"


@app.post("/getStatus/")
async def get_status(status: Status) -> Any:
    if status.uuid == "All":
        stat = jobStat.getAllJobsForToken(status.token)
    else:
        stat = jobStat.getJobStatus(status.token,status.uuid)
    return stat

@app.post("/createToken/")
async def create_token(token: TokenCreation) -> Any:
    if token.supertoken == supertoken:
        token = generate_token(token.quota,token.description)
        return {"token":token}
    else:
        return {"result": "Acces denied."}
    
@app.post("/revokeToken/")
async def create_token(token: TokenRevoke) -> Any:
    if token.supertoken == supertoken:
        result = revoke_token(token.token)
        return {"result": result}
    else:
        return {"result": "Acces denied."}

@app.post("/generate/")
async def generate_text(item: Item) -> Any:
    if(check_token(item.token)):
        uuid = uuid4().hex
        jobStat.addJob(item.token,uuid,item.prompt) #item.question,item.translate
        job = {'token':item.token,'uuid':uuid}
        try:
            taskQueue.put(job)
        except:
            jobStat.updateStatus(item.token,uuid,"failed")
        result = jobStat.getJobStatus(item.token,uuid)
    else:
        result = "Access denied."
    return result


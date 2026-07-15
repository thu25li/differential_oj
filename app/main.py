from fastapi import FastAPI
app=FastAPI(title='differential_OJ')
@app.get("/")
async def root():
    return{"code":200,"message":"ok","data":{"service":"oj"}}

**Steps to run intuitiveobjects-rag-client**
- install all node modules -> **npm install**
- update **.env**
- Start client app ->** npm run dev**

**Steps to run intuitiveobjects-rag-server**
- Create venv -> **python3 -m venv venv**
- Activate venv -> **source venv/bin/activate**
- update **.env**
- Install modules -> **pip install -r requierments.txt**
- Update **google.secret.json**
- run rabbitmq using this command -> docker run -d --name rabbitmq \
  -p 5672:5672 -p 15672:15672 \
  rabbitmq:3-management 
- To start the server app -> **make run**
- To  start the MD worker -> **python3 -m app.workers.md_upload_worker**
- To start raw pd uploader worker which helps doc upload from google drive -> **python3 -m app.workers.raw_upload_worker**
- Once you have uploaded pdfs from client and documents uploaded is completed, Run reterival files -> **python3 -m app.utils.pages_wise_metadata**
- Type search and ask your queries

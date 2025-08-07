GOOGLE DRIVE FILE UPLOAD

1. step connect google account 
    1.create project in google 
    2.create oauth client id
    3.store that token all in mongodb using fast api

2. list the google drive files and folders only show pdf files
    1. get the files and folders in googles drive if click folder show inside the folder files then nested show nested also create like.

3. queue the files rabbit mq
    1. then get the selected folder list and files if files more than 10 dont upload 
    2. if file grater than 10MB skip that file 
    3. if all correct create one record mongo db and with status
    4. queue the process

4. raw file upload.
    1.get file from queue then create hash that file if the file already exisit in the organization dont upload that
    2. upload the file in grid fs file then store the id in the document
    3. then move another queue for md conversion

5. md file conversion and vecotor db store.
    1. get the file from grid fs then move then convert to md file 
    2. upload the md file store in grid fs
    3. then convert chunk and store vecotor db

final.
   every process stored in database and update live notification frontend
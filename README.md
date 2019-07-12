# upload-flask
# build docker image
docker build -t upload-flask:v1 .

# run docker container
docker run -d -p 5002:5002 upload-flask:v1

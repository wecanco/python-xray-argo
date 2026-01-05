FROM python:3.10-alpine

WORKDIR /app

# Install dependencies first
RUN apk update && apk --no-cache add openssl bash curl unzip &&\
    pip install requests

# Copy only necessary files
COPY app.py main.py requirements.txt ./

EXPOSE 3000

# Make script executable
RUN chmod +x app.py

CMD ["python3", "app.py"]

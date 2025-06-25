# Use a lightweight Python image
FROM python:3.10-slim-buster

WORKDIR /usr/src/app

# Install system dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# upgrade pip
RUN pip install --upgrade pip

# Install workflows-cdk
RUN pip install git+https://github.com/stacksyncdata/workflows-cdk.git@prod

# Install Python dependencies
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy your app code
COPY . .

# Make sure entrypoint script is executable (if used)
RUN chmod +x ./config/entrypoint.sh

# Expose the port for Google Cloud Run
EXPOSE 8080

# Start the app using Gunicorn with config
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]




# make the entrypoint executable
# RUN chmod +x ./entrypoint.sh

# run the entrypoint to start the Guicorn production server
# ENTRYPOINT ["sh", "entrypoint.sh"]


# RUN in interactive mode
# UNIX: docker run --rm -p 2001:8080 -it -e ENVIRONMENT=dev -e REGION=besg -v $PWD:/usr/src/app/ workflows-app-example
# Windows: docker run --rm -p 2001:8080 -it -e ENVIRONMENT=dev -e REGION=besg -v ${PWD}:/usr/src/app/ workflows-app-example

# BUILD container
# docker build -t workflows-app-example . --build-arg ENVIRONMENT=dev
# docker build --no-cache -t workflows-app-example . --build-arg ENVIRONMENT=dev

# CONNECT to container terminal
# docker exec -it workflows-app-example bash

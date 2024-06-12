import os
import json
import boto3
import streamlit as st
from io import BytesIO
from botocore.exceptions import ClientError
from pycognito import Cognito
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Cognito settings
USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")

# AWS credentials
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

# Initialize AWS clients
session = boto3.Session(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name='us-east-1'
)
bedrock_client = session.client('bedrock-runtime')
s3 = session.client('s3')

# Streamlit app
st.title("Amazon Bedrock Titan Image Generator 1.0")

# User authentication
username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    try:
        user = Cognito(USER_POOL_ID, CLIENT_ID, client_secret=CLIENT_SECRET, username=username)
        user.authenticate(password=password)
        st.success("Logged in successfully!")
    except Exception as e:
        st.error(f"Login failed: {e}")

if 'user' in locals() and user.access_token:
    prompt = st.text_input("Enter a prompt to generate an image:")
    seed = st.number_input("Enter a seed value:", min_value=0, step=1)

    if st.button("Generate Image"):
        try:
            # Invoke the Titan Image Generator model
            response = bedrock_client.invoke_model(
                modelId="amazon.titan-image-generator-v1",
                contentType="application/json",
                accept="application/json",
                body=bytes(f',"taskType":"TEXT_IMAGE","imageGenerationConfig":{{"cfgScale":8,"seed":{seed},"quality":"standard","width":1024,"height":1024,"numberOfImages":3}}}}'.encode('utf-8'))
            )

            # Get the generated image
            image_data = response.get('OutputData', b'')

            # Save the image to S3
            bucket_name = "wdgomezimagegen"
            object_key = f"{prompt.replace(' ', '_')}.png"
            s3.put_object(Bucket=bucket_name, Key=object_key, Body=image_data)

            st.success(f"Image saved to s3://{bucket_name}/{object_key}")
        except ClientError as e:
            st.error(f"Error generating image: {e}")

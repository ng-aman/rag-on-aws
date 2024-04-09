import streamlit as st
import boto3
import re
import time

s3_bucket= 'genai-rag-on-aws'
s3_client = boto3.client('s3')

st.title('Opensearch DB file upload')

def format_pdf_file_name(input_string):
    # converting string to lower
    input_string= input_string.lower()

    # Define a regex pattern to match special characters
    pattern = r'[^\w\s.-]|_'
    # Replace special characters with "-"
    replaced_string = re.sub(pattern, '-', input_string)

    # Condense multiple consecutive dashes to a single dash
    condensed_string = re.sub(r'-+', '-', replaced_string)
    
    return condensed_string

def upload_file_to_s3(file, bucket_name, object_name):
    try:
        # Upload the file
        response = s3_client.upload_fileobj(file, bucket_name, object_name)
        # st.info(f"{file.name} uploaded successfully to s3")
        return True
    except Exception as e:
        # st.error(f"Error uploading {file.name} to s3: {e}")
        return False

def pdf_file_check(file_name):
    return file_name.endswith('.pdf')

def check_files_in_folder(bucket_name, folder_name):
    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket_name, 
            Prefix=folder_name
            )
        if 'Contents' in response:
            return True
        else:
            return False
    except:
        return False

def check_for_status(bucket_name, folder_name, wait_time= 180):
    start= time.time()
    result= True
    while result:
        if check_files_in_folder(bucket_name, folder_name):
            response= s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_name)
            return 'success' in response['Contents'][0]['Key']
        else:
            end = time.time()
            if int(end-start) < wait_time:
                # wait for some time and try again for file
                time.sleep(15)
            else:
                return False
    
# streamlit fileupload
def main():
    file= st.file_uploader("Upload pdf here")
    if file is not None:
        if pdf_file_check(file.name):
            # fetching s3 bucket folder and file names
            file_name= format_pdf_file_name(file.name)
            folder_name= file_name.split('.pdf')[0]
            object_name= f'pdf_files/{folder_name}/{file_name}'
            # upload file to s3
            if st.button("Upload"):
                # Initialize progress bar and text
                progress_text = st.empty()
                percent_complete= 0
                progress_bar = st.progress(percent_complete)
                # Execute steps
                event1= upload_file_to_s3(file, s3_bucket, object_name)  # s3 file upload
                if event1:
                    percent_complete+= 33
                    progress_text.text("file uploaded to s3")
                    progress_bar.progress(percent_complete)
                else:
                    progress_text.text("s3 file upload is failed")
                    st.error('Job failed')
                
                # checking for index_creation
                if event1:                          # progress to event2 if event1 succeeds
                    s3_folder= f'pdf_files/{folder_name}/index_creation'
                    event2= check_for_status(s3_bucket, s3_folder, wait_time= 180)
                    if event2:
                        percent_complete+= 33
                        progress_bar.progress(percent_complete)
                        progress_text.text("opensearch vectordb index is created")
                    else:
                        progress_text.text("opensearch vectordb index creation is failed")
                        st.error('Job failed')

                # checking for uploading embeddings
                if event1 and event2:             # progress to event3 if event1, event2 succeeds
                    s3_folder= f'pdf_files/{folder_name}/upload_embeddings'
                    event3= check_for_status(s3_bucket, s3_folder, wait_time= 180)
                    if event3:
                        percent_complete+= 34
                        progress_bar.progress(percent_complete)
                        progress_text.text("Embeddings uploaded")
                        st.success(f"embeddings created with name 'index-{folder_name}'")
                    else:
                        progress_text.text("Inserting Embeddings failed")
                        st.error('Job failed')
        else:
            st.error("Please upload pdf only")
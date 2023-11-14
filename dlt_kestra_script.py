import json
import requests
import openai
import os
from google.cloud import bigquery
from google.cloud.exceptions import Conflict
from google.oauth2.service_account import Credentials

import dlt
from inbox import inbox_source  # Adjust import as needed

def initialize_bigquery_client():
    """
    Initialize a BigQuery client with service account authentication.

    Returns:
        google.cloud.bigquery.Client: An authenticated BigQuery client instance.
    """

    private_key_str = os.environ['DESTINATION__BIGQUERY__CREDENTIALS__PRIVATE_KEY'].replace('\\n', '\n') # replace escaped newlines with actual newlines
    service_account_info = {
        "type": "service_account",
        "project_id": os.environ['DESTINATION__BIGQUERY__CREDENTIALS__PROJECT_ID'],
        "private_key": private_key_str,
        "client_email": os.environ['DESTINATION__BIGQUERY__CREDENTIALS__CLIENT_EMAIL'],
        "token_uri": "https://oauth2.googleapis.com/token",  # This is the standard token URI for Google APIs,
    }
    credentials = Credentials.from_service_account_info(service_account_info)
    return bigquery.Client(credentials=credentials, project=credentials.project_id)

def create_summary_table(client, dataset_name, table_name):
    """
    Create a summary table in BigQuery.

    Args:
        client (google.cloud.bigquery.Client): A BigQuery client instance.
        dataset_name (str): Name of the dataset.
        table_name (str): Name of the table.

    This function creates a new table in BigQuery for storing email summary and sentiment data.

    Raises:
        google.api_core.exceptions.Conflict: If the table already exists.
    """

    table_id = f"{client.project}.{dataset_name}.{table_name}"
    schema = [
        bigquery.SchemaField("email_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("summary", "STRING"),
        bigquery.SchemaField("sentiment", "STRING"),
        bigquery.SchemaField("date", "TIMESTAMP"),
    ]
    table = bigquery.Table(table_id, schema=schema)
    try:
        client.create_table(table)  # Make an API request.
        print(f"Created table {table_id}.")
    except Conflict:
        print(f"Table {table_id} already exists.")

def send_slack_message(slack_webhook_url, message_text):
    """
    Send a message to Slack using a webhook.

    Args:
        slack_webhook_url (str): The URL of the Slack webhook.
        message_text (str): The text of the message to send.

    This function sends a message to a Slack channel using a webhook URL.
    
    Raises:
        ValueError: If the Slack request returns an error.
    """

    data = {'text': message_text}
    response = requests.post(slack_webhook_url, data=json.dumps(data), headers={'Content-Type': 'application/json'})
    if response.status_code != 200:
        raise ValueError(f'Request to Slack returned an error {response.status_code}, the response is:\n{response.text}')

def get_last_emails(load_info):
    """
    Retrieve the latest email records from BigQuery based on load information.

    Args:
        load_info (object): Information about the data load, including load IDs and dataset name.

    This function constructs and executes an SQL query to retrieve email records from
    BigQuery filtered by the latest load ID provided in the `load_info` object.

    Returns:
        google.cloud.bigquery.QueryJobResult: A result object containing the filtered email records.
    """

    load_id = load_info.loads_ids[0]
    dataset_name = load_info.dataset_name
    query = f"""SELECT * FROM `{dataset_name}.{table_name}` WHERE _dlt_load_id = @load_id"""
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
        bigquery.ScalarQueryParameter("load_id", "STRING", load_id),
        ]
    )
    query_job = client.query(query, job_config=job_config)
    return query_job.result()

def summarize_email(body):
    """
    Summarize email content using AI.

    Args:
        body (str): The email content to summarize.

    Returns:
        str: A concise summary of the email content.
    """

    prompt = f"Summarize the email content in one sentence with less than 30 words: {body}"
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a tool that summarizes emails."},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message["content"]

def analyze_sentiment(body):
    """
    Analyze email sentiment using AI.

    Args:
        body (str): The email content for sentiment analysis.

    Returns:
        str: One-word sentiment analysis result.
    """
    
    prompt = f"Analyze the sentiment of the following email and reply only with one word: {body}"
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a tool that analyzes email sentiment."},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message["content"]

def prepare_data_for_insertion(row, summary, sentiment):
    """
    Prepare email data for database insertion.

    Args:
        row (object): Email message details.
        summary (str): Email summary.
        sentiment (str): Sentiment analysis result.

    Returns:
        dict: A dictionary with formatted data for insertion.
    """
        
    return {
        "email_id": row.message_uid,
        "summary": summary,
        "sentiment": sentiment,
        "date": row.date.isoformat()
    }

# Set openAI and Slack credentials from the environment
openai.api_key = os.getenv('OPENAI_API')
slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')

# Initialize the BigQuery client
client = initialize_bigquery_client()

# Create a table for storing summaries and sentiment analysis results in BigQuery
create_summary_table(client, "messages_data", "summary_sentiment")

# Run dlt pipeline to load email data from gmail to BigQuery
pipeline = dlt.pipeline(
    pipeline_name="standard_inbox",
    destination='bigquery',
    dataset_name="messages_data",
    full_refresh=False,
)

# Set table name
table_name = "my_inbox"
# Get messages resource from the source
messages = inbox_source().messages
# Configure the messages resource to get bodies of the emails
messages = messages(include_body=True).with_name(table_name)
# Load data to "my_inbox" table
load_info = pipeline.run(messages)

# Check if new email data was loaded
if len(load_info.loads_ids) == 0:
    send_slack_message(slack_webhook_url, "No new emails in the last hour so far.\n" + '-'*50)
    exit()

# Get data of emails that were loaded last
last_emails = get_last_emails(load_info)

# Initialize a list to store summaries and sentiment analysis results
rows_to_insert = []

# Process emails using openAI
for row in last_emails:
    summary = summarize_email(row.body)
    sentiment = analyze_sentiment(row.body)
    message_text = f"*Subject*: {row.subject}\n*Sender:* {row['from']}\n*Summary:* {summary}\n*Sentiment:* {sentiment}\n*Date:* {row.date}\n{'-'*50}"    
    send_slack_message(slack_webhook_url, message_text)
    rows_to_insert.append(prepare_data_for_insertion(row, summary, sentiment))

# Insert summaries and sentiment analysis results in batch to the "summary_sentiment" table
errors = client.insert_rows_json(
    f"{client.project}.messages_data.summary_sentiment",  # Make sure to use the correct table path
    rows_to_insert
)

if errors == []:
    print("New rows have been added to the summary table.")
else:
    print("Encountered errors while inserting rows: {}".format(errors))
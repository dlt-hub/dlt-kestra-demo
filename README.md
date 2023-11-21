# From Inbox to Insights: AI-enhanced email analysis with dlt and Kestra

## Overview

This is a demo project that shows the orchestration of a workflow in Kestra. It demonstrates the process of loading data from Gmail into BigQuery using `dlt` (Data Loading Tool) and includes AI analysis, specifically for summarization and sentiment asessment.

![Overview of project demo](dlt-kestra-demo.png)

The diagram above represents the Kestra flow of the project, encompassing the following steps:

1. Data ingestion from Gmail to BigQuery utilizing `dlt`.
2. Data analysis for summarization and sentiment assessment using OpenAI, with the results stored in BigQuery.
3. Sharing of the outcomes to Slack.

## Prerequisites

1. Gmail credentials
    - IMAP server hostname (default for Gmail is `imap.gmail.com`)
    - Gmail account email
    - App password

    :::note
    For the app pasword, refer to Gmail's [official guidelines](https://support.google.com/mail/answer/185833?hl=en#:~:text=An%20app%20password%20is%20a,2%2DStep%20Verification%20turned%20on).
    :::
2. BigQuery credentials
    - Project ID
    - Private key
    - Client email
    
    :::note
    Learn more about obtaining BigQuery credentials in `dlt`'s [documentation](https://dlthub.com/docs/dlt-ecosystem/destinations/bigquery).
    :::

3. OpenAI API key
    
    :::note
    If you're new to [OpenAi](https://platform.openai.com/), they offer $5 in free credits usable during your first 3 months.
    :::

4. Slack credentials
    - Webhook URL

    :::note
    Follow Slack's [guidelines](https://api.slack.com/messaging/webhooks) to obtain your webhook URL.
    :::

## Setup

1. **Create a Virtual Environment**: It's advised to create a virtual environment to maintain a clean workspace and prevent dependency conflicts, although this is not mandatory.

2. **Create an .env File**: Within your repository, generate an ``.env`` file to securely store credentials in base64 format. Prefix each secret with 'SECRET_' in order for Kestra's [`secret()`](https://kestra.io/docs/developer-guide/variables/function/secret) function to work. For seamless integration, specifically name your Gmail and BigQuery credentials as follows to align with the `dlt` pipeline's automatic detection:

    ```env
    SECRET_GMAIL_HOST=someSecretValueInBase64
    SECRET_GMAIL_EMAIL_ACCOUNT=someSecretValueInBase64
    SECRET_GMAIL_PASSWORD=someSecretValueInBase64
    SECRET_BIGQUERY_PROJECT_ID=someSecretValueInBase64
    SECRET_BIGQUERY_PRIVATE_KEY=someSecretValueInBase64
    SECRET_BIGQUERY_CLIENT_EMAIL=someSecretValueInBase64
    SECRET_OPENAI_API=someSecretValueInBase64
    SECRET_SLACK_WEBHOOK_URL=someSecretValueInBase64

    ```

   :::note
   The base64 format is required because Kestra mandates it.
   :::

3. **Download Docker Desktop**: As recommended by Kestra, download and install Docker Desktop.

4. **Ensure Docker is Running**: Verify that Docker is active. You can start Kestra with a single command using Docker:
   ```bash
   docker run --pull=always --rm -it -p 8080:8080 --user=root -v /var/run/docker.sock:/var/run/docker.sock -v /tmp:/tmp kestra/kestra:develop-full server local
5. **Configure Docker Compose File**: Modify your Docker Compose file to include the ``.env`` file:

    ```yaml
    kestra:
        image: kestra/kestra:develop-full
        env_file:
            - .env
    ``` 

6. **Enable Auto-Restart in Docker Compose**: Add ``restart: always`` to the `postgres` and `kestra` services in your `docker-compose.yml`. This ensures they automatically restart after a system reboot:

    ```yaml
    postgres:
        image: postgres
        restart: always
    ```

    ```yaml
    kestra:
        image: kestra/kestra:latest-full
        restart: always
    ```

7. **Access Kestra UI**: Launch http://localhost:8080/ to open the Kestra UI.

## Create Your Flow
1. **Navigate to Flows**: On the left side menu, click on 'Flows', then click 'Create Flow' in the bottom right corner.
2. **Copy and Paste YAML Code**: Copy the YAML code from `dlt_kestra_demo.yml` and paste it into the editor in Kestra.
3. **Save Your Flow**: After pasting the code, save your flow.

## Understand Your Flow
In Kestra, each flow consists of three required components:
- **`id`**: Represents the name of the flow.
- **`namespace`**: Can be used to separate development and production environments.
- **`tasks`**: A list of tasks to be executed in the order they are defined. Each task in `tasks` must contain an `id` and a `type`. Our flow is of the 'scripts' type, which means it runs scripts in Docker containers or local processes – in this case, within a Docker container.

The tasks section includes the following:
1. **The `beforeCommands` Section**: Outlines initial setup commands executed in a Python 3.11 Docker environment, preparing the environment with necessary dependencies.
2. **`warningOnStdEr`**: Set to `false` to ensure that warnings are not treated as critical errors.
3. **The `env` Block**: Defines environment variables, providing essential credentials.

   :::note
   The variable names for Gmail and BigQuery credentials match the `dlt` pipeline's requirements, allowing automatic detection and use of these credentials.
   :::

4. **The `script` Section**: Contains a Python script with the core functionality of the Kestra flow. The script is divided into multiple functions, each with a specific purpose. For more details, refer to the explanatory comments in the `dlt_kestra_script.py` file.

5. **The `Triggers` Part**: Includes a trigger set to run every hour. To address the default backfill behavior, we use the `lateMaximumDelay` property set to 1 hour and 10 minutes. This configuration ensures that tasks missed during system downtime will not be executed if the delay exceeds this duration, preventing unnecessary catch-up runs.

## Understand your pipeline

As you have noticed, there are two commands in the beforeCommands section that are essential for running the pipeline:
    
1. **``pip install "dlt[bigquery]"``**: Installs the `dlt` library along with the dependencies required for the BigQuery destination. 

2. **``dlt --non-interactive init inbox bigquery``**: Initializes the pipeline that loads data from the inbox verified source to BigQuery.

    :::note
    A verified source is a data source that is regularly tested and maintained by `dlt`.
    :::

The pipeline is then created and executed as outlined in the `script` section:

```python
# Run dlt pipeline to load email data from gmail to BigQuery
pipeline = dlt.pipeline(
    pipeline_name="standard_inbox",
    destination='bigquery',
    dataset_name="messages_data",
    full_refresh=False, # Load only new data
)

# Set table name
table_name = "my_inbox"
# Get messages resource from the source
messages = inbox_source().messages
# Configure the messages resource to get bodies of the emails
messages = messages(include_body=True).with_name(table_name)
# Load data to "my_inbox" table
load_info = pipeline.run(messages)
```

Additional parameters, such as specifying the email folder or a start date, can be passed to the `inbox_source()` function. For more detailed information on these parameters and other aspects of the `dlt` library, refer to `dlt`'s official [documentation](https://dlthub.com/docs/dlt-ecosystem/verified-sources/inbox).

## Email Summary and Sentiment Analysis

The rest of the script automates the processing of new email data and updates the table containing summaries and sentiment analyses. The process involves the following steps:

1. **Check for New Email Data**: The script first verifies whether new email data has been loaded. If there are no new emails, a notification is sent to a predefined Slack channel, and the script terminates.
2. **Retrieve and Process New Emails**: The latest emails are retrieved and processed. This includes:
    - Summarizing the content of each email.
    - Performing sentiment analysis on the email content.
3. **Notify via Slack**: For each processed email, a detailed message including the email's summary and sentiment analysis is sent to Slack. This message also includes the email's subject, sender, and date.
4. **Prepare Data for Insertion**: The summarized and sentiment-analyzed data for each email is prepared for database insertion. This data includes the email's details along with the generated summary and sentiment analysis results.
5. **Batch Insertion into Database**: The prepared data is batch-inserted into the "summary_sentiment" table in the database. This step ensures that the data is systematically added to the database for easy access and analysis.

## Execute your flow
To execute a flow in Kestra after setting up the YAML file, simply click on `New execution` located in the bottom right corner of the Kestra interface. This action initiates the flow. You can then monitor its progress and review outputs directly through the Kestra UI.

## Contact / Support
For guidance on running custom pipelines with `dlt` or orchestrating flows in Kestra, consider joining their Slack communities:

- [dltHub](https://dlthub-community.slack.com)
- [Kestra](https://kestra-io.slack.com)

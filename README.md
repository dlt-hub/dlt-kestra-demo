# From Inbox to Insights: AI-enhanced email analysis with dlt and Kestra

## Overview

This is a demo project that shows the orchestration of a workflow in Kestra. It demonstrates the process of loading data from Gmail into BigQuery using dlt (Data Loading Tool) and includes AI analysis, specifically for summarization and sentiment asessment.

![Overview of project demo](dlt-kestra-demo.png)

The diagram above represents the Kestra flow of the project, encompassing the following steps:

1. Data ingestion from Gmail to BigQuery utilizing dlt.
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

2. **Create an .env File**: In your working repository, create an .env file and store your credentials in base64 format. Ensure that all secrets are prefixed with 'SECRET_'.

   :::note
   The base64 format is required because Kestra mandates it.
   :::

3. **Download Docker Desktop**: As recommended by Kestra, download and install Docker Desktop.

4. **Ensure Docker is Running**: Verify that Docker is active. You can start Kestra with a single command using Docker:
   ```bash
   docker run --pull=always --rm -it -p 8080:8080 --user=root -v /var/run/docker.sock:/var/run/docker.sock -v /tmp:/tmp kestra/kestra:develop-full server local

5. **Configure Docker Compose File**: Modify your Docker Compose file to include the .env file:

    ```yaml
    kestra:
        image: kestra/kestra:develop-full
        env_file:
            - .env
    ``` 
6. **Access Kestra UI**: Launch http://localhost:8080/ to open the Kestra UI.

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

5. Triggers (TBA)

## Understand your pipeline

(TBA)




## Execute your flow

1. Click new execution

(TBA)

## Contact / Support

# From Inbox to Insights: AI-enhanced email analysis with dlt and Kestra

## Overview

This is a demo project that shows the orchestration of a workflow in Kestra. It demonstrates the process of loading data from Gmail into BigQuery using dlt (Data Loading Tool) and includes AI analysis, specifically for summarization and sentiment asessment.

![Overview of project demo](dlt-kestra-demo.png)

The diagram above represents the Kestra flow of the project, encompassing the following steps:

1. Data ingestion from Gmail to BigQuery utilizing dlt.
2. Data analysis for summarization and sentiment assessment using OpenAI, with the results stored in BigQuery.
3. Sharing of the outcomes to Slack.

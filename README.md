# Attempt_ApacheAirflow
Exploring and creating workflows in Apache Airflow workflows

Apache Airflow is python-based workflow based management system developed by Airbnb.<br>
Workflows can be used to automate the pipelines, ETL process. It uses Directed Acyclic Graphs (DAGs) to define worfklows.<br>
A brief understanding of [Airflow DAGs](https://www.astronomer.io/guides/dags/).

**Note**:<br>
Airflow scheduler runs the DAGs for the given/scheduled time, if the DAG run is successfull we cannot trigger for the same timestamp.

Further reading can be done here - <br>
[1]: https://airflow.apache.org/docs/stable/index.html <br>
[2]: [Airflow Operators and Hooks](https://github.com/lowks/Airflow/blob/master/docs/tutorial.rst)
[3]: [Snowflake connector](https://docs.snowflake.net/manuals/user-guide/python-connector.html)
[4]: [Connecting to Snowflake using Airflow](https://itnext.io/connect-apache-airflow-to-snowflake-data-warehouse-37936a9edfa1)

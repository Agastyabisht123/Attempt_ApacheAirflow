import logging
import snowflake.connector
from datetime import datetime, timedelta
from airflow import DAG
from airflow.hooks.base_hook import BaseHook
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
from airflow import AirflowException
from airflow.utils.email import send_email_smtp
from airflow.contrib.operators.slack_webhook_operator import SlackWebhookOperator
import statsd

# Statsd
# TCP connection
# statsd_client = statsd.TCPStatsClient('localhost', 8125, prefix='AirFlow')
# UDP connection
statsd_client = statsd.StatsClient('localhost', 8125, prefix='AirFlow')
# Logging 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

default_args = {
    'owner' : 'airflow',
    'retries' : 1,
    'retry_delay' : timedelta(minutes = 2)
    # 'email_on_failure' : True,
    # 'email_on_success' : True,
    # 'email' : ['karan.nadagoudar@datagrokr.com']
}

# Snowflake information
# Information must be stored in connections
# It can be done with Airflow UI - 
# Admin -> Connections -> Create
database_name = 'DEMO_DB'
schema_name = 'public'
snowflake_username = BaseHook.get_connection('snowflake_sql').login
snowflake_password = BaseHook.get_connection('snowflake_sql').password
snowflake_account = BaseHook.get_connection('snowflake_sql').host

dag = DAG(
    dag_id="sample_snowflake_procedures", 
    default_args=default_args,
    start_date=days_ago(1),
    schedule_interval='*/20 * * * *',
    catchup=False
)

def send_slack_notification(context):
    SLACK_CONN_ID = 'slack_conn'
    slack_webhook_token = BaseHook.get_connection(SLACK_CONN_ID).password
    slack_msg = """
            :red_circle: Task Failure 
*Task*: {task}  
*Dag*: {dag}
*Start Time*: {start_date}
*Log Url*: {log_url} 
            """.format(
            task=context.get('task_instance').task_id,
            dag=context.get('task_instance').dag_id,
            start_date=context.get('task_instance').start_date,
            log_url=context.get('task_instance').log_url,
        )
    alert = SlackWebhookOperator(
        task_id='slack_notify',
        http_conn_id=SLACK_CONN_ID,
        webhook_token=slack_webhook_token,
        message=slack_msg,
        username='airflow'
        )
    return alert.execute(context=context)

def send_email(context):
    subject = "[Airflow] DAG {0} - Task {1}: Success".format(
        context['task_instance_key_str'].split('__')[0],
        context['task_instance_key_str'].split('__')[1]
        )
    html_content = """
    DAG: {0}<br>
    Task: {1}<br>
    Succeeded on: {2}
    """.format(
        context['task_instance_key_str'].split('__')[0],
        context['task_instance_key_str'].split('__')[1],
        datetime.now()
        )
    send_email_smtp('karan.nadagoudar@datagrokr.com', subject, html_content)

# Check the execution time of the task
@statsd_client.timer('load_merge_table.time')
def load_merge_table(**context):
    con = snowflake.connector.connect(user = snowflake_username, \
        password = snowflake_password, account = snowflake_account, \
        database=database_name, schema=schema_name)
    cs = con.cursor()

    load_sql = "call mergetableProc();"
    
    try:
        status = cs.execute(load_sql).fetchall()[0][0]
        if status == 'Done.':
            logger.info("Procedure executed successfully")
        else:
            logger.error("Procedure failed with {}".format(str(status)))
            raise AirflowException("Failed procedure run.")
    except Exception as ex:
        logger.error("Procedure failed with {}".format(str(ex)))
        raise AirflowException("Failed procedure run.")
    finally:
        cs.close()
    
@statsd_client.timer('drop_merge_table.time')
def drop_merge_table(**context):
    con = snowflake.connector.connect(user = snowflake_username, \
        password = snowflake_password, account = snowflake_account,\
        database=database_name, schema=schema_name)
    cs = con.cursor()

    drop_sql = "call dropmergetableProc();"
    
    try:
        status = cs.execute(drop_sql).fetchall()[0][0]
        if status == 'Done.':
            logger.info("Procedure executed successfully")
        else:
            logger.error("Procedure failed with {}".format(str(status)))
            raise AirflowException("Failed procedure run.")
    except Exception as ex:
        logger.error("Procedure failed with {}".format(str(ex)))
        raise AirflowException("Failed procedure run.")
    finally:
        cs.close()


with dag:
    load_table = PythonOperator(
        task_id="load_merge_table",
        python_callable=load_merge_table,
        on_failure_callback=send_slack_notification
    )

    drop_table = PythonOperator(
        task_id="drop_merge_table", 
        python_callable=drop_merge_table,
        on_failure_callback=send_slack_notification
    )

load_table >> drop_table
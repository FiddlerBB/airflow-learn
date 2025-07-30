FROM apache/airflow:3.0.3

COPY requirements.txt .

RUN pip install -r requirements.txt && \
    pip install "apache-airflow[celery]==3.0.3" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-3.0.3/constraints-3.9.txt"
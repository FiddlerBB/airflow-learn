FROM apache/airflow:3.0.3-python3.12

COPY requirements.txt .
# RUN pip install -r requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir "apache-airflow[celery]==3.0.3" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-3.0.3/constraints-3.12.txt"
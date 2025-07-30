from __future__ import annotations
from module.sessions import RandomUserAgentSession
import polars as pl
import logging
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from selectolax.parser import HTMLParser
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow import DAG
from airflow.decorators import dag, task
from datetime import datetime, timedelta
import boto3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class GoldCrawler:
    __slots__ = ("headers", "session", "proxy", "timeout")

    def __init__(self, proxy=None, timeout=10, random_user_agent=True):
        self.session = RandomUserAgentSession() if random_user_agent else requests.Session()
        self.proxy = proxy
        self.timeout = timeout

        retries = Retry(
            total=5,
            backoff_factor=2,  # Exponential backoff
            status_forcelist=[429, 500, 502, 503, 504],
        )

        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    def get_html_data(self, url):
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching HTML data: {e}")
            return None
        
    def parse_table(self, html_data: HTMLParser):
        table = html_data.css_first("table[class='gia-vang-search-data-table']")
        rows = table.css("tr")
        out = []
        for row in rows:
            cells = row.css("td")
            gold_idx = cells[0].text().strip().lower().replace(' ', '_')
            buy_price = list(cells[1].text().strip().split())[0].replace(',', '')
            sell_price = list(cells[2].text().strip().split())[0].replace(',', '')
            yesterday_buy_price = cells[3].text().strip().replace(',', '')
            yesterday_sell_price = cells[4].text().strip().replace(',', '')
            # print(f"Buy Price: {buy_price}")
            # print(f"Sell Price: {sell_price}")
            # print(f"Yesterday Buy Price: {yesterday_buy_price}")
            # print(f"Yesterday Sell Price: {yesterday_sell_price}")
            out.append({
                "gold_idx": gold_idx,
                "buy_price": buy_price,
                "sell_price": sell_price,
                "yesterday_buy_price": yesterday_buy_price,
                "yesterday_sell_price": yesterday_sell_price
            })
        df = pl.DataFrame(out, schema={
            "gold_idx": pl.String,
            "buy_price": pl.Int64,
            "sell_price": pl.Int64,
            "yesterday_buy_price": pl.Int64,
            "yesterday_sell_price": pl.Int64
        })
        out = out[0]
        return {'gold_idx': out['gold_idx'], 
                'buy_price': out['buy_price'],
                'sell_price': out['sell_price'],
                'yesterday_buy_price': out['yesterday_buy_price'],
                'yesterday_sell_price': out['yesterday_sell_price']}

    def parse_chart(self, html: HTMLParser):
        chart = html.css_first("div[class='cate-24h-gold-pri-chart'] > script[type='text/javascript']")
        dates = chart.text().split('categories: [')[1].split(']')[0].replace("'", "").split(',')
        buy_in = chart.text().split('data: [')[1].split(']')[0].split(',')
        sell_out = chart.text().split('data: [')[2].split(']')[0].split(',')
        df = pl.DataFrame({
            "date": dates,
            "buy_in": buy_in,
            "sell_out": sell_out
        })
        df = df.with_columns([
            pl.col("buy_in").cast(pl.Int64),
            pl.col("sell_out").cast(pl.Int64)
        ])
        print(df.head())
    
default_args={
        'retries': 3,
        'retry_delay': timedelta(minutes=5),
        'retry_exponential_backoff': True,
        'max_retry_delay': timedelta(minutes=30),
    }

@dag(
    start_date=datetime(2024, 1, 1),
    schedule='0 9 * * *',
    catchup=False,
    tags=['gold', 'taskflow'],
    default_args=default_args
)
def gold_scrape():
    gold_crawler = GoldCrawler()
    @task()
    def get_html_data_task():
        url = "https://www.24h.com.vn/gia-vang-hom-nay-c425.html"
        logger.info(f"Fetching HTML data from {url}")
        html_data = gold_crawler.get_html_data(url)
        # html_data = HTMLParser(html_data)
        return html_data

    @task()
    def parse_gold_prices_task(html_data):
        logger.info(f"Parse gold prices")
        html_data = HTMLParser(html_data)
        gold_data = gold_crawler.parse_table(html_data)
        return gold_data
    
    @task()
    def print_gold_prices(gold_data):
        logger.info(f"Gold prices: {gold_data}")

    @task()
    def parse_chart(html_data):
        html_data = HTMLParser(html_data)
        gold_crawler.parse_chart(html_data)


    @task()
    def assume_role():
        sts_client = boto3.client("sts")
        assumed_role = sts_client.assume_role(
            RoleArn="arn:aws:iam::123456789012:role/MyCrossAccountRole",
            RoleSessionName="airflow-session"
        )

        credentials = assumed_role["Credentials"]
        return {
            "aws_access_key_id": credentials["AccessKeyId"],
            "aws_secret_access_key": credentials["SecretAccessKey"],
            "aws_session_token": credentials["SessionToken"],
        }
    

    @task()
    def send_sns(gold_data, creds):
        session = boto3.Session(
            aws_access_key_id=creds["aws_access_key_id"],
            aws_secret_access_key=creds["aws_secret_access_key"],
            aws_session_token=creds["aws_session_token"],
        )

        sns_client = session.client('sns', 'us-east-1')
        sns_arn = 'arn:aws:sns:us-east-1:174227742216:gold-scrape-topic'
        message = f"Gold data for today: {gold_data['buy_price']} - {gold_data['sell_price']}"
        sns_client.publish(
            TargetArn=sns_arn,
            Message=message,
            Subject='Gold Data'
        )
    
    html_data = get_html_data_task()
    gold_data = parse_gold_prices_task(html_data)
    print_gold_prices(gold_data)
    parse_chart(html_data)
    creds = assume_role()
    send_sns(gold_data, creds)

etl_dag = gold_scrape()

    
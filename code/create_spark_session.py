# Import Python modules
import os
import sys

# Set path
os.environ['SPARK_HOME'] = '/usr/lib/spark'
sys.path.append('/usr/lib/spark/python')
sys.path.append('/usr/lib/spark/python/lib/py4j-0.10.4-src.zip')

# Import PySpark modules
from pyspark.sql import SparkSession

def create_spark_session():

    spark_session = SparkSession.builder.appName('spark_parallel_forecasting')\
        .master('yarn').getOrCreate()

    return spark_session
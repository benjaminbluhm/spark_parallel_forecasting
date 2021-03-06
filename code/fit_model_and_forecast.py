# Import python modules
import s3fs
import joblib
import s3io
import boto
import pandas as pd
import numpy as np
from fastparquet import ParquetFile, write
from statsmodels.tsa.arima_model import ARMA

def fit_model_and_forecast(id_list, config):

    # Cast collection of distinct time series IDs into Python list
    id_list = list(id_list)

    # Open connections to S3 File System
    s3 = s3fs.S3FileSystem()
    s3_open1 = s3.open
    s3_open2 = boto.connect_s3(host=config['s3_host'])

    # Loop over time series IDs
    for i, id in enumerate(id_list):

        # Determine S3 file path and load data into pandas dataframe
        file_path = s3.glob(config['path_training_data_parquet'] + 'ID=' + str(id) +
                            '/*.parquet')
        df_data = ParquetFile(file_path,open_with=s3_open1).to_pandas()

        # Sort time series data according to original ordering
        df_data = df_data.sort_values('ORDER')

        # Initialize dataframe to store forecast
        df_forecasts = pd.DataFrame(np.nan, index=range(0, config['len_eval']),
                                    columns=['FORECAST'])

        # Add columns with ID, true data and ordering information
        df_forecasts.insert(0, 'ID', id, allow_duplicates=True)
        df_forecasts.insert(1, 'ORDER', np.arange(1, config['len_eval'] + 1))
        df_forecasts.insert(2, 'DATA', df_data['DATA'][range((config['len_series'] -
                                                              config['len_eval']),
                                                             config['len_series'])].values,
                                                             allow_duplicates=True)

        # Loop over successive estimation windows
        for j, train_end in enumerate(range((config['len_series'] - config['len_eval'] - 1),
                                            (config['len_series'] - 1))):

            # Fit ARMA(2,2) model and forecast one-step ahead
            model = ARMA(df_data['DATA'][range(0, train_end+1)], (2, 2)).fit(disp=False)
            df_forecasts.at[j, 'FORECAST'] = model.predict(train_end+1, train_end+1)

        # Write dataframe with forecast to S3 in Parquet file format
        path = config['path_forecasts'] + 'ID=' + str(id) + '.parquet'
        write(path, df_forecasts, write_index=False, append=False, open_with=s3_open1)

        # Save fitted ARMA model to S3 in pickle file format
        path = config['path_models'] + 'ID=' + str(id) + '.model'
        with s3io.open(path, mode='w', s3_connection=s3_open2) as s3_file:
            joblib.dump(model, s3_file)


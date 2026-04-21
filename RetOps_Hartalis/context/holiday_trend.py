import pandas as pd

URL_DATA = 'https://storage.dosm.gov.my/iowrt/iowrt_3d.parquet'
URL_METADATA = 'https://storage.dosm.gov.my/technotes/iowrt.pdf'
df = pd.read_parquet(URL_DATA)
df['date'] = pd.to_datetime(df['date'])
df['month'] = df['date'].dt.month

monthly_avg = df[df['series'] == 'abs'].groupby('month')['sales'].mean()
baseline = monthly_avg[[4, 6, 7, 9]].mean()  
lift = (monthly_avg - baseline) / baseline * 100
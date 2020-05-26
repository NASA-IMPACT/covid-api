from covid_api.core.config import INDICATOR_BUCKET, DT_FORMAT
import boto3
import csv
import json
from datetime import datetime
from typing import Dict

s3 = boto3.client('s3')

def s3_get(bucket, key):
    response = s3.get_object(Bucket=bucket, Key=key)
    return response["Body"].read()

def indicator_folders():
    response = s3.list_objects_v2(
        Bucket=INDICATOR_BUCKET,
        Prefix=f'indicators/',
        Delimiter='/',
    )
    return [obj['Prefix'].split('/')[1] for obj in response['CommonPrefixes']]

def _dt(d: Dict) -> datetime:
    return datetime.strptime(d["date"], DT_FORMAT)

def _di(d: Dict):
    return d["indicator"]

def get_indicators(identifier):
    indicators = []
    for folder in indicator_folders():
        try:
            data = []
            metadata_json = s3_get(INDICATOR_BUCKET, f"indicators/{folder}/metadata.json")
            metadata_dict = json.loads(metadata_json.decode('utf-8'))

            indicator_csv = s3_get(INDICATOR_BUCKET, f"indicators/{folder}/{identifier}.csv")
            indicator_lines = indicator_csv.decode('utf-8').split()
            reader = csv.DictReader(
                indicator_lines,
            )
            for row in reader:
                date = datetime.strptime(
                    row[metadata_dict['date']['column']],
                    metadata_dict['date']['format']
                ).strftime(DT_FORMAT)

                indicator = float(row[metadata_dict['indicator']['column']])

                data.append(dict(
                    date=date,
                    indicator=indicator
                ))

            indicators.append(
                dict(
                    id=folder,
                    domain=dict(
                        date=[min(data, key=_dt)['date'], max(data, key=_dt)['date']],
                        indicator=[min(data, key=_di)['indicator'], max(data, key=_di)['indicator']]
                    ),
                    data=data,
                )
            )
        except Exception as e:
            pass

    return indicators
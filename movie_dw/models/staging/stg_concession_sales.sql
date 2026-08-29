with source as (
    select * from {{ source('movie', 'concession_sales') }}
)

select
    *,
    current_localtimestamp() as ingestion_timestamp
from source
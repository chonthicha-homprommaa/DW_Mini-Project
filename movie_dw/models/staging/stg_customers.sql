with source as (
    select * from {{ source('movie', 'customers') }}
)

select
    *,
    current_localtimestamp() as ingestion_timestamp
from source
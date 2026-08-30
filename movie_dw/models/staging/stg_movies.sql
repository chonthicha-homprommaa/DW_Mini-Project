with source as (
    select * from {{ source('movie', 'movies') }}
)

select
    *,
    current_localtimestamp() as ingestion_timestamp
from source
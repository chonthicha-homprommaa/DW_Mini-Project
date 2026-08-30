with source as (
    select * from {{ source('movie', 'showtimes') }}
)

select
    *,
    current_localtimestamp() as ingestion_timestamp
from source
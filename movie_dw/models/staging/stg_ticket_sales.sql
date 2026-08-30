with source as (
    select * from {{ source('movie', 'ticket_sales_5000') }}
)

select
    *,
    current_localtimestamp() as ingestion_timestamp
from source
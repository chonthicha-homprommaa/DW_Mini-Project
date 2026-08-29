with source as (
    select
        showtime_id,
        movie_id,
        show_date,
        screen_number,
        ticket_price,
        ingestion_timestamp as insertion_timestamp
    from {{ ref('stg_showtimes') }}
),

unique_source as (
    select
        *,
        row_number() over(partition by showtime_id) as row_num
    from source
)

select *
exclude (row_num)
from unique_source
where row_num = 1
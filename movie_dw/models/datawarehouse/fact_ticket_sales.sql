{{ config(
    materialized = 'table',
    partition_by = 'show_date'
) }}

with source as (
    select
        t.ticket_id,
        t.showtime_id,
        t.customer_id,
        s.movie_id,
        t.seat_number,
        t.seat_type,
        t.final_price,
        cast(
            coalesce(
                try_strptime(s.show_date, '%m/%d/%Y %H:%M:%S'),
                try_strptime(s.show_date, '%Y-%m-%d'),
                try_strptime(s.show_date, '%m/%d/%Y')
            ) as date
        ) as show_date,
        current_localtimestamp() as insertion_timestamp
    from {{ ref('stg_ticket_sales') }} as t
    left join {{ ref('stg_showtimes') }} as s
        on t.showtime_id = s.showtime_id
    where t.ticket_id is not null
),

unique_source as (
    select
        *,
        row_number() over (
            partition by ticket_id
        ) as row_number
    from source
)

select
    ticket_id,
    showtime_id,
    customer_id,
    movie_id,
    seat_number,
    seat_type,
    final_price,
    show_date,
    insertion_timestamp
from unique_source
where row_number = 1
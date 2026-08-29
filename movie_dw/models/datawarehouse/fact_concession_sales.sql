{{ config(
    materialized = 'table'
) }}

with source as (
    select
        sale_id as concession_sale_id,
        customer_id,
        item_name,
        quantity,
        unit_price,
        total_price,
        cast(
            coalesce(
                try_strptime(sale_date, '%m/%d/%Y %H:%M:%S'),
                try_strptime(sale_date, '%Y-%m-%d %H:%M:%S'),
                try_strptime(sale_date, '%Y-%m-%d'),
                try_strptime(sale_date, '%m/%d/%Y')
            ) as date
        ) as sale_date,
        current_localtimestamp() as insertion_timestamp
    from {{ ref('stg_concession_sales') }}
    where sale_id is not null
),

unique_source as (
    select
        *,
        row_number() over (
            partition by concession_sale_id
        ) as row_number
    from source
)

select
    concession_sale_id,
    customer_id,
    item_name,
    quantity,
    unit_price,
    total_price,
    sale_date,
    insertion_timestamp
from unique_source
where row_number = 1
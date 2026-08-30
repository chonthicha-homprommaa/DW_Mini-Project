with source as (
    select
        movie_id,
        title,
        genre,
        duration_min,
        rating,
        ingestion_timestamp as insertion_timestamp
    from {{ ref('stg_movies') }}
),

unique_source as (
    select
        *,
        row_number() over(partition by movie_id) as row_num
    from source
)

select *
exclude (row_num)
from unique_source
where row_num = 1
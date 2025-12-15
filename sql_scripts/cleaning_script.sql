-- create_clean_table.sql
CREATE TABLE fact_publisher AS
SELECT
    TRIM(`Publisher name`) AS publisher,
    STR_TO_DATE(`Date`, '%d.%m.%Y') AS date,
    IFNULL(`Impressions`,0) AS impressions,
    IFNULL(`Pageviews`,0) AS pageviews,
    IFNULL(`Likes`,0) AS likes,
    IFNULL(`Followers`,0) AS followers,
    IFNULL(`Comments`,0) AS comments,
    IFNULL(`In app pageviews`,0) AS in_app_pageviews,
    IFNULL(`Shares`,0) AS shares,
    IFNULL(`Register followers`,0) AS register_followers
FROM data
WHERE
    impressions >= 0
    AND pageviews >= 0
    AND likes >= 0;

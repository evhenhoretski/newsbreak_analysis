-- publisher_kpis.sql
CREATE VIEW publisher_monthly_kpi AS
SELECT
    publisher,
    DATE_FORMAT(date, '%Y-%m') AS month,
    SUM(impressions) AS total_impressions,
    SUM(pageviews) AS total_pageviews,
    SUM(likes) AS total_likes,
    SUM(shares) AS total_shares,
    SUM(comments) AS total_comments,

    ROUND(SUM(likes + comments + shares) / NULLIF(SUM(impressions),0), 4) AS engagement_rate,
    ROUND(SUM(shares) / NULLIF(SUM(impressions),0), 4) AS share_rate,
    ROUND(SUM(pageviews) / NULLIF(SUM(impressions),0), 4) AS ctr
FROM fact_publisher
GROUP BY publisher, month;

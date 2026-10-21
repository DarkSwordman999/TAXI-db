-- ./help.sh top-tips — топ-10 водителей по чаевым
SELECT
    'Водитель №' || В.код AS водитель,
    COUNT(*) AS поездок,
    SUM(П.чаевые) AS чаевые
FROM ПОЕЗДКИ П
JOIN ВОДИТЕЛИ В ON П.водитель = В.код
GROUP BY В.код
ORDER BY чаевые DESC
LIMIT 10;

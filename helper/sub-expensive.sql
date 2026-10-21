-- ./help.sh sub-expensive — самые дорогие поездки
SELECT *
FROM v_rides_user
ORDER BY стоимость DESC
LIMIT 10;

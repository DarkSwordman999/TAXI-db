-- ./help.sh func-drivers-above [порог] — водители с выручкой выше порога (функция drivers_above_revenue)
-- параметры: :arg1 — порог в долларах, по умолчанию 10000
\if :{?arg1}
\else
    \set arg1 10000
\endif
SELECT *
FROM drivers_above_revenue(:arg1)
LIMIT 20;

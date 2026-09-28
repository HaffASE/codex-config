# backend-data-review

## Метод

Восстанови чтения/записи, уникальность, ownership и tenant scope. Проверь transaction atomicity, read-modify-write races, lost update, isolation assumptions и порядок commit/event publication. Для migrations оцени backwards compatibility, nullable/default/backfill, lock risk и expand/contract deployment. Проследи pagination ordering, filtering, soft-delete и relations. Для query-cost claims отделяй доказуемую cardinality/N+1 от недоказанного performance impact. Держи описание на уровне конкретного invariant и failure scenario.

## Проверки против ложноположительных выводов

Не запускай migrations и не подключайся к production. Наличие транзакции не доказывает нужную isolation. Отсутствие repository interface не finding. Не придумывай объём данных, plan cost или p95. Ссылка на ORM документацию должна соответствовать установленной версии.

Верни кандидаты, evidence и gaps по общему protocol.md. Не делегируй и не исправляй код.

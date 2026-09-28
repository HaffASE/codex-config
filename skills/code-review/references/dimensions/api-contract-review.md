# api-contract-review

## Метод

Сопоставь handler input, validation/transforms, service output, serializer, headers/cookies/statuses и опубликованную схему. Проверь optional vs nullable, absent vs empty, enum evolution, pagination, identifiers, dates/timezones и errors. Найди несовпадение declared DTO и runtime response, включая interceptors. Для auth сравни OpenAPI security scheme и реальный guard. Установи deployment/backwards-compatibility требования до обвинения breaking change. Укажи доступные consumers; при их отсутствии ограничь вывод producer-side.

## Проверки против ложноположительных выводов

TypeScript type не runtime validation. Swagger decorator не доказывает фактический payload. Нельзя подтвердить client compatibility, видя только server DTO. Не регенерируй клиент/схему без разрешения и не требуй versioning без потребителей/политики.

Верни кандидаты, evidence и gaps по общему protocol.md. Не делегируй и не исправляй код.

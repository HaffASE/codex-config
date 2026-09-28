# backend-reliability-review

## Метод

Построй последовательность side effects и точки отказа. Проверь bounded timeouts/retries, backoff, cancellation, idempotency ключи, повторную доставку и частичный успех. Найди race windows и опиши interleaving по шагам. Проверь cleanup ресурсов, graceful shutdown и recoverability. Для Redis token storage проверь atomic check/delete/rotate, TTL и область logout/invalidate с реальными семантиками команд. Разделяй ожидаемую деградацию и потерю данных/доступа. Оцени, можно ли обнаружить реальную неисправность безопасными логами/метриками.

## Проверки против ложноположительных выводов

Не требуй distributed transactions или очереди без сценария. Отсутствие retry не дефект, если retry опасен. Не выполняй fault injection без разрешения. Не считай один пользовательский Redis set ошибкой только из личных предпочтений: нужны требования к сессиям и TTL.

Верни кандидаты, evidence и gaps по общему protocol.md. Не делегируй и не исправляй код.

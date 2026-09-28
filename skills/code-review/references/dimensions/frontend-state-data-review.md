# frontend-state-data-review

## Метод

Проследи user action → local/form/URL/server state → request → cache → render. Проверь источник истины, derived state, effect dependencies и cleanup, optimistic update/rollback. Найди query-key collisions, tenant/user leakage, invalidation gaps и out-of-order responses. Для форм проверь async defaults/reset, validation transform, dirty state, submit duplication и отображение server errors. Сопоставь library versions и договорённости по React Query/RHF с кодом. Для каждого race покажи конкретный порядок событий и итоговое неверное состояние.

## Проверки против ложноположительных выводов

Не советуй useEffect для state, который вычисляется при render. Не требуй глобального store только потому, что state используется в двух компонентах. Оцени effect semantics установленного React; не приписывай development StrictMode дубли production без доказательств. Не называй cache bug обычный intentional stale-while-revalidate.

Верни кандидаты, evidence и gaps по общему protocol.md. Не делегируй и не исправляй код.

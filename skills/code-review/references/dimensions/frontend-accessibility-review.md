# frontend-accessibility-review

## Метод

Пройди пользовательский сценарий клавиатурой концептуально и, только при доступном разрешённом browser, фактически. Проверь accessible name, native semantics, label/error association, focus entry/return в modal/popover, focus traps, disabled/loading/error states и live announcements. Сверь UI-kit component implementation прежде чем обвинять wrapper в отсутствии semantics. Для контраста/zoom/target size используй реальный rendered evidence либо укажи необходимость проверки. Указывай конкретный элемент и потерянную возможность действия.

## Проверки против ложноположительных выводов

Не добавляй ARIA вместо работающего native control. Отсутствие aria-label не дефект, если имя задано text/label. Не считай чтение JSX screen-reader тестом. Без браузера явно укажи source-only coverage, не заявляй accessibility certification.

Верни кандидаты, evidence и gaps по общему protocol.md. Не делегируй и не исправляй код.

# behavior-test-review

## Метод

Составь короткую таблицу changed behavior → failure mode → existing test/assertion. Проверь, отражают ли mocks реальные boundaries и ловят ли assertions нужную регрессию. Для Vitest/RTL предпочитай пользовательское наблюдаемое поведение; для интеграции оцени wiring/providers/serialization. Для concurrency/errors предложи минимальный regression scenario словами. Установи существующий package manager и repository test scripts; выполняй только явно разрешённые команды и фиксируй фактический результат. Отделяй отсутствующее покрытие от подтверждённого runtime defect.

## Проверки против ложноположительных выводов

Ноль *.spec.ts в одном каталоге не означает, что тестов нет во всём проекте. Не требуй coverage percentage или тест на каждый private method. Не запускай npx/latest tool/install для проверки. Test gap обычно observation; P2 допустим, когда нарушено explicit обязательство либо gap скрывает доказанную регрессию, не только потенциальную.

Верни кандидаты, evidence и gaps по общему protocol.md. Не делегируй и не исправляй код.

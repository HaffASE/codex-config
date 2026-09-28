# frontend-architecture-review

## Метод

Установи действующие архитектурные правила и границы приложения, feature, UI kit, data adapters. Проверь владельца состояния, сценария формы и API mapping. Найди обход public API feature и связи, увеличивающие impact обычного изменения. Проверь coupling micro-frontend с host: routing, providers, UI kit версии и контракт mount/unmount. Укажи конкретного consumer для каждой утечки internal detail. Предлагай небольшую корректировку ownership; сохраняй полезные facade и co-location.

## Проверки против ложноположительных выводов

Не запрещай horizontal imports только из-за личного выбора FSD. Папка widgets/features не доказывает правило. Shared hook не обязан стать сервисом. Props drilling и colocated logic не дефект без реальной проблемы. Типовые архитектурные предпочтения — observation.

Верни кандидаты, evidence и gaps по общему protocol.md. Не делегируй и не исправляй код.

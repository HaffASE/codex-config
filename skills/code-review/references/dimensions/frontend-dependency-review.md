# frontend-dependency-review

## Метод

Проследи реальные imports с alias resolution, package exports, barrel side effects и type-only edges. Различай runtime cycles и harmless type graph. Проверь browser code на server-only modules/secrets, SSR-safe entrypoints и singleton/provider identity в host/MFE. Установи фактический bundler и правила resolution. Для duplicate React/context/library claims найди dependency resolution evidence, а не только две записи manifests. Проверь consumer visibility при перемещении API и совместимость public entrypoints.

## Проверки против ложноположительных выводов

Не обещай tree shaking, dead-code elimination или рост bundle без соответствующей config/build evidence. Не каждое barrel export — defect. Не приравнивай пакетный dependency cycle к runtime crash. Не запускай install/bundle generator для проверки без разрешения.

Верни кандидаты, evidence и gaps по общему protocol.md. Не делегируй и не исправляй код.

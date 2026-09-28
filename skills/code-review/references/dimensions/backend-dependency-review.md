# backend-dependency-review

## Метод

Построй конкретные рёбра consumer → token/provider/module. Различай TypeScript type-only import, runtime import, module dependency и DI-resolution cycle. Проверь public versus internal exports и использование implementation tokens чужими feature-сценариями. Для Nest найди действительные imports/exports/global flags, dynamic registration options и datasource name. Перед утверждением о duplicate services/connections проверь версию пакета и composition. Перед советом убрать export проверь всех реальных consumers. Проверь транзитивные зависимости, side effects и обратное направление core → feature в контексте правил проекта.

## Проверки против ложноположительных выводов

Два вызова forRoot/registerAsync сами по себе не доказывают два соединения. Перенос Redis в AppModule не гарантирует видимость во feature: может потребоваться инфраструктурный module import/export. Generic T стирается и не создаёт отдельный runtime token. Повторная repository registration может быть корректной; не называй её дублированием database state.

Верни кандидаты, evidence и gaps по общему protocol.md. Не делегируй и не исправляй код.

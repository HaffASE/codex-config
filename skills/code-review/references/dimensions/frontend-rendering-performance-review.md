# frontend-rendering-performance-review

## Метод

Найди user-visible hot path. Проверь key/identity correctness, unmount/reset, hydration mismatch и render-time side effects. Проследи, какие state changes действительно затрагивают subtree. Для дорогих вычислений установи рост input, частоту и доступные измерения. Различай re-render (нормален) и нарушенное поведение/измеримый bottleneck. Проверь lazy boundaries, data waterfalls и layout thrashing по реальному порядку операций. Указывай measurement needed, если impact не доказан.

## Проверки против ложноположительных выводов

Не ставь P2 за отсутствие React.memo/useMemo/useCallback. Не утверждай, что compiler/bundler оптимизирует код без конфигурации. Не выдумывай milliseconds/CLS/LCP. Статический бесконечный render loop можно подтвердить трассой; небольшую производительность — observation до profiling.

Верни кандидаты, evidence и gaps по общему protocol.md. Не делегируй и не исправляй код.

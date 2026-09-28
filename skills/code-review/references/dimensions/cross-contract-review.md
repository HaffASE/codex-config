# cross-contract-review

## Метод

Назови конкретный producer revision и consumer revision. Зафиксируй цепочку endpoint → serialized schema → generated types/client → mapping → UI/error handling. Сравни имена, nullability, enum unknown cases, dates, pagination и auth/cookie/credentials semantics. Проследи ошибки и refresh/logout с обеих сторон. Проверь совместимость развёртывания старого consumer с новым producer и наоборот, когда это часть требований. Найди доказуемый divergence и дай evidence на обе стороны.

## Проверки против ложноположительных выводов

Недоступен второй repo или revision — status=partial и точный пробел, не полное cross-review. Generated types могут быть устаревшими: provenance важен. Согласие типов не доказывает runtime serialization. В v0.1 helper проверяет paths одного Git root; multi-repo evidence проверяется вручную, не притворяйся что helper его валидировал.

Верни кандидаты, evidence и gaps по общему protocol.md. Не делегируй и не исправляй код.

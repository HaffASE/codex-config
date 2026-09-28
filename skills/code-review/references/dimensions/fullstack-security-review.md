# fullstack-security-review

## Метод

Построй trust boundaries и attacker-controlled inputs. Разделяй authentication и authorization, проверь ownership/tenant scopes на server. Для cookies/JWT проверь effective config: secure/httpOnly/sameSite, CSRF model, token audience/type/issuer/expiry/rotation/replay и logout semantics по требованиям. Для frontend проследи dangerous HTML/URLs, sanitization boundary и попадание secrets в bundle/logs. Для server проследи инъекции/SSRF/file paths в реальном reachable sink. Для каждого finding укажи preconditions, конкретный путь и impact без раскрытия секретов.

## Проверки против ложноположительных выводов

Не считай любой innerHTML уязвимостью: проверь источник и sanitizer. secure=false в локальном dev не равен production exploit; production config должна быть подтверждена. Не выполняй exploit, outbound request, fuzzing, audit/install command без разрешения. Пакетный CVE требует точной версии и первичного advisory; иначе отдельный вопрос, не уверенное утверждение.

Верни кандидаты, evidence и gaps по общему protocol.md. Не делегируй и не исправляй код.

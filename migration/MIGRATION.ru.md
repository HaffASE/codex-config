# OMX → native Codex: границы миграции

Это изменение архитектуры, не замена строки `omx` на `codex`.
Skills описывают процедуры; Codex исполняет tools и управляет дочерними потоками.
Оставшиеся Python helpers проверяют структуру/хэши артефактов и устанавливают файлы,
но не запускают модели, не возобновляют задачи и не координируют агентов.

## Соответствие workflows

| Прежняя потребность | Нативный путь | Что намеренно не переносится |
| --- | --- | --- |
| analyze / deepsearch | nc_scout → nc_explorer, при необходимости nc_docs | OMX routing/state tools |
| deep-interview / question CLI | `$deep-interview`, обычный диалог | Специальный question runtime |
| plan / ralplan | `$implementation-plan` или `$feature-discovery` | Скрытая вложенная consensus-петля |
| autopilot / execute | `$execute-plan` по текущему разрешению | Автоматическое расширение scope |
| ralph / ultragoal | Опциональный `/goal` + `$checkpoint` | OMX ledger/lifecycle, гарантия бесконечного продолжения |
| team / ultrawork | `$parallel-work`, native children, ownership | tmux panes, mailbox, Team CLI, автоматические worktrees |
| ultraqa | `$verify-work` с явным бюджетом исправлений | Persisted QA mode и бесконечный repair loop |
| tdd | `$testing-code-changes` и `$frontend-tests` | Обязательный тест на каждый метод/механическую правку |
| build-fix / debugger | `$debug-by-evidence`, разрешённая правка, `$verify-work` | Лишний режим при уже доказанной причине |
| code-review / multi-agent review-kit | `$code-review`, native lanes + 14 checklists | Внешний CLI model runner, отдельный ledger scheduler |
| security-review | `$security-review` / nc_security | Имитация проведённого pentest |
| visual verification | `$browser-debug`, фактически доступный браузер | Автоустановка browser/MCP, выдуманные screenshots |
| cancel | Нативные stop/interrupt и `/goal pause/clear` | Псевдоочистка несуществующего режима |
| hud / notifications / mission / wiki | Нативный интерфейс и явные подключённые tools | OMX UI/операционные сервисы; они не реализованы |
| doctor / setup | `doctor.py` и `install.py` | Удаление неизвестных настроек/credentials |

Соответствие означает покрытие цели, а не равенство состояния и operational semantics.
Native Goal не является взаимозаменяемой реализацией Ultragoal ledger.
Native subagents не дают Team mailbox/tmux и сами по себе не изолируют файловую систему.
Отдельные native instances не заменяют явно обязательное ревью другой моделью/провайдером.

## Сохраняемое содержимое

Из feature-discovery сохранены frozen packets, SHA-bound и per-file review,
traceability, prerequisite ownership, delta-review с полным findings ledger,
source/runtime различие, ограничение review rounds и отдельно scoped handoff.
Результат READY не даёт разрешения на implementation, commit, merge или release.

Пять evidence-skills адаптированы без потери их инженерных границ. Из review-kit
перенесены 14 тематических методов/false-positive checklists, а не старый runner.
Code-review сохраняет distinction между verdict, completeness и actual coverage.
Снято требование, что состоянием и orchestration обязан владеть OMX.

## Порядок перехода на машине

Сначала прочитайте текущие user/project/override instructions и список реально
активных skills, agents, hooks, MCP и shell aliases. Учитывайте CODEX_HOME и выбранный
проект. `doctor.py` помогает, но не сканирует все вложенные инструкции/marketplaces.
Не выводите auth.json, токены, cookie и секретные значения конфигов в отчёт.

Завершите или остановите относящийся к миграции активный workflow его штатными
средствами. Не завершайте все процессы Codex/tmux пользователя. Сделайте внешнюю
резервную копию каждого файла, который предстоит изменить. Не используйте для неё
каталог, который затем собираетесь удалять.

Адресно отключите подтверждённые OMX-owned runtime hooks, config/MCP entries,
конкурирующий orchestration block и legacy role/skill registrations. Смешанный
AGENTS.md не удаляйте: сохраняйте пользовательские/командные договорённости.
Не используйте удаление строки по совпадению `omx` как доказательство владения.

Установите пакет сначала в preview. Разрешите коллизии имён до `--replace`.
При необходимости подключите AGENTS.native.md как общий блок. Не переносите весь
global contract в каждый repository. Локальный AGENTS.md должен содержать именно
местные stack/commands/boundaries, а не копию всех skills.

Откройте новую нативную сессию командой `codex`, не прежним OMX wrapper.
Проверьте реальные native agents и manual skills. При отсутствии capability не
называйте текстовую симуляцию полноценной заменой. Не обновляйте клиента, модели,
permissions или зависимости без соответствующего разрешения.

Пакет OMX можно оставить установленным, но неактивным на переходный период.
Его удаление package manager'ом — отдельное действие, которое нужно обосновать
способом первоначальной установки. Не запускайте угадываемый `uninstall --purge`.

## Старые артефакты и контракты

Ссылки `.omx/...` в существующих документах могут оставаться историей.
Переезд не должен менять bytes/hash уже рецензированного packet. В новом run
создайте provenance-map с original path, captured path, SHA и текущей ролью документа.
Snapshot, index summary и поздний scoped handoff — разные сущности.

В native feature-discovery изменены capability IDs preflight:

```text
analyze         → native-analysis
deep-interview  → user-interaction
ralplan         → native-planning
ask-advisor     → native-council
independent-review — сохранён
```

Новая версия сохраняет schema_version=1 структуры документов, но старые capabilities
не являются валидным свежим native preflight. Старый packet импортируется как history;
новый native draft проверяется и рецензируется заново. Не редактируйте исторический
packet для прохождения нового валидатора и не заменяйте прежние verdicts новыми именами.

Explicit constraints типа «ровно Fable и Opus, без fallback» не считаются выполненными
двумя native Codex agents. Они остаются unmet до явного изменения требования или
фактического предоставления нужного reviewer. Глобального требования внешних моделей
в новом пакете нет.

## Почему остались scripts

freeze_plan.py и validate_plan.py нужны для детерминированной проверки артефактов.
Они не аутентифицируют reviewer/model, не знают фактического sandbox и не проверяют
production runtime. Валидный JSON с именем модели не доказывает вызов этой модели.
Authority также не выводится из подписи/названия handoff: нужен текущий контекст задачи.

## Критерий завершения миграции

Проверены active instruction chain, нужные manual skills и реальный native spawn.
Нет активных OMX lifecycle/tool dependencies в выбранном профиле/проекте.
Сохранены прежние пользовательские правила, credentials и непричастные интеграции.
Есть diff/backup каждого изменения и честный список непроверенных capabilities.
До этого момента комплект установлен, но миграция машины не объявляется завершённой.

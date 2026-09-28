# Обновление из отдельного каталога

Skills установлены как ссылки на исходный каталог комплекта. Изменение файлов в
этом каталоге становится видно сразу, до `install.py --update`. Для обновления
подготовьте новую версию в другом постоянном каталоге и сохраните старый каталог
до завершения проверки. Не используйте временную распаковку, которую удалите после
обновления.

Ниже `OLD` — текущий исходный каталог, `NEXT` — новая версия. Подставьте реальные
абсолютные пути. Команды не меняют пользовательскую конфигурацию до `--apply`.

```bash
OLD=/absolute/path/to/current-kit
NEXT=/absolute/path/to/next-kit
cd "$NEXT"
python3 check.py
python3 release.py
```

`release.py` сравнивает пакет с его `SHA256SUMS`. Для собственного изменённого
исходника сначала завершите проверку и ревью, затем создайте новый manifest через
`python3 release.py --write` и повторите `python3 release.py`. Не обновляйте
контрольные суммы только ради обхода ошибки сверки.

## Пробное обновление в отдельном home

Испытайте именно переход со старой версии на новую, не затрагивая рабочий home:

```bash
TEST_HOME="$(mktemp -d)"
python3 "$OLD/install.py" --home "$TEST_HOME" --apply
python3 "$NEXT/install.py" --home "$TEST_HOME" --update
python3 "$NEXT/install.py" --home "$TEST_HOME" --update --apply
python3 "$NEXT/doctor.py" --home "$TEST_HOME" --skill checkpoint
```

Просмотрите план перед `--apply`. Для `checkpoint` ожидаются
`ownership: recorded` и `state: link_current`; это проверка пути ссылки, а не
содержимого skill или его загрузки в Codex. Если исходная установка имела
специальный режим (`--agents-only` либо `--with-guidance`), сохранённый inventory
определяет тот же режим при обновлении.

## Рабочее переключение

Когда пробное обновление и план выглядят правильно:

```bash
python3 "$NEXT/install.py" --update
python3 "$NEXT/install.py" --update --apply
python3 "$NEXT/doctor.py" --skill checkpoint
python3 "$NEXT/doctor.py"
```

Сохраните выведенный путь к backup manifest и старый каталог. Затем откройте новую
сессию Codex и выполните [smoke-проверки](SMOKE-TESTS.ru.md) для фактического
обнаружения skills и запуска ролей. Файловый отчёт этого не подтверждает.

Если новая версия не подходит, а управляемые файлы не были изменены вручную,
сначала просмотрите обратный план и переключитесь со старого каталога:

```bash
python3 "$OLD/install.py" --update
python3 "$OLD/install.py" --update --apply
python3 "$OLD/doctor.py"
```

При `installation_drift` или конфликте не применяйте замену вслепую: сверяйте
`$CODEX_HOME/backups/native-codex-kit/active.json`, указанный backup manifest и
фактические пути. Установщик отказывается перезаписывать пользовательские правки
управляемых файлов; резервная копия не равна автоматическому восстановлению после
прерывания процесса или ошибки файловой системы.

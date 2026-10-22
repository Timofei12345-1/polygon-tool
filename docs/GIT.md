# Работа с Git и GitHub

## 1. Первичная настройка

```bash
git config --global user.name  "Ваше Имя"
git config --global user.email "you@example.com"

cd polygon-tool
git init -b main
git add .
git commit -m "chore: initial project structure"
```

Создайте на GitHub пустой репозиторий `polygon-tool` (без README и .gitignore), затем:

```bash
git remote add origin https://github.com/Timofei12345-1/polygon-tool.git
git push -u origin main
git switch -c develop
git push -u origin develop
```

## 2. Ветки

| Ветка | Назначение |
|---|---|
| `main` | Стабильная версия, каждый релиз помечается тегом |
| `develop` | Интеграция готовых функций |
| `feature/<имя>` | Новая функция (`feature/geometry`, `feature/io`, `feature/backup`) |
| `docs/<имя>` | Документация |
| `test/<имя>` | Тесты и тест-кейсы |
| `fix/<имя>` | Исправление ошибок |

Слияние — через Pull Request в `develop`, затем `develop` → `main`. В настройках GitHub
(Settings → Branches) включите защиту `main`: обязательный Pull Request и успешный CI (`.github/workflows/tests.yml`).

## 3. Сообщения коммитов (Conventional Commits)

```
feat(geometry): add shoelace area calculation
feat(backup): add SHA-256 integrity check
fix(geometry): detect self-intersection with zero signed area
docs: add Russian and English README
test: add test cases for degenerate polygons
chore: add .gitignore
```

Типы: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`. Один коммит — одно логическое изменение.

## 4. Рекомендуемый порядок коммитов

Если делаете историю заново, по пунктам задания:

```bash
git switch -c docs/tz develop
git add docs/TZ.md
git commit -m "docs: add technical specification"

git switch -c feature/geometry develop
git add src/polygon_tool/geometry.py tests/test_geometry.py
git commit -m "feat(geometry): add perimeter, area and polygon validation"

git switch -c feature/io develop
git add src/polygon_tool/io_handlers.py tests/test_io.py examples
git commit -m "feat(io): add console and TXT/CSV/JSON input, result output"

git switch -c feature/backup develop
git add src/polygon_tool/backup.py tests/test_backup.py
git commit -m "feat(backup): add backup, verification, rotation and restore"

git switch -c feature/cli develop
git add src/polygon_tool/cli.py src/polygon_tool/__main__.py src/polygon_tool/__init__.py tests/test_cli.py pyproject.toml
git commit -m "feat(cli): add calc, backup, restore, list-backups, verify commands"

git switch -c docs/user-docs develop
git add README.md README.en.md docs/maintenance.md docs/test-cases.md docs/GIT.md
git commit -m "docs: add READMEs (ru/en), maintenance regulations, test cases"
```

После каждой ветки: `git push -u origin <ветка>` → Pull Request на GitHub → Merge.

## 5. Задачи (Issues)

Создайте по одному Issue на пункт задания и закрывайте их из коммитов/PR (`closes #1`):

1. Консольная программа расчёта периметра и площади
2. Алгоритм резервного копирования и восстановления точек
3. Пользовательская документация (ТЗ, README ru/en, регламент ТО)
4. Тест-кейсы и проверка соответствия ТЗ

## 6. Релиз

```bash
git switch main
git merge --no-ff develop
git tag -a v1.0.0 -m "First release"
git push origin main --tags
```

На GitHub: Releases → Draft a new release → выбрать тег `v1.0.0` → описать изменения.

## 7. Что не коммитить

Рабочие данные (`data/*.json`), резервные копии (`backups/*`), виртуальное окружение, `__pycache__` — всё это уже в `.gitignore`.

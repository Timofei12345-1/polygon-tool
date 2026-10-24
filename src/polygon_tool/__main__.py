import sys

if len(sys.argv) == 1:      # без аргументов — графический интерфейс
    from .gui import main
else:                       # с аргументами — консольная версия
    from .cli import main

raise SystemExit(main())

"""Графический интерфейс (tkinter) для polygon-tool.

Запуск:  python -m polygon_tool        (без аргументов — откроется окно)
         python -m polygon_tool.gui
Использует только стандартную библиотеку и те же модули, что и консольная версия.
"""

from __future__ import annotations

import math
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from . import __version__
from .backup import BackupError, BackupManager
from .geometry import Point, PolygonError, analyze
from .io_handlers import (
    DataError,
    format_number,
    parse_points_text,
    read_points_file,
    write_result_file,
)

PAD = 40
COLOR_OK = "#1f6feb"
COLOR_FILL = "#dbeafe"
COLOR_BAD = "#d1242f"
COLOR_GRID = "#e5e7eb"
COLOR_AXIS = "#9ca3af"


def _parse_number(text: str, name: str) -> float:
    try:
        value = float(text.strip().replace(",", "."))
    except ValueError:
        raise DataError(f"{name}: «{text}» не является числом.") from None
    if not math.isfinite(value):
        raise DataError(f"{name}: значение должно быть конечным числом.")
    return value


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"Polygon Tool {__version__} — периметр и площадь многоугольника")
        self.geometry("1100x680")
        self.minsize(900, 560)

        self.points: list[Point] = []
        self.result: dict | None = None
        self.error: str = ""
        self.manager = BackupManager("data/points.json", "backups", 10)
        self._tf = (0.0, 0.0, 1.0, 0.0, 0.0, 1)  # minx, miny, scale, ox, oy, height

        self.var_x = tk.StringVar()
        self.var_y = tk.StringVar()
        self.var_click = tk.BooleanVar(value=False)
        self.var_vertices = tk.StringVar(value="—")
        self.var_perimeter = tk.StringVar(value="—")
        self.var_area = tk.StringVar(value="—")
        self.var_status = tk.StringVar()
        self.var_cursor = tk.StringVar()

        self._build_menu()
        self._build_ui()
        self._update_all()

    # ------------------------------------------------------------------ UI

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)

        m_file = tk.Menu(menubar, tearoff=False)
        m_file.add_command(label="Открыть точки из файла…", accelerator="Ctrl+O", command=self.open_file)
        m_file.add_command(label="Вставить точки из буфера обмена", accelerator="Ctrl+V", command=self.paste_points)
        m_file.add_separator()
        m_file.add_command(label="Сохранить результат…", accelerator="Ctrl+S", command=self.save_result)
        m_file.add_separator()
        m_file.add_command(label="Загрузить точки из хранилища", command=self.load_storage)
        m_file.add_command(label="Сохранить точки в хранилище", command=self.save_storage)
        m_file.add_separator()
        m_file.add_command(label="Выход", command=self.destroy)
        menubar.add_cascade(label="Файл", menu=m_file)

        m_backup = tk.Menu(menubar, tearoff=False)
        m_backup.add_command(label="Резервные копии…", command=self.open_backups)
        m_backup.add_command(label="Создать копию сейчас", command=self.create_backup)
        m_backup.add_separator()
        m_backup.add_command(label="Файл хранилища…", command=self.choose_data_file)
        m_backup.add_command(label="Каталог копий…", command=self.choose_backup_dir)
        m_backup.add_command(label="Сколько копий хранить…", command=self.choose_keep)
        menubar.add_cascade(label="Копирование", menu=m_backup)

        m_help = tk.Menu(menubar, tearoff=False)
        m_help.add_command(label="О программе", command=self.about)
        menubar.add_cascade(label="Справка", menu=m_help)

        self.config(menu=menubar)
        self.bind("<Control-o>", lambda e: self.open_file())
        self.bind("<Control-s>", lambda e: self.save_result())

    def _build_ui(self) -> None:
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        left = ttk.Frame(paned, padding=4)
        right = ttk.Frame(paned, padding=4)
        paned.add(left, weight=0)
        paned.add(right, weight=1)

        # --- таблица вершин
        ttk.Label(left, text="Вершины (по порядку обхода)", font=("", 10, "bold")).pack(anchor="w")
        table_frame = ttk.Frame(left)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 6))
        self.tree = ttk.Treeview(table_frame, columns=("n", "x", "y"), show="headings", height=12, selectmode="browse")
        for col, title, width in (("n", "№", 40), ("x", "X", 110), ("y", "Y", 110)):
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor="e" if col != "n" else "center")
        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Delete>", lambda e: self.delete_selected())

        # --- ввод точки
        entry_row = ttk.Frame(left)
        entry_row.pack(fill=tk.X)
        ttk.Label(entry_row, text="X").pack(side=tk.LEFT)
        ex = ttk.Entry(entry_row, textvariable=self.var_x, width=10)
        ex.pack(side=tk.LEFT, padx=(2, 8))
        ttk.Label(entry_row, text="Y").pack(side=tk.LEFT)
        ey = ttk.Entry(entry_row, textvariable=self.var_y, width=10)
        ey.pack(side=tk.LEFT, padx=2)
        ex.bind("<Return>", lambda e: ey.focus_set())
        ey.bind("<Return>", lambda e: (self.add_point(), ex.focus_set()))
        self.entry_x = ex

        btn_row = ttk.Frame(left)
        btn_row.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(btn_row, text="Добавить", command=self.add_point).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(btn_row, text="Заменить", command=self.replace_selected).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)
        ttk.Button(btn_row, text="Удалить", command=self.delete_selected).pack(side=tk.LEFT, expand=True, fill=tk.X)

        btn_row2 = ttk.Frame(left)
        btn_row2.pack(fill=tk.X, pady=(4, 0))
        ttk.Button(btn_row2, text="▲", width=3, command=lambda: self.move_selected(-1)).pack(side=tk.LEFT)
        ttk.Button(btn_row2, text="▼", width=3, command=lambda: self.move_selected(1)).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row2, text="Очистить всё", command=self.clear_points).pack(side=tk.LEFT, expand=True, fill=tk.X)

        ttk.Separator(left).pack(fill=tk.X, pady=10)

        # --- результаты
        res = ttk.LabelFrame(left, text="Результат", padding=8)
        res.pack(fill=tk.X)
        for row, (label, var) in enumerate(
            (("Вершин:", self.var_vertices), ("Периметр:", self.var_perimeter), ("Площадь:", self.var_area))
        ):
            ttk.Label(res, text=label).grid(row=row, column=0, sticky="w", pady=1)
            ttk.Label(res, textvariable=var, font=("", 11, "bold")).grid(row=row, column=1, sticky="e", padx=(16, 0))
        res.columnconfigure(1, weight=1)

        self.lbl_status = ttk.Label(left, textvariable=self.var_status, wraplength=300, justify="left")
        self.lbl_status.pack(fill=tk.X, pady=(8, 0))

        ttk.Button(left, text="Сохранить результат…", command=self.save_result).pack(fill=tk.X, pady=(10, 0))

        # --- холст
        top = ttk.Frame(right)
        top.pack(fill=tk.X)
        ttk.Checkbutton(top, text="Добавлять вершины кликом по полотну", variable=self.var_click).pack(side=tk.LEFT)
        ttk.Label(top, textvariable=self.var_cursor, foreground="#6b7280").pack(side=tk.RIGHT)

        self.canvas = tk.Canvas(right, background="white", highlightthickness=1, highlightbackground="#d1d5db")
        self.canvas.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        self.canvas.bind("<Configure>", lambda e: self.redraw())
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Motion>", self._on_canvas_motion)

    # -------------------------------------------------------------- состояние

    def _update_all(self) -> None:
        self._refresh_table()
        self._recalc()
        self.redraw()

    def _refresh_table(self, select: int | None = None) -> None:
        self.tree.delete(*self.tree.get_children())
        for i, (x, y) in enumerate(self.points):
            self.tree.insert("", tk.END, iid=str(i), values=(i + 1, format_number(x, 10), format_number(y, 10)))
        if select is not None and 0 <= select < len(self.points):
            self.tree.selection_set(str(select))
            self.tree.see(str(select))

    def _recalc(self) -> None:
        self.result = None
        self.error = ""
        if len(self.points) < 3:
            self.var_status.set(f"Добавьте не менее 3 вершин (сейчас: {len(self.points)}).")
            self.lbl_status.configure(foreground="#6b7280")
        else:
            try:
                self.result = analyze(self.points)
            except PolygonError as exc:
                self.error = str(exc)
        if self.result:
            self.var_vertices.set(str(self.result["vertices"]))
            self.var_perimeter.set(format_number(self.result["perimeter"]))
            self.var_area.set(format_number(self.result["area"]))
            self.var_status.set("Многоугольник корректен.")
            self.lbl_status.configure(foreground="#1a7f37")
        else:
            self.var_vertices.set(str(len(self.points)) if self.points else "—")
            self.var_perimeter.set("—")
            self.var_area.set("—")
            if self.error:
                self.var_status.set(self.error)
                self.lbl_status.configure(foreground=COLOR_BAD)

    def _selected_index(self) -> int | None:
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def _guard(self, func):
        """Выполняет func, показывая ошибки пользователю окном."""
        try:
            return func()
        except (DataError, PolygonError, BackupError) as exc:
            messagebox.showerror("Ошибка", str(exc), parent=self)
        except OSError as exc:
            messagebox.showerror("Ошибка", exc.strerror or str(exc), parent=self)
        return None

    # --------------------------------------------------------- редактирование

    def _read_entry(self) -> Point:
        return _parse_number(self.var_x.get(), "X"), _parse_number(self.var_y.get(), "Y")

    def add_point(self) -> None:
        def go():
            self.points.append(self._read_entry())
            self.var_x.set("")
            self.var_y.set("")
            self._update_all()
            self._refresh_table(select=len(self.points) - 1)
            self.tree.selection_remove(self.tree.selection())

        self._guard(go)

    def replace_selected(self) -> None:
        idx = self._selected_index()
        if idx is None:
            messagebox.showinfo("Заменить", "Выберите вершину в таблице.", parent=self)
            return

        def go():
            self.points[idx] = self._read_entry()
            self._update_all()
            self._refresh_table(select=idx)

        self._guard(go)

    def delete_selected(self) -> None:
        idx = self._selected_index()
        if idx is None:
            return
        del self.points[idx]
        self._update_all()
        self._refresh_table(select=min(idx, len(self.points) - 1))

    def move_selected(self, delta: int) -> None:
        idx = self._selected_index()
        if idx is None:
            return
        new = idx + delta
        if not 0 <= new < len(self.points):
            return
        self.points[idx], self.points[new] = self.points[new], self.points[idx]
        self._update_all()
        self._refresh_table(select=new)

    def clear_points(self) -> None:
        if self.points and not messagebox.askyesno("Очистить", "Удалить все вершины?", parent=self):
            return
        self.points = []
        self._update_all()

    def _on_select(self, _event=None) -> None:
        idx = self._selected_index()
        if idx is not None and idx < len(self.points):
            x, y = self.points[idx]
            self.var_x.set(format_number(x, 10))
            self.var_y.set(format_number(y, 10))
        self.redraw()

    def _set_points(self, points: list[Point]) -> None:
        self.points = list(points)
        self._update_all()

    # ------------------------------------------------------------------ файлы

    def open_file(self) -> None:
        path = filedialog.askopenfilename(
            parent=self,
            title="Открыть точки",
            filetypes=[("Файлы точек", "*.txt *.csv *.json"), ("Все файлы", "*.*")],
        )
        if path:
            self._guard(lambda: self._set_points(read_points_file(path)))

    def paste_points(self) -> None:
        def go():
            try:
                text = self.clipboard_get()
            except tk.TclError:
                raise DataError("Буфер обмена пуст.") from None
            self._set_points(parse_points_text(text, source="буфер обмена"))

        self._guard(go)

    def save_result(self) -> None:
        if not self.result:
            messagebox.showwarning("Сохранить результат", self.error or "Нет корректного результата для сохранения.", parent=self)
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Сохранить результат",
            defaultextension=".txt",
            filetypes=[("Текст", "*.txt"), ("JSON", "*.json")],
        )
        if path:
            self._guard(lambda: (write_result_file(path, self.result), messagebox.showinfo("Готово", f"Результат записан:\n{path}", parent=self)))

    # ---------------------------------------------------- хранилище и копии

    def load_storage(self) -> None:
        self._guard(lambda: self._set_points(self.manager.load_points()))

    def save_storage(self) -> None:
        def go():
            if not self.points:
                raise DataError("Нет точек для сохранения.")
            self.manager.save_points(self.points)
            messagebox.showinfo("Готово", f"Точки сохранены:\n{self.manager.data_file}", parent=self)

        self._guard(go)

    def create_backup(self) -> None:
        def go():
            if not self.manager.data_file.exists() and self.points:
                if messagebox.askyesno("Копия", "Хранилище пусто. Сохранить текущие точки в хранилище и сделать копию?", parent=self):
                    self.manager.save_points(self.points)
            path = self.manager.create_backup()
            messagebox.showinfo("Готово", f"Копия создана:\n{path}", parent=self)

        self._guard(go)

    def _rebuild_manager(self, data_file=None, backup_dir=None, keep=None) -> None:
        self.manager = BackupManager(
            data_file or self.manager.data_file,
            backup_dir or self.manager.backup_dir,
            keep if keep is not None else self.manager.keep,
        )

    def choose_data_file(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Файл хранилища точек",
            initialfile=self.manager.data_file.name,
            initialdir=str(self.manager.data_file.parent),
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            confirmoverwrite=False,
        )
        if path:
            self._rebuild_manager(data_file=path)

    def choose_backup_dir(self) -> None:
        path = filedialog.askdirectory(parent=self, title="Каталог резервных копий", mustexist=False)
        if path:
            self._rebuild_manager(backup_dir=path)

    def choose_keep(self) -> None:
        n = simpledialog.askinteger(
            "Ротация", "Сколько копий хранить?", parent=self, initialvalue=self.manager.keep, minvalue=1, maxvalue=1000
        )
        if n:
            self._rebuild_manager(keep=n)

    def open_backups(self) -> None:
        BackupWindow(self)

    def about(self) -> None:
        messagebox.showinfo(
            "О программе",
            f"Polygon Tool {__version__}\n\nПериметр и площадь многоугольника по координатам вершин,\n"
            "резервное копирование точек.\n\n"
            f"Хранилище: {self.manager.data_file}\nКопии: {self.manager.backup_dir} (хранить {self.manager.keep})",
            parent=self,
        )

    # --------------------------------------------------------------- рисование

    def _compute_transform(self) -> None:
        w = max(self.canvas.winfo_width(), 50)
        h = max(self.canvas.winfo_height(), 50)
        if self.points:
            xs = [p[0] for p in self.points]
            ys = [p[1] for p in self.points]
            minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
        else:
            minx, maxx, miny, maxy = 0.0, 10.0, 0.0, 10.0
        spanx, spany = maxx - minx, maxy - miny
        avail_w, avail_h = max(w - 2 * PAD, 10), max(h - 2 * PAD, 10)
        candidates = []
        if spanx > 0:
            candidates.append(avail_w / spanx)
        if spany > 0:
            candidates.append(avail_h / spany)
        scale = min(candidates) if candidates else min(avail_w, avail_h) / 10
        ox = PAD + (avail_w - spanx * scale) / 2
        oy = PAD + (avail_h - spany * scale) / 2
        self._tf = (minx, miny, scale, ox, oy, h)

    def _to_canvas(self, p: Point) -> tuple[float, float]:
        minx, miny, s, ox, oy, h = self._tf
        return ox + (p[0] - minx) * s, h - (oy + (p[1] - miny) * s)

    def _to_world(self, cx: float, cy: float) -> Point:
        minx, miny, s, ox, oy, h = self._tf
        return (cx - ox) / s + minx, (h - cy - oy) / s + miny

    @staticmethod
    def _nice_step(target: float) -> float:
        if target <= 0 or not math.isfinite(target):
            return 1.0
        p = 10 ** math.floor(math.log10(target))
        for m in (1, 2, 5, 10):
            if m * p >= target:
                return m * p
        return 10 * p

    def redraw(self) -> None:
        c = self.canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 60 or h < 60:
            return
        self._compute_transform()
        scale = self._tf[2]

        # сетка
        step = self._nice_step(70 / scale)
        x0, y_top = self._to_world(0, 0)
        x1, y_bottom = self._to_world(w, h)
        k = math.ceil(x0 / step)
        while k * step <= x1:
            v = k * step
            cx, _ = self._to_canvas((v, 0))
            c.create_line(cx, 0, cx, h, fill=COLOR_AXIS if k == 0 else COLOR_GRID)
            c.create_text(cx + 2, h - 2, text=format_number(v, 8), anchor="sw", fill="#6b7280", font=("", 8))
            k += 1
        k = math.ceil(y_bottom / step)
        while k * step <= y_top:
            v = k * step
            _, cy = self._to_canvas((0, v))
            c.create_line(0, cy, w, cy, fill=COLOR_AXIS if k == 0 else COLOR_GRID)
            c.create_text(2, cy - 2, text=format_number(v, 8), anchor="sw", fill="#6b7280", font=("", 8))
            k += 1

        if not self.points:
            c.create_text(w / 2, h / 2, text="Добавьте вершины в таблице слева\nили включите добавление кликом", fill="#9ca3af", justify="center", font=("", 12))
            return

        coords = [self._to_canvas(p) for p in self.points]
        color = COLOR_OK if self.result else COLOR_BAD
        if len(coords) >= 3:
            flat = [v for xy in coords for v in xy]
            c.create_polygon(*flat, outline=color, fill=COLOR_FILL if self.result else "", width=2)
        elif len(coords) == 2:
            c.create_line(*coords[0], *coords[1], fill=color, width=2)

        selected = self._selected_index()
        for i, (cx, cy) in enumerate(coords):
            r = 6 if i == selected else 4
            c.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#f59e0b" if i == selected else color, outline="white")
            c.create_text(cx + 8, cy - 8, text=str(i + 1), anchor="sw", font=("", 9, "bold"), fill="#111827")

    def _on_canvas_motion(self, event) -> None:
        x, y = self._to_world(event.x, event.y)
        self.var_cursor.set(f"x = {format_number(x, 4)}   y = {format_number(y, 4)}")

    def _on_canvas_click(self, event) -> None:
        if not self.var_click.get():
            return
        x, y = self._to_world(event.x, event.y)
        step = self._nice_step(70 / self._tf[2])
        digits = max(0, 1 - math.floor(math.log10(step)))
        self.points.append((round(x, digits), round(y, digits)))
        self._update_all()
        self._refresh_table(select=len(self.points) - 1)


class BackupWindow(tk.Toplevel):
    """Окно списка резервных копий: проверка, создание, восстановление."""

    def __init__(self, app: App) -> None:
        super().__init__(app)
        self.app = app
        self.title("Резервные копии")
        self.geometry("760x380")
        self.transient(app)

        self.tree = ttk.Treeview(self, columns=("name", "count", "created", "state"), show="headings", selectmode="browse")
        for col, title, width in (("name", "Файл", 250), ("count", "Точек", 60), ("created", "Создана", 190), ("state", "Состояние", 200)):
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor="w")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 4))

        bar = ttk.Frame(self)
        bar.pack(fill=tk.X, padx=8, pady=8)
        ttk.Button(bar, text="Создать копию", command=self.create).pack(side=tk.LEFT)
        ttk.Button(bar, text="Обновить / проверить", command=self.refresh).pack(side=tk.LEFT, padx=6)
        ttk.Button(bar, text="Восстановить выбранную", command=self.restore).pack(side=tk.LEFT)
        ttk.Button(bar, text="Восстановить из файла…", command=self.restore_file).pack(side=tk.LEFT, padx=6)
        ttk.Button(bar, text="Закрыть", command=self.destroy).pack(side=tk.RIGHT)
        self.refresh()

    def refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())
        mgr = self.app.manager
        for path in reversed(mgr.list_backups()):
            try:
                info = mgr.verify_backup(path)
                row = (path.name, info["points_count"], info["created"], "OK")
            except BackupError as exc:
                row = (path.name, "—", "—", f"ПОВРЕЖДЕНА: {exc}")
            self.tree.insert("", tk.END, iid=str(path), values=row)

    def create(self) -> None:
        self.app.create_backup()
        self.refresh()

    def _restore(self, backup) -> None:
        if not messagebox.askyesno(
            "Восстановление",
            "Текущее хранилище будет заменено выбранной копией\n(перед этим будет создана копия текущих данных). Продолжить?",
            parent=self,
        ):
            return

        def go():
            path = self.app.manager.restore(backup)
            self.app._set_points(self.app.manager.load_points())
            messagebox.showinfo("Готово", f"Данные восстановлены из {path.name} и загружены в таблицу.", parent=self)

        self.app._guard(go)
        self.refresh()

    def restore(self) -> None:
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Восстановление", "Выберите копию в списке.", parent=self)
            return
        self._restore(sel[0])

    def restore_file(self) -> None:
        path = filedialog.askopenfilename(
            parent=self, title="Выберите копию", initialdir=str(self.app.manager.backup_dir), filetypes=[("Копии", "points_*.json"), ("JSON", "*.json")]
        )
        if path:
            self._restore(path)


def main() -> int:
    App().mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

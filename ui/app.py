import json
import sys
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from tkinter import messagebox, simpledialog
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from learning.active_recall import generate_quiz
from learning.review import recomendar_revisao
from llm_client import send_message
from main import _decide_tool, TOOL_FUNCTIONS, log_tool_call
from rag.chunker import chunk_documents
from rag.embedder import generate_embeddings, save_index
from rag.loader import load_documents
from tools import rag as rag_module
from planning.study_plan import gerar_prioridades_do_dia
from tools.agenda import consultar_agenda
from tools.rag import buscar_material_rag
from tools.tarefas import adicionar_tarefa, listar_tarefas


class JarvisApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("JARVIS - Assistente Academico")
        self.geometry("960x640")
        self.configure(bg="#0f172a")

        self._init_styles()

        self.history: List[Dict[str, Any]] = []

        self._build_layout()

    def _init_styles(self) -> None:
        self.font_title = ("Segoe UI", 16, "bold")
        self.font_body = ("Segoe UI", 11)
        self.font_small = ("Segoe UI", 10)

        self.color_bg = "#0f172a"
        self.color_panel = "#111827"
        self.color_card = "#0b1220"
        self.color_text = "#e2e8f0"
        self.color_muted = "#94a3b8"
        self.color_accent = "#38bdf8"
        self.color_success = "#22c55e"
        self.color_error = "#7f1d1d"

    def _build_layout(self) -> None:
        header = tk.Frame(self, bg=self.color_bg)
        header.pack(fill="x", padx=16, pady=(16, 8))
        tk.Label(
            header,
            text="JARVIS",
            fg=self.color_text,
            bg=self.color_bg,
            font=self.font_title,
        ).pack(side="left")
        tk.Label(
            header,
            text="Assistente Academico",
            fg=self.color_muted,
            bg=self.color_bg,
            font=self.font_small,
        ).pack(side="left", padx=8)

        body = tk.Frame(self, bg=self.color_bg)
        body.pack(fill="both", expand=True, padx=16, pady=8)

        sidebar = tk.Frame(body, bg=self.color_panel, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        main = tk.Frame(body, bg=self.color_bg)
        main.pack(side="left", fill="both", expand=True, padx=(16, 0))

        tk.Label(
            sidebar,
            text="Acoes rapidas",
            fg=self.color_text,
            bg=self.color_panel,
            font=self.font_body,
        ).pack(anchor="w", padx=12, pady=(12, 6))

        self._build_sidebar_button(sidebar, "Hoje", self._show_today)
        self._build_sidebar_button(sidebar, "Tarefas", self._show_tasks)
        self._build_sidebar_button(sidebar, "Adicionar tarefa", self._add_task)
        self._build_sidebar_button(sidebar, "Buscar RAG", self._search_rag)
        self._build_sidebar_button(sidebar, "Gerar embeddings", self._build_embeddings)
        self._build_sidebar_button(sidebar, "Prioridades", self._show_priorities)
        self._build_sidebar_button(sidebar, "Quiz", self._run_quiz)
        self._build_sidebar_button(sidebar, "Revisao", self._run_review)

        output_frame = tk.Frame(main, bg=self.color_card)
        output_frame.pack(fill="both", expand=True)

        self.output = tk.Text(
            output_frame,
            wrap="word",
            state="disabled",
            bg=self.color_card,
            fg=self.color_text,
            insertbackground=self.color_text,
            font=self.font_body,
            relief="flat",
        )
        self.output.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)

        scrollbar = tk.Scrollbar(output_frame, command=self.output.yview)
        scrollbar.pack(side="left", fill="y", padx=(4, 8), pady=8)
        self.output.configure(yscrollcommand=scrollbar.set)

        controls = tk.Frame(main, bg=self.color_bg)
        controls.pack(fill="x", pady=(12, 0))

        self.entry = tk.Entry(
            controls,
            font=self.font_body,
            bg="#0b1220",
            fg=self.color_text,
            insertbackground=self.color_text,
            relief="flat",
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=6)
        self.entry.bind("<Return>", self._on_send)

        send_btn = tk.Button(
            controls,
            text="Enviar",
            command=self._on_send,
            bg=self.color_accent,
            fg="#0f172a",
            relief="flat",
            font=self.font_body,
            padx=12,
            pady=6,
        )
        send_btn.pack(side="left")

        self.status = tk.Label(
            self,
            text="Pronto",
            fg=self.color_muted,
            bg=self.color_bg,
            font=self.font_small,
        )
        self.status.pack(fill="x", padx=16, pady=(6, 12), anchor="w")

        self._spinner: tk.Toplevel | None = None

    def _build_sidebar_button(self, parent: tk.Widget, label: str, command) -> None:
        tk.Button(
            parent,
            text=label,
            command=command,
            bg=self.color_panel,
            fg=self.color_text,
            relief="flat",
            activebackground="#1f2937",
            activeforeground=self.color_text,
            font=self.font_body,
            anchor="w",
            padx=12,
            pady=6,
        ).pack(fill="x", padx=8, pady=2)

    def _open_window(self, title: str) -> tk.Toplevel:
        window = tk.Toplevel(self)
        window.title(title)
        window.configure(bg=self.color_bg)
        window.geometry("700x480")
        return window

    def _window_output(self, window: tk.Toplevel, title: str) -> tk.Text:
        header = tk.Label(
            window,
            text=title,
            fg=self.color_text,
            bg=self.color_bg,
            font=self.font_body,
        )
        header.pack(anchor="w", padx=16, pady=(16, 8))

        frame = tk.Frame(window, bg=self.color_card)
        frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        output = tk.Text(
            frame,
            wrap="word",
            state="disabled",
            bg=self.color_card,
            fg=self.color_text,
            insertbackground=self.color_text,
            font=self.font_body,
            relief="flat",
        )
        output.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)

        scrollbar = tk.Scrollbar(frame, command=output.yview)
        scrollbar.pack(side="left", fill="y", padx=(4, 8), pady=8)
        output.configure(yscrollcommand=scrollbar.set)

        return output

    def _set_output(self, output: tk.Text, text: str) -> None:
        output.configure(state="normal")
        output.delete("1.0", "end")
        output.insert("end", text)
        output.configure(state="disabled")

    def _append_output(self, text: str) -> None:
        self.output.configure(state="normal")
        self.output.insert("end", text + "\n")
        self.output.configure(state="disabled")
        self.output.see("end")

    def _show_spinner(self, message: str = "Espere!") -> None:
        if self._spinner is not None:
            return
        spinner = tk.Toplevel(self)
        spinner.title("Processando")
        spinner.configure(bg=self.color_bg)
        spinner.geometry("240x120")
        spinner.transient(self)
        spinner.grab_set()

        tk.Label(
            spinner,
            text=message,
            fg=self.color_text,
            bg=self.color_bg,
            font=self.font_body,
        ).pack(pady=(16, 8))

        bar = ttk.Progressbar(spinner, mode="indeterminate")
        bar.pack(fill="x", padx=20, pady=(0, 16))
        bar.start(10)

        self._spinner = spinner

    def _hide_spinner(self) -> None:
        if self._spinner is None:
            return
        self._spinner.grab_release()
        self._spinner.destroy()
        self._spinner = None

    def _on_send(self, event: tk.Event | None = None) -> None:
        user_text = self.entry.get().strip()
        if not user_text:
            return
        self.entry.delete(0, "end")

        self._append_output(f"> {user_text}")
        self.history.append({"role": "user", "content": user_text})
        try:
            self.status.configure(text="Consultando LLM...")
            self._show_spinner("Espere! Consultando a LLM...")
            decision = _decide_tool(self.history)
            tool_name = decision.get("tool", "none")
            input_args = decision.get("args") or {}
            if tool_name == "none":
                answer = (decision.get("response") or "").strip()
            else:
                tool_fn = TOOL_FUNCTIONS.get(tool_name)
                if tool_fn is None:
                    tool_output = f"Tool desconhecida: {tool_name}"
                else:
                    try:
                        tool_output = tool_fn(**input_args)
                    except Exception as exc:
                        tool_output = f"Erro ao executar {tool_name}: {exc}"
                log_tool_call(tool_name, input_args, tool_output)
                self.history.append({"role": "assistant", "content": "Ferramenta executada."})
                self.history.append(
                    {
                        "role": "user",
                        "content": (
                            "Resultado da ferramenta:\n" + tool_output + "\n\nResponda ao usuario."
                        ),
                    }
                )
                response = send_message(self.history)
                answer = (response.content or "").strip()
        except Exception as exc:
            answer = f"Erro ao chamar LLM: {exc}"
        finally:
            self._hide_spinner()
        self.status.configure(text="Pronto")
        self.history.append({"role": "assistant", "content": answer})
        self._append_output(answer)

    def _show_today(self) -> None:
        window = self._open_window("Agenda de Hoje")
        output = self._window_output(window, "Agenda de hoje")
        self._set_output(output, consultar_agenda("hoje"))

    def _show_tasks(self) -> None:
        window = self._open_window("Tarefas")
        header = tk.Label(
            window,
            text="Tarefas",
            fg=self.color_text,
            bg=self.color_bg,
            font=self.font_body,
        )
        header.pack(anchor="w", padx=16, pady=(16, 8))

        list_frame = tk.Frame(window, bg=self.color_bg)
        list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        listbox = tk.Listbox(
            list_frame,
            bg=self.color_card,
            fg=self.color_text,
            font=self.font_body,
            selectbackground="#1f2937",
            relief="flat",
        )
        listbox.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame, command=listbox.yview)
        scrollbar.pack(side="left", fill="y")
        listbox.configure(yscrollcommand=scrollbar.set)

        actions = tk.Frame(window, bg=self.color_bg)
        actions.pack(fill="x", padx=16, pady=(0, 16))

        tasks = self._load_tasks()

        def refresh_list() -> None:
            listbox.delete(0, "end")
            for task in tasks:
                status = task.get("status", "pendente")
                desc = task.get("descricao") or "sem descricao"
                listbox.insert(
                    "end",
                    f"#{task.get('id','')} | {task.get('titulo','')} | {task.get('materia') or 'sem materia'} "
                    f"| prazo: {task.get('prazo') or 'sem prazo'} | {task.get('status','pendente')} | {desc}",
                )
                color = "#22c55e" if status == "concluida" else "#fbbf24"
                listbox.itemconfig("end", fg=color)

        def get_selected_task() -> Dict[str, Any] | None:
            selection = listbox.curselection()
            if not selection:
                return None
            return tasks[selection[0]]

        def edit_task() -> None:
            task = get_selected_task()
            if not task:
                messagebox.showwarning("Tarefas", "Selecione uma tarefa para editar.")
                return
            self._edit_task_window(task, refresh_list, tasks)

        def conclude_task() -> None:
            task = get_selected_task()
            if not task:
                messagebox.showwarning("Tarefas", "Selecione uma tarefa para concluir.")
                return
            task["status"] = "concluida"
            self._save_tasks(tasks)
            refresh_list()

        tk.Button(
            actions,
            text="Editar",
            command=edit_task,
            bg=self.color_accent,
            fg="#0f172a",
            relief="flat",
            font=self.font_body,
            padx=12,
            pady=6,
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            actions,
            text="Concluir",
            command=conclude_task,
            bg=self.color_panel,
            fg=self.color_text,
            relief="flat",
            font=self.font_body,
            padx=12,
            pady=6,
        ).pack(side="left")

        refresh_list()

    def _search_rag(self) -> None:
        question = simpledialog.askstring("Buscar RAG", "Pergunta:")
        if not question:
            return
        window = self._open_window("Busca RAG")
        output = self._window_output(window, f"Pergunta: {question}")
        self._set_output(output, buscar_material_rag(question))

    def _build_embeddings(self) -> None:
        window = self._open_window("Gerar embeddings")
        output = self._window_output(window, "Geracao de embeddings")
        self._set_output(output, "Gerando indice... Aguarde.")
        self.status.configure(text="Gerando embeddings...")
        self._show_spinner("Espere! Gerando embeddings...")
        try:
            docs_path = ROOT / "data" / "docs"
            index_path = ROOT / "data" / "index.pkl"
            docs = load_documents(str(docs_path))
            chunks = chunk_documents(docs)
            embeddings = generate_embeddings(chunks)
            save_index(embeddings, str(index_path))
            rag_module._INDEX = rag_module.load_index(str(index_path))
            message = f"Index gerado com sucesso. Docs: {len(docs)} | Chunks: {len(chunks)}"
            self._set_output(output, message)
            messagebox.showinfo("Embeddings", message)
        except Exception as exc:
            message = f"Falha ao gerar embeddings: {exc}"
            self._set_output(output, message)
            messagebox.showerror("Embeddings", message)
        finally:
            self.status.configure(text="Pronto")
            self._hide_spinner()

    def _show_priorities(self) -> None:
        window = self._open_window("Prioridades do dia")
        output = self._window_output(window, "Prioridades do dia")
        self._show_spinner("Espere! Gerando prioridades...")
        try:
            self._set_output(output, gerar_prioridades_do_dia())
        finally:
            self._hide_spinner()

    def _run_quiz(self) -> None:
        topic = simpledialog.askstring("Quiz", "Materia:")
        if not topic:
            return
        window = self._open_window("Quiz")
        saved_state = self._load_quiz_state()
        if saved_state and saved_state.get("topic") == topic:
            resume = messagebox.askyesno(
                "Quiz",
                "Encontramos um quiz salvo para esse topico. Deseja retomar?",
            )
            if resume:
                quiz_items = saved_state.get("quiz", [])
                answers = saved_state.get("answers", [])
                index = saved_state.get("index", 0)
                self._run_quiz_ui(window, topic, quiz_items, answers, index)
                return

        self._show_spinner("Espere! Gerando quiz...")
        try:
            context = buscar_material_rag(topic)
            quiz_items = generate_quiz(topic, context)
        finally:
            self._hide_spinner()
        if not quiz_items:
            output = self._window_output(window, f"Quiz: {topic}")
            self._set_output(output, "Nao foi possivel gerar o quiz.")
            return
        self._run_quiz_ui(window, topic, quiz_items, None, 0)

    def _run_review(self) -> None:
        topic = simpledialog.askstring("Revisao", "Materia:")
        if not topic:
            return
        window = self._open_window("Revisao")
        output = self._window_output(window, f"Revisao: {topic}")
        context = buscar_material_rag(topic)
        self._set_output(output, recomendar_revisao(topic, context))

    def _add_task(self) -> None:
        window = self._open_window("Adicionar tarefa")
        frame = tk.Frame(window, bg=self.color_bg)
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        fields = [
            ("Nome da tarefa", "titulo"),
            ("Materia associada", "materia"),
            ("Entrega (YYYY-MM-DD)", "prazo"),
        ]
        entries: Dict[str, tk.Entry] = {}
        for idx, (label, key) in enumerate(fields):
            tk.Label(
                frame,
                text=label,
                fg=self.color_text,
                bg=self.color_bg,
                font=self.font_body,
            ).grid(row=idx, column=0, sticky="w", pady=(0, 8))
            entry = tk.Entry(
                frame,
                font=self.font_body,
                bg="#0b1220",
                fg=self.color_text,
                insertbackground=self.color_text,
                relief="flat",
                width=40,
            )
            entry.grid(row=idx, column=1, sticky="ew", pady=(0, 8), padx=(12, 0))
            entries[key] = entry

        frame.columnconfigure(1, weight=1)

        output = tk.Text(
            frame,
            wrap="word",
            state="disabled",
            bg=self.color_card,
            fg=self.color_text,
            insertbackground=self.color_text,
            font=self.font_body,
            relief="flat",
            height=10,
        )
        output.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(8, 0))
        frame.rowconfigure(4, weight=1)

        def save_task() -> None:
            titulo = entries["titulo"].get().strip()
            materia = entries["materia"].get().strip() or None
            prazo = entries["prazo"].get().strip() or None
            if not titulo:
                messagebox.showwarning("Tarefa", "Informe o nome da tarefa.")
                return
            result = adicionar_tarefa(titulo, prazo, materia)
            output.configure(state="normal")
            output.delete("1.0", "end")
            output.insert("end", result + "\n\n" + self._format_tasks())
            output.configure(state="disabled")

        tk.Button(
            frame,
            text="Salvar tarefa",
            command=save_task,
            bg=self.color_accent,
            fg="#0f172a",
            relief="flat",
            font=self.font_body,
            padx=12,
            pady=6,
        ).grid(row=3, column=0, columnspan=2, sticky="w")

    def _edit_task_window(
        self,
        task: Dict[str, Any],
        on_save,
        tasks: List[Dict[str, Any]],
    ) -> None:
        window = self._open_window("Editar tarefa")
        frame = tk.Frame(window, bg=self.color_bg)
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        fields = [
            ("Nome da tarefa", "titulo"),
            ("Materia associada", "materia"),
            ("Entrega (YYYY-MM-DD)", "prazo"),
            ("Descricao", "descricao"),
        ]
        entries: Dict[str, tk.Entry] = {}
        for idx, (label, key) in enumerate(fields):
            tk.Label(
                frame,
                text=label,
                fg=self.color_text,
                bg=self.color_bg,
                font=self.font_body,
            ).grid(row=idx, column=0, sticky="w", pady=(0, 8))
            entry = tk.Entry(
                frame,
                font=self.font_body,
                bg="#0b1220",
                fg=self.color_text,
                insertbackground=self.color_text,
                relief="flat",
                width=40,
            )
            entry.grid(row=idx, column=1, sticky="ew", pady=(0, 8), padx=(12, 0))
            entry.insert(0, str(task.get(key, "") or ""))
            entries[key] = entry

        frame.columnconfigure(1, weight=1)

        def save_changes() -> None:
            task["titulo"] = entries["titulo"].get().strip()
            task["materia"] = entries["materia"].get().strip() or None
            task["prazo"] = entries["prazo"].get().strip() or None
            task["descricao"] = entries["descricao"].get().strip() or None
            self._save_tasks(tasks)
            on_save()
            window.destroy()

        tk.Button(
            frame,
            text="Salvar alteracoes",
            command=save_changes,
            bg=self.color_accent,
            fg="#0f172a",
            relief="flat",
            font=self.font_body,
            padx=12,
            pady=6,
        ).grid(row=len(fields), column=0, columnspan=2, sticky="w")

    def _format_tasks(self) -> str:
        tasks = self._load_tasks()
        if not tasks:
            return "Nenhuma tarefa encontrada."

        lines = []
        for task in tasks:
            status = task.get("status", "pendente")
            titulo = task.get("titulo", "(sem titulo)")
            materia = task.get("materia") or "sem materia"
            prazo = task.get("prazo") or "sem prazo"
            desc = task.get("descricao") or "sem descricao"
            task_id = task.get("id", "")
            lines.append(
                f"#{task_id} | {titulo} | {materia} | prazo: {prazo} | {status} | {desc}"
            )

        return "\n".join(lines)

    def _run_quiz_ui(
        self,
        window: tk.Toplevel,
        topic: str,
        quiz_items: List[Dict[str, Any]],
        saved_answers: List[int | None] | None,
        saved_index: int,
    ) -> None:
        state = {
            "index": max(0, min(saved_index, len(quiz_items) - 1)) if quiz_items else 0,
            "answers": saved_answers or [None] * len(quiz_items),
            "quiz": quiz_items,
            "topic": topic,
        }

        header = tk.Label(
            window,
            text=f"Quiz: {topic}",
            fg=self.color_text,
            bg=self.color_bg,
            font=self.font_body,
        )
        header.pack(anchor="w", padx=16, pady=(16, 8))

        question_label = tk.Label(
            window,
            text="",
            fg=self.color_text,
            bg=self.color_bg,
            font=self.font_body,
            wraplength=620,
            justify="left",
        )
        question_label.pack(anchor="w", padx=16, pady=(0, 12))

        options_frame = tk.Frame(window, bg=self.color_bg)
        options_frame.pack(fill="x", padx=16)

        nav_frame = tk.Frame(window, bg=self.color_bg)
        nav_frame.pack(fill="x", padx=16, pady=(8, 0))

        meta_frame = tk.Frame(window, bg=self.color_bg)
        meta_frame.pack(fill="x", padx=16, pady=(8, 0))

        progress = ttk.Progressbar(meta_frame, orient="horizontal", mode="determinate")
        progress.pack(side="left", fill="x", expand=True, padx=(0, 12))

        score_label = tk.Label(
            meta_frame,
            text="Acertos: 0/0",
            fg=self.color_text,
            bg=self.color_bg,
            font=self.font_small,
        )
        score_label.pack(side="left")

        def update_meta() -> None:
            answered = sum(1 for ans in state["answers"] if ans is not None)
            total = len(state["quiz"])
            acertos = self._quiz_score(state["quiz"], state["answers"])
            progress["maximum"] = total if total > 0 else 1
            progress["value"] = answered
            score_label.configure(text=f"Acertos: {acertos}/{total}")

        def clear_options() -> None:
            for child in options_frame.winfo_children():
                child.destroy()

        def show_question(index: int) -> None:
            clear_options()
            for child in nav_frame.winfo_children():
                child.destroy()
            item = state["quiz"][index]
            question_label.configure(text=f"{index + 1}. {item.get('pergunta', '')}")
            options = item.get("opcoes", [])
            correct = (item.get("resposta_correta") or 0) - 1

            def on_select(choice_idx: int) -> None:
                state["answers"][index] = choice_idx
                for btn_idx, btn in enumerate(options_frame.winfo_children()):
                    if btn_idx == correct:
                        btn.configure(bg=self.color_success, fg="#0f172a")
                    elif btn_idx == choice_idx:
                        btn.configure(bg=self.color_error, fg=self.color_text)
                    else:
                        btn.configure(bg="#1f2937", fg=self.color_text)
                update_meta()
                self._save_quiz_state(state)
                window.after(800, next_question)

            for i, option in enumerate(options):
                btn = tk.Button(
                    options_frame,
                    text=f"{i + 1}. {option}",
                    command=lambda idx=i: on_select(idx),
                    bg="#1f2937",
                    fg=self.color_text,
                    relief="flat",
                    activebackground="#334155",
                    activeforeground=self.color_text,
                    font=self.font_body,
                    anchor="w",
                    padx=12,
                    pady=6,
                )
                btn.pack(fill="x", pady=4)

            next_btn = tk.Button(
                nav_frame,
                text="Proxima",
                command=next_question,
                bg=self.color_panel,
                fg=self.color_text,
                relief="flat",
                font=self.font_body,
                padx=12,
                pady=6,
            )
            next_btn.pack(side="right")

        def next_question() -> None:
            state["index"] += 1
            self._save_quiz_state(state)
            if state["index"] >= len(state["quiz"]):
                attempt_finish()
            else:
                show_question(state["index"])

        def attempt_finish() -> None:
            unanswered = next(
                (i for i, ans in enumerate(state["answers"]) if ans is None),
                None,
            )
            if unanswered is not None:
                proceed = messagebox.askyesno(
                    "Quiz",
                    "Ha questoes sem resposta. Deseja concluir mesmo assim?",
                )
                if not proceed:
                    state["index"] = unanswered
                    show_question(unanswered)
                    return
            show_summary()

        def show_summary() -> None:
            self._show_quiz_summary(window, topic, state)

        window.protocol("WM_DELETE_WINDOW", lambda: self._on_quiz_close(window, state))
        update_meta()
        show_question(state["index"])

    def _show_quiz_review(
        self,
        window: tk.Toplevel,
        topic: str,
        state: Dict[str, Any],
        index: int,
    ) -> None:
        for child in window.winfo_children():
            child.destroy()

        header = tk.Label(
            window,
            text=f"Revisao: {topic}",
            fg=self.color_text,
            bg=self.color_bg,
            font=self.font_body,
        )
        header.pack(anchor="w", padx=16, pady=(16, 8))

        item = state["quiz"][index]
        question = item.get("pergunta", "")
        options = item.get("opcoes", [])
        correct = (item.get("resposta_correta") or 0) - 1
        chosen = state["answers"][index]

        tk.Label(
            window,
            text=f"{index + 1}. {question}",
            fg=self.color_text,
            bg=self.color_bg,
            font=self.font_body,
            wraplength=620,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 12))

        options_frame = tk.Frame(window, bg=self.color_bg)
        options_frame.pack(fill="x", padx=16)

        for i, option in enumerate(options):
            bg = "#1f2937"
            fg = self.color_text
            if i == correct:
                bg = self.color_success
                fg = "#0f172a"
            elif chosen is not None and i == chosen:
                bg = self.color_error
            tk.Label(
                options_frame,
                text=f"{i + 1}. {option}",
                bg=bg,
                fg=fg,
                font=self.font_body,
                anchor="w",
                padx=12,
                pady=6,
            ).pack(fill="x", pady=4)

        tk.Button(
            window,
            text="Voltar ao resumo",
            command=lambda: self._show_quiz_summary(window, topic, state),
            bg=self.color_accent,
            fg="#0f172a",
            relief="flat",
            font=self.font_body,
            padx=12,
            pady=6,
        ).pack(anchor="w", padx=16, pady=(12, 16))

    def _show_quiz_summary(self, window: tk.Toplevel, topic: str, state: Dict[str, Any]) -> None:
        for child in window.winfo_children():
            child.destroy()

        title = tk.Label(
            window,
            text="Resumo do quiz",
            fg=self.color_text,
            bg=self.color_bg,
            font=self.font_body,
        )
        title.pack(anchor="w", padx=16, pady=(16, 8))

        list_frame = tk.Frame(window, bg=self.color_bg)
        list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        listbox = tk.Listbox(
            list_frame,
            bg=self.color_card,
            fg=self.color_text,
            font=self.font_body,
            selectbackground="#1f2937",
            relief="flat",
        )
        listbox.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame, command=listbox.yview)
        scrollbar.pack(side="left", fill="y")
        listbox.configure(yscrollcommand=scrollbar.set)

        for idx, item in enumerate(state["quiz"]):
            listbox.insert("end", f"{idx + 1}. {item.get('pergunta', '')}")

        feedback = self._generate_quiz_feedback(topic, state["quiz"], state["answers"])
        feedback_label = tk.Label(
            window,
            text=f"Feedback: {feedback}",
            fg=self.color_text,
            bg=self.color_bg,
            font=self.font_body,
            wraplength=620,
            justify="left",
        )
        feedback_label.pack(anchor="w", padx=16, pady=(8, 16))

        def on_select(_: tk.Event) -> None:
            selection = listbox.curselection()
            if not selection:
                return
            review_index = selection[0]
            self._show_quiz_review(window, topic, state, review_index)

        listbox.bind("<<ListboxSelect>>", on_select)

        self._clear_quiz_state()

    def _generate_quiz_feedback(
        self, topic: str, quiz_items: List[Dict[str, Any]], answers: List[int | None]
    ) -> str:
        total = len(quiz_items)
        acertos = self._quiz_score(quiz_items, answers)

        messages = [
            {
                "role": "user",
                "content": (
                    "Gere um feedback curto e motivador para o estudante com base no desempenho. "
                    "Mencione o topico e sugira proximos passos de estudo.\n\n"
                    f"Topico: {topic}\nAcertos: {acertos}\nTotal: {total}"
                ),
            }
        ]
        try:
            self._show_spinner("Espere! Gerando feedback...")
            response = send_message(messages)
            return (response.content or "").strip()
        except Exception as exc:
            return f"Feedback indisponivel: {exc}"
        finally:
            self._hide_spinner()

    def _quiz_score(self, quiz_items: List[Dict[str, Any]], answers: List[int | None]) -> int:
        acertos = 0
        for item, chosen in zip(quiz_items, answers):
            correct = (item.get("resposta_correta") or 0) - 1
            if chosen is not None and chosen == correct:
                acertos += 1
        return acertos

    def _quiz_state_path(self) -> Path:
        return ROOT / "data" / "quiz_state.json"

    def _save_quiz_state(self, state: Dict[str, Any]) -> None:
        path = self._quiz_state_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "topic": state.get("topic"),
            "index": state.get("index"),
            "answers": state.get("answers"),
            "quiz": state.get("quiz"),
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_quiz_state(self) -> Dict[str, Any] | None:
        path = self._quiz_state_path()
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None

    def _clear_quiz_state(self) -> None:
        path = self._quiz_state_path()
        if path.exists():
            path.unlink()

    def _on_quiz_close(self, window: tk.Toplevel, state: Dict[str, Any]) -> None:
        self._save_quiz_state(state)
        window.destroy()

    def _load_tasks(self) -> List[Dict[str, Any]]:
        tasks_path = ROOT / "data" / "tarefas.json"
        if not tasks_path.exists():
            return []
        try:
            return json.loads(tasks_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

    def _save_tasks(self, tasks: List[Dict[str, Any]]) -> None:
        tasks_path = ROOT / "data" / "tarefas.json"
        tasks_path.parent.mkdir(parents=True, exist_ok=True)
        tasks_path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    app = JarvisApp()
    app.mainloop()
